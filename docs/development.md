# Development Guide

## Requirements

- Python 3.11 or newer.
- [uv](https://docs.astral.sh/uv/) for local environment and dependency management.
- Git.

## Set up the project

Fork the repository, clone your fork, and enter the project directory:

```bash
git clone https://github.com/<your-username>/sentinel-monitor.git
cd sentinel-monitor
uv sync --locked --all-groups
```

This creates or updates the project virtual environment from `uv.lock`, installs the package in the project environment, and includes the development dependency group.

Run project commands through uv:

```bash
uv run sentinel --help
uv run pytest -v
uv run ruff check .
```

## Tests

The test suite is in `tests/`. Run all tests:

```bash
uv run pytest -v
```

Run a single test module:

```bash
uv run pytest -v tests/test_config.py
```

Run a focused test by name:

```bash
uv run pytest -v -k <test-name>
```

Add tests when fixing a bug or changing behavior. Prefer deterministic tests that do not depend on external websites or live network availability.

## Linting

Run Ruff:

```bash
uv run ruff check .
```

Fix automatically fixable findings only when the resulting changes are understood:

```bash
uv run ruff check . --fix
```

## Dependency management

Declare runtime dependencies in `[project].dependencies` and development-only dependencies in `[dependency-groups].dev` in `pyproject.toml`. Update the lock file after changing dependency declarations:

```bash
uv lock
uv sync --locked --all-groups
```

Commit `pyproject.toml` and `uv.lock` together when dependencies change. The repository also currently contains a pinned `requirements.txt`, which is used by GitHub Actions CI and release validation. If changing dependencies, check that file too so CI and local development remain consistent.

## Continuous integration

Pull requests targeting `main` run Ruff and the test suite on Python 3.11, 3.12, and 3.13. The workflow currently installs pinned dependencies from `requirements.txt`. Run the equivalent Ruff and pytest commands locally before requesting review.

## Pull requests

Follow [CONTRIBUTING.md](../CONTRIBUTING.md). Keep changes focused, include tests, and describe exactly what you verified.
