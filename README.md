# Sentinel — Uptime & SSL Monitor

A fast, minimal CLI tool to monitor website uptime and SSL certificate health concurrently from your terminal.

<div align="center">

![PyPI version](https://img.shields.io/pypi/v/sentinel-monitor)
![License](https://img.shields.io/github/license/tomi3-11/sentinel-monitor)
![PyPI downloads](https://img.shields.io/pypi/dm/sentinel-monitor)
![Last commit](https://img.shields.io/github/last-commit/tomi3-11/sentinel-monitor)
![Issues](https://img.shields.io/github/issues/tomi3-11/sentinel-monitor)
![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![GitHub repo size](https://img.shields.io/github/repo-size/tomi3-11/sentinel-monitor)

</div>

![demo](demo.gif)

---

## The Problem

Managing multiple projects means keeping track of domain health and SSL expiration dates manually — which is tedious and easy to miss. Sentinel gives you an instant, locally executable snapshot of your web services without the overhead of a heavy monitoring stack or an external SaaS dependency.

## Key Features

- **Concurrent checks** — sites are probed concurrently using async I/O.
- **SSL health tracking** — retrieves certificate expiry metadata using TLS connections and X.509 parsing.
- **Responsive terminal UI** — color-coded output that adapts to terminal width.
- **Declarative configuration** — define monitoring targets in a YAML file.
- **Independent health signals** — HTTP reachability, HTTP status, certificate metadata, and TLS validation are reported separately.
- **Per-site error handling** — DNS failures, timeouts, and connection errors are reported without stopping checks for other sites.

---

## Installation

With pip:

```bash
pip install sentinel-monitor
```

Or with uv:

```bash
uv tool install sentinel-monitor
```

## Quick Start

Generate a starter configuration in the current directory:

```bash
sentinel init
```

Run the monitor:

```bash
sentinel
```

Select a configuration file explicitly:

```bash
sentinel --config /path/to/targets.yaml
```

Or set a default with the `SENTINEL_CONFIG` environment variable. The command-line option takes precedence:

```bash
export SENTINEL_CONFIG="$HOME/.config/sentinel/targets.yaml"
sentinel
```

Check the installed version:

```bash
sentinel --version
```

**Current limitation:** `sentinel init` creates `targets.yaml` in the current directory. It does not yet honor `--config` or `SENTINEL_CONFIG` when choosing where to write the starter file.

---

## Configuration

```yaml
settings:
  timeout: 5
  alert_webhook: ""

sites:
  - name: "Google"
    url: "https://google.com"
  - name: "My API"
    url: "https://api.example.com"
```

- `settings.timeout` sets the HTTP client timeout in seconds; the default is 5.
- `sites` contains the endpoints to monitor. Each entry needs a `url`; `name` is optional and defaults to `Unknown Site`.
- `settings.alert_webhook` is reserved configuration only. Webhook notifications are not implemented yet.

See the [Configuration Guide](docs/configuration.md) for file selection, supported fields, and current limitations.

Configuration validation is still being improved; not every malformed YAML structure is currently rejected with a friendly error.

## How It Works

Sentinel loads the YAML configuration, then runs an HTTP probe and TLS certificate inspection for each configured site.

- **HTTP probe:** sends an asynchronous HTTP `HEAD` request using `httpx`.
- **TLS inspection:** opens a TLS connection to retrieve certificate metadata. Inspection runs in a worker thread so it does not block the asyncio event loop.
- **Independent results:** an HTTP response proves reachability, while an HTTP status of 400 or higher is reported as an HTTP error. TLS certificate validity is reported separately from certificate expiry metadata.

For module responsibilities and execution flow, see [Architecture](docs/architecture.md).

---

## Docker

Build the image:

```bash
docker build -t sentinel-monitor .
```

Run with a configuration file from the current host directory:

```bash
docker run --rm -t \
  -v "$PWD/targets.yaml:/config/targets.yaml:ro" \
  sentinel-monitor sentinel --config /config/targets.yaml
```

The image's default command explicitly selects `targets.yaml`. When using a mounted custom path, override the command as shown so the selected path is passed to Sentinel.

---

## Contributing

Contributions, bug reports, and thoughtful feature proposals are welcome. Start with:

- [Contributing Guide](CONTRIBUTING.md) — setup, branch workflow, tests, and pull requests.
- [Development Guide](docs/development.md) — environment, dependencies, tests, and linting.
- [Code of Conduct](CODE_OF_CONDUCT.md) — community expectations.
- [Support](SUPPORT.md) — where to ask questions and report problems.
- [Security Policy](SECURITY.md) — how to report vulnerabilities privately.

Browse [open issues](https://github.com/tomi3-11/sentinel-monitor/issues) for work in progress and contribution opportunities.

## License

MIT. See [LICENSE](LICENSE).
