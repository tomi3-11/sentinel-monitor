import pytest

from monitor.config import AppConfig, SiteConfig, load_config


def test_load_valid_config(tmp_path):
    """Valid config loads correctly into typed dataclasses."""
    config_file = tmp_path / "targets.yaml"
    config_file.write_text("""
settings:
  timeout: 10
  alert_webhook: ""

sites:
  - name: "Google"
    url: "https://google.com"
  - name: "My API"
    url: "https://api.example.com"
""")

    config = load_config(str(config_file))

    assert isinstance(config, AppConfig)
    assert config.timeout == 10
    assert config.webhook_url == ""
    assert len(config.sites) == 2
    assert isinstance(config.sites[0], SiteConfig)
    assert config.sites[0].name == "Google"
    assert config.sites[0].url == "https://google.com"


def test_load_config_defaults(tmp_path):
    """Config uses default timeout when settings block is missing."""
    config_file = tmp_path / "targets.yaml"
    config_file.write_text("""
sites:
  - name: "Google"
    url: "https://google.com"
""")
    config = load_config(str(config_file))

    assert config.timeout == 5
    assert config.webhook_url is None


def test_missing_file():
    """Missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")


def test_malformed_yaml(tmp_path):
    """Malformed YAML raises ValueError."""
    config_file = tmp_path / "targets.yaml"
    config_file.write_text("{ invalid: yaml: content:")

    with pytest.raises(ValueError):
        load_config(str(config_file))


def test_no_site(tmp_path):
    """Config with no valid sites raises ValueError."""
    config_file = tmp_path / "targets.yaml"
    config_file.write_text("""
settings:
  timeout: 5
sites: []
""")
    with pytest.raises(ValueError):
        load_config(str(config_file))


def test_site_missing_url_is_skipped(tmp_path):
    """Sites without a url field are skipped, raises ValueError if none left."""
    config_file = tmp_path / "targets.yaml"
    config_file.write_text("""
sites:
  - name: "No URL Site"
""")
    with pytest.raises(ValueError):
        load_config(str(config_file))
