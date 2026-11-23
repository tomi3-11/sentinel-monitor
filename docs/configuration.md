# Configuration

Sentinel reads a YAML configuration file. The default path is `targets.yaml` in the current working directory.

## Selecting a configuration file

The current precedence is:

1. `-c` or `--config` command-line option.
2. `SENTINEL_CONFIG` environment variable.
3. `targets.yaml` in the current working directory.

Example using the command-line option:

```bash
sentinel --config /path/to/targets.yaml
```

Example using the environment variable:

```bash
export SENTINEL_CONFIG="$HOME/.config/sentinel/targets.yaml"
sentinel
```

The command-line option overrides the environment variable.

## YAML example

```yaml
settings:
  timeout: 5
  alert_webhook: ""

sites:
  - name: "Example"
    url: "https://example.com"
  - name: "Example API"
    url: "https://api.example.com"
```

## Settings

| Key | Current behavior |
|---|---|
| `settings.timeout` | HTTP client timeout in seconds; defaults to `5` |
| `settings.alert_webhook` | Reserved configuration value; webhook notifications are not currently implemented |

Each site currently uses:

| Key | Description |
|---|---|
| `name` | Display name for the target; defaults to `Unknown Site` if omitted |
| `url` | URL used for the HTTP and TLS checks |

## Validation limitations

Configuration validation is being improved. Do not assume every malformed YAML shape or invalid field type is rejected with a friendly validation message yet. See the project's open configuration-validation issue before depending on strict validation.

## Initialization command

`sentinel init` creates a starter `targets.yaml` in the current working directory if one does not already exist. The current implementation does not yet honor a custom `--config` path or `SENTINEL_CONFIG` when initializing.
