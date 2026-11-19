import sys

import pytest

from monitor import cli
from monitor.checker import SiteResult
from monitor.cli import init_config, print_table
from monitor.config import AppConfig, SiteConfig


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_information_flags_exit_without_monitoring(flag, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sentinel", flag])

    def unexpected(*args, **kwargs):
        pytest.fail("Information flags should exit before loading config or running checks")

    monkeypatch.setattr(cli, "load_config", unexpected)
    monkeypatch.setattr(cli, "run_all_checks", unexpected)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    output = capsys.readouterr()
    assert output.err == ""
    if flag == "--version":
        assert output.out == f"sentinel {cli.__version__}\n"
    else:
        assert "usage: sentinel" in output.out
        assert "--config" in output.out
        assert "--version" in output.out


def _run_main_capturing_config_path(monkeypatch, argv):
    """Run main() with the checks stubbed out and return the config path it loaded."""
    loaded = []

    def fake_load_config(path):
        loaded.append(path)
        return AppConfig(sites=[SiteConfig(name="Example", url="https://example.com")])

    async def fake_run_all_checks(sites, timeout):
        return []

    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(cli, "load_config", fake_load_config)
    monkeypatch.setattr(cli, "run_all_checks", fake_run_all_checks)
    monkeypatch.setattr(cli, "print_table", lambda results: None)

    cli.main()

    assert len(loaded) == 1
    return loaded[0]


def test_config_defaults_to_targets_yaml(monkeypatch):
    """Without a flag or SENTINEL_CONFIG, the config is ./targets.yaml."""
    monkeypatch.delenv("SENTINEL_CONFIG", raising=False)

    assert _run_main_capturing_config_path(monkeypatch, ["sentinel"]) == "targets.yaml"


def test_config_uses_sentinel_config_env_var(monkeypatch):
    """SENTINEL_CONFIG is used when -c is not passed."""
    monkeypatch.setenv("SENTINEL_CONFIG", "/etc/sentinel/targets.yaml")

    path = _run_main_capturing_config_path(monkeypatch, ["sentinel"])

    assert path == "/etc/sentinel/targets.yaml"


def test_config_flag_overrides_sentinel_config_env_var(monkeypatch):
    """-c / --config always wins over SENTINEL_CONFIG."""
    monkeypatch.setenv("SENTINEL_CONFIG", "/etc/sentinel/targets.yaml")

    path = _run_main_capturing_config_path(
        monkeypatch, ["sentinel", "-c", "/other/targets.yaml"]
    )

    assert path == "/other/targets.yaml"


def test_empty_sentinel_config_env_var_is_ignored(monkeypatch):
    """An empty SENTINEL_CONFIG falls back to the default path."""
    monkeypatch.setenv("SENTINEL_CONFIG", "")

    assert _run_main_capturing_config_path(monkeypatch, ["sentinel"]) == "targets.yaml"


def test_init_creates_file(tmp_path, monkeypatch):
    """sentinel init creates a targets.yaml with example content."""
    monkeypatch.chdir(tmp_path)

    init_config()

    config_file = tmp_path / "targets.yaml"
    assert config_file.exists()
    content = config_file.read_text()
    assert "sites:" in content
    assert "settings:" in content


def test_init_warns_if_exists(tmp_path, monkeypatch, capsys):
    """Sentinel init does not overwrite an existing targets.yaml."""
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / "targets.yaml"
    config_file.write_text("original content")

    init_config()

    captured = capsys.readouterr()
    assert "already exists" in captured.out
    assert config_file.read_text() == "original content"



def test_print_table_does_not_duplicate_tls_verification_error(capsys):
    """A TLS handshake failure is shown once, using the SSL inspection result."""
    result = SiteResult(
        name="ITS",
        url="https://its.example.com",
        is_up=False,
        status_code=0,
        response_time_ms=25.0,
        ssl_days_left=-5,
        error_msg=(
            "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
            "self-signed certificate in certificate chain (_ssl.c:1032)"
        ),
        ssl_validation_error=(
            "self-signed certificate in certificate chain"
        ),
        is_reachable=False,
    )

    print_table([result])
    output = capsys.readouterr().out

    assert output.count("self-signed certificate in certificate chain") == 1
    assert "Error:" not in output
    assert "[ITS] TLS validation failed" in output



def test_print_table_separates_diagnostics_from_site_rows(capsys):
    """Diagnostics are grouped below the table rather than splitting site rows."""
    results = [
        SiteResult(
            name="Example",
            url="https://example.com",
            is_up=True,
            status_code=200,
            response_time_ms=20.0,
            ssl_days_left=30,
            is_reachable=True,
        ),
        SiteResult(
            name="ITS",
            url="https://its.example.com",
            is_up=False,
            status_code=0,
            response_time_ms=25.0,
            ssl_days_left=-5,
            error_msg="connection failed",
            ssl_validation_error="self-signed certificate",
            is_reachable=False,
        ),
    ]

    print_table(results)
    output = capsys.readouterr().out

    table_end = output.index("\nDiagnostics")
    diagnostics_start = output.index("[ITS] TLS validation failed")

    assert output.index("Example") < table_end
    assert output.index("ITS") < table_end
    assert table_end < diagnostics_start
    assert "connection failed" not in output  # TLS validation is the useful diagnosis.
    assert "self-signed certificate" in output


def test_print_table_omits_empty_diagnostics_section(capsys):
    """A clean run should show only the site table."""
    result = SiteResult(
        name="Example",
        url="https://example.com",
        is_up=True,
        status_code=200,
        response_time_ms=20.0,
        ssl_days_left=30,
        is_reachable=True,
    )

    print_table([result])
    output = capsys.readouterr().out

    assert "Diagnostics" not in output
