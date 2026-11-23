# Architecture

This document describes the current implementation. Update it when module responsibilities or execution flow change.

## High-level flow

```text
CLI (monitor/cli.py)
  |
  +-- Resolve config path
  |     CLI --config / -c
  |       > SENTINEL_CONFIG
  |       > ./targets.yaml
  |
  +-- Load configuration (monitor/config.py)
  |
  +-- Run checks (monitor/checker.py)
  |     |
  |     +-- HTTP HEAD request via httpx
  |     |
  |     +-- TLS certificate inspection in a worker thread
  |
  +-- Render status table and diagnostics (monitor/cli.py)
```

## Modules

### `monitor/cli.py`

Defines the `sentinel` command, argument parsing, configuration-path precedence, the `init` command, and terminal output. The status table and diagnostic messages are rendered separately.

### `monitor/config.py`

Defines `SiteConfig` and `AppConfig`, reads YAML configuration with PyYAML, and creates the application configuration object. Configuration validation is currently limited; malformed YAML structures may still produce low-level exceptions. See the configuration guide and the open validation work before relying on strict schema guarantees.

### `monitor/checker.py`

Uses a shared `httpx.AsyncClient` to issue HTTP HEAD requests. For each site, the HTTP probe and TLS inspection run concurrently. Results keep reachability, HTTP status health, TLS metadata, and certificate validation as separate signals.

A received HTTP response means the endpoint is reachable. A status below 400 is considered healthy by the current implementation; an HTTP response with status 400 or higher is reachable but reported as an HTTP error. A request error means no HTTP response was received.

### `monitor/ssl_utils.py`

Inspects HTTPS certificates. It first attempts a normally verified TLS handshake. If certificate verification fails, it can perform a separate unverified handshake to retrieve certificate metadata while preserving the validation failure in the result. Retrieving expiry metadata does not mean the certificate is trusted.

## Tests

Tests are organized by module under `tests/`:

- `test_cli.py` — command-line behavior and terminal output.
- `test_config.py` — configuration loading.
- `test_checker.py` — HTTP checking and result classification.
- `test_ssl_utils.py` — TLS certificate inspection and validation.

## Design constraints

- Keep the tool lightweight and suitable for local CLI use.
- Avoid coupling HTTP reachability to TLS certificate validity.
- Do not treat an HTTP error response as proof that a host is unreachable.
- Keep network-dependent tests deterministic by using mocks or local test servers where appropriate.
- Keep output readable in narrow terminals and avoid duplicate diagnostics.
