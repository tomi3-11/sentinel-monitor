from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SiteConfig:
    """Represent a single website target to monitor."""

    name: str
    url: str


@dataclass
class AppConfig:
    """Represents the global application configuration."""

    sites: list[SiteConfig]
    timeout: int = 5
    webhook_url: str | None = None


def load_config(file_path: str = "targets.yaml") -> AppConfig:
    """
    Read the YAML configuration file and returns a strongly-typed AppConfig object.
    Includes error handling for missing files or malformed YAML.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file '{file_path}' not found. Please create it."
        )

    with open(path, "r") as file:
        try:
            # safe_load prevents execution of arbituary code embedded in YAML
            data = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ValueError(
                f"Error parsing YAML file. Please check the formation: {e}"
            )

    # Extract global settings
    settings = data.get("settings", {})
    timeout = settings.get("timeout", 5)
    webhook_url = settings.get("alert_webhook")

    # Extract and type-cast the sites
    sites_data = data.get("sites", [])
    sites = []

    for s in sites_data:
        if "url" in s:
            name = s.get("name", "Unknown Site")
            sites.append(SiteConfig(name=name, url=s["url"]))

    if not sites:
        raise ValueError(
            f"No valid sites found in '{file_path}'."
            "Each site must have a 'url' field. Run 'sentinel init' to see the expected format."
        )

    return AppConfig(sites=sites, timeout=timeout, webhook_url=webhook_url)


if __name__ == "__main__":
    """
    Quick check Only executes when run directly, this is for testing purposes.
    """
    try:
        config = load_config()
        print(f"Successfully loaded {len(config.sites)} sites.")
        for site in config.sites:
            print(f"- {site.name}: {site.url}")
    except Exception as e:
        print(f"Error: {e}")
