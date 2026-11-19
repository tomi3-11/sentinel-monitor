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

---

## Key Features

- **Concurrent checks** — all sites are probed simultaneously using async I/O, not one by one
- **SSL health tracking** — extracts certificate expiry directly via raw TCP sockets, no third-party APIs
- **Responsive terminal UI** — color-coded output that adapts to your terminal width
- **Declarative config** — define all your targets in a single YAML file
- **Independent health signals** — network reachability, HTTP status, and TLS certificate validity are reported separately
- **Graceful error handling** — DNS failures, timeouts, and connection drops are caught and reported per site without crashing

---

## Installation

```bash
pip install sentinel-monitor
```

Or with uv:

```bash
uv tool install sentinel-monitor
```

---

## Quick Start

Generate a starter config in your current directory:

```bash
sentinel init
```

Run the monitor:

```bash
sentinel
```

Point to a specific config file:

```bash
sentinel -c /path/to/targets.yaml
```

Or set a default once with the `SENTINEL_CONFIG` environment variable. The `-c` flag still takes priority, and `targets.yaml` in the current directory is used when neither is set:

```bash
export SENTINEL_CONFIG=~/.config/sentinel/targets.yaml
sentinel
```

Check version:

```bash
sentinel --version
```

---

## Configuration

```yaml
settings:
  timeout: 5
  alert_webhook: ""  # optional: Discord/Slack webhook URL

sites:
  - name: "Google"
    url: "https://google.com"
  - name: "My API"
    url: "https://api.example.com"
```

---

## How It Works

Sentinel is built around three components:

**Configuration Manager** — parses `targets.yaml` into typed dataclasses, validates structure, and raises actionable errors on bad input.

**Concurrency Engine** — an `asyncio` event loop dispatches all HTTP checks simultaneously via `httpx`. Sites are never checked sequentially.

**Network Probes** — two probe types run per site:
- *Uptime probe:* async HTTP `HEAD` request — minimal bandwidth, no body fetched
- *SSL probe:* raw TCP socket wrapped with `ssl.SSLContext` to extract and parse X.509 certificate metadata, runs in a background thread via `asyncio.to_thread` to avoid blocking the event loop

---

## Development Setup

```bash
git clone https://github.com/tomi3-11/sentinel-monitor.git
cd sentinel-monitor
uv venv && source .venv/bin/activate
uv sync
sentinel -c targets.yaml
```

---

## Docker

```bash
docker build -t monitor .
docker run -t monitor sentinel -c targets.yaml
```

---

## License

MIT

