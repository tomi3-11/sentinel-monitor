import argparse
import asyncio
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from blessed import Terminal

from monitor.checker import run_all_checks
from monitor.config import load_config

term = Terminal()

try:
    __version__ = version("sentinel-monitor")
except PackageNotFoundError:
    __version__ = "dev"


def init_config():
    path = Path("targets.yaml")
    if path.exists():
        print(term.yellow("targets.yaml already exists in this directory."))
        return
    template = """\\
settings:
  timeout: 5
  alert_webhook: "" # to be implemented for real time alerts on discord/slack

sites:
  - name: "Example Site"
    url: "https://example.com"
  - name: "Google"
    url: "https://google.com"
"""
    path.write_text(template)
    print(term.bold_green("Created targets.yaml - edit it with your sites and run: sentinel -c targets.yaml"))


def print_table(results):
    tw = term.width or 120
    show_url = tw >= 100

    # fixed columns
    fixed = {
        "status": 12,
        "code": 10,
        "rtime": 14,
        "ssl": 24,
    }
    if show_url:
        name_w = 20
        fixed_total = sum(fixed.values()) + 3 * 5 + name_w

        # url gets whatever is left, minimum 10
        url_w = max(tw - fixed_total - 3, 10) # -3 for its own separator

        col = {
            "status": fixed["status"],
            "name": name_w,
            "url": url_w,
            "code": fixed["code"],
            "rtime": fixed["rtime"],
            "ssl": fixed["ssl"],
        }
    else:
        name_w = max(tw - sum(fixed.values()) - 3 * 4 - 1, 10)
        col = {
            "status": fixed["status"],
            "name": name_w,
            "code": fixed["code"],
            "rtime": fixed["rtime"],
            "ssl": fixed["ssl"],
        }

    def cell(s, w):
        visible = term.length(s)
        return s + " " * max(w - visible, 0)

    def trunc(s, w):
        return s[:w-1] + "…" if len(s) > w else s

    sep = term.dim(" | ")
    total_w = sum(col.values()) + 3 * (len(col) - 1)
    divider = term.dim("-" * total_w)

    if show_url:
        header = (
            cell(term.bold_magenta("Status"),       col["status"]) + sep +
            cell(term.bold_magenta("Site Name"),    col["name"]) + sep +
            cell(term.bold_magenta("URL"),          col["url"]) + sep +
            cell(term.bold_magenta("HTTP"),         col["code"]) + sep +
            cell(term.bold_magenta("Resp(ms)"),     col["rtime"]) + sep +
            cell(term.bold_magenta("SSL Expires"),  col["ssl"])
        )
    else:
        header = (
            cell(term.bold_magenta("Status"),       col["status"]) + sep +
            cell(term.bold_magenta("Site Name"),    col["name"]) + sep +
            cell(term.bold_magenta("HTTP"),         col["code"]) + sep +
            cell(term.bold_magenta("Resp(ms)"),     col["rtime"]) + sep +
            cell(term.bold_magenta("SSL Expires"),  col["ssl"])
        )

    print()
    print(term.bold("Sentinel Uptime & SSL Monitor"))
    print(divider)
    print(header)
    print(divider)

    diagnostics = []

    for res in results:
        if not res.is_reachable:
            status_str = term.bold_red("DOWN")
            code_str = term.red(str(res.status_code) if res.status_code else "-")
        elif res.is_up:
            status_str = term.bold_green("UP")
            code_str = term.green(str(res.status_code))
        else:
            status_str = term.bold_yellow("HTTP ERROR")
            code_str = term.yellow(str(res.status_code))

        ssl_raw = res.ssl_days_left

        if isinstance(ssl_raw, int):
            if res.ssl_validation_error:
                ssl_str = term.bold_red(f"{ssl_raw} days (INVALID)")
            elif ssl_raw < 7:
                ssl_str = term.bold_red(f"{ssl_raw} days (CRITICAL)")
            elif ssl_raw < 30:
                ssl_str = term.yellow(f"{ssl_raw} days (WARN)")
            else:
                ssl_str = term.green(f"{ssl_raw} days")
        else:
            ssl_str = str(ssl_raw)

        if show_url:
            row = (
                cell(status_str,                        col["status"]) + sep +
                cell(term.cyan(res.name),               col["name"]) + sep +
                cell(term.dim(trunc(res.url, url_w)),   col["url"]) + sep +
                cell(code_str,                          col["code"]) + sep +
                cell(f"{res.response_time_ms:.2f}ms",       col["rtime"]) + sep +
                cell(ssl_str,                           col["ssl"])
            )
        else:
            row = (
                cell(status_str,                        col["status"]) + sep +
                cell(term.cyan(trunc(res.name, name_w)),               col["name"]) + sep +
                cell(code_str,                          col["code"]) + sep +
                cell(f"{res.response_time_ms:.2f}ms",       col["rtime"]) + sep +
                cell(ssl_str,                           col["ssl"])
            )

        print(row)

        # Keep diagnostics out of the status table so every site remains one row.
        if res.error_msg and not res.ssl_validation_error:
            diagnostics.append((res.name, "Request failed", res.error_msg))
        if res.ssl_validation_error:
            diagnostics.append(
                (res.name, "TLS validation failed", res.ssl_validation_error)
            )
        if (
            res.ssl_metadata_error
            and res.ssl_metadata_error != "Not HTTPS"
            and res.ssl_days_left == "Unavailable"
        ):
            diagnostics.append(
                (res.name, "SSL metadata unavailable", res.ssl_metadata_error)
            )

    print(divider)

    if diagnostics:
        print()
        print(term.bold("Diagnostics"))
        print(term.dim("-" * min(total_w, 80)))
        for site_name, category, message in diagnostics:
            print(term.bold_cyan(f"[{site_name}] {category}"))
            print(f"    {term.red(message)}")

    print()


def main():
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Sentinel: A fast concurrent uptime and SSL monitor."
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"sentinel {__version__}",
    )

    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help=(
            "Path to the configuration file. Overrides the SENTINEL_CONFIG "
            "environment variable. Defaults to targets.yaml."
        ),
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="Optional command: init",
    )

    args = parser.parse_args()

    # Precedence: --config flag, then SENTINEL_CONFIG, then ./targets.yaml.
    config_path = args.config or os.getenv("SENTINEL_CONFIG") or "targets.yaml"

    if args.command == "init":
        init_config()
        return

    try:
        # Load the configurations
        app_config = load_config(config_path)

        print(f"[*] Loaded {len(app_config.sites)} sites from {config_path}...")

        # Run the asynchronous checks
        print(term.bold_green("Probing network targets concurrently..."))

        results = asyncio.run(
            run_all_checks(app_config.sites, app_config.timeout)
        )

        # Draw the table
        print_table(results)

    except FileNotFoundError as e:
        print(term.bold_red(f"Error: {e}"))
        sys.exit(1)

    # Keep the CLI boundary user-friendly for unexpected runtime failures.
    except Exception as e:  # noqa: BLE001
        print(term.bold_red(f"Fatal Error: {e}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
