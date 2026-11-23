# Contributing to Sentinel Monitor

Thank you for considering a contribution. Sentinel Monitor is a small Python CLI for checking HTTP availability and TLS certificate health. Contributions should keep it reliable, understandable, and lightweight.

## Before you start

- Read this guide and the [Code of Conduct](CODE_OF_CONDUCT.md).
- Search [existing issues](https://github.com/tomi3-11/sentinel-monitor/issues) and pull requests before starting work.
- For a substantial change, open an issue or discuss the design before writing code.
- If you want to work on an existing issue, leave a comment so maintainers and other contributors know it is being handled. An issue is not assigned to you until a maintainer confirms it.

Good first issues are intended for newcomers, but ask questions when requirements are unclear.

## Development environment

Sentinel supports Python 3.11 and newer. The project uses `uv` for local dependency and environment management.

1. Fork the repository on GitHub.
2. Clone your fork and enter the project directory:

   ```bash
   git clone https://github.com/<your-username>/sentinel-monitor.git
   cd sentinel-monitor
   ```

3. Add the upstream repository:

   ```bash
   git remote add upstream https://github.com/tomi3-11/sentinel-monitor.git
   ```

4. Install the project and development dependencies:

   ```bash
   uv sync --locked --all-groups
   ```

5. Confirm the environment works:

   ```bash
   uv run ruff check .
   uv run pytest -v
   ```

See [Development Guide](docs/development.md) for more detail. The current GitHub Actions test workflow installs the pinned dependencies from `requirements.txt`; local development uses the committed `uv.lock`.

## Branches

Create a focused branch from an up-to-date `main`:

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git switch -c <type>/<short-description>
```

Suggested prefixes:

- `fix/` — bug fixes
- `feat/` — user-facing features
- `test/` — tests
- `docs/` — documentation
- `refactor/` — internal restructuring
- `chore/` — maintenance

Keep each pull request focused. Avoid combining unrelated fixes and features.

## Making changes

- Follow the existing code style and keep the implementation simple.
- Add or update tests for behavior changes and bug fixes.
- Do not weaken or delete tests merely to make a change pass.
- Keep HTTP reachability, HTTP status health, certificate metadata, and TLS validation as distinct concepts.
- Preserve existing CLI behavior unless the issue explicitly calls for a change.
- Update relevant documentation and the changelog when user-visible behavior changes.
- Never commit credentials, tokens, private keys, real webhook URLs, or personal configuration files. Use dummy values in examples.
- Avoid adding dependencies unless they are necessary; explain the trade-off in the pull request.

## Tests and linting

Run both checks before opening a pull request:

```bash
uv run ruff check .
uv run pytest -v
```

If you change packaging, installation, CLI entry points, configuration, Docker behavior, or release automation, add tests or verification appropriate to that surface. State exactly what you ran in the pull request. Do not claim a check passed if you did not run it.

## Commits

Use short, descriptive commit messages. Suggested prefixes are `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, and `chore:`.

Examples:

- `fix: handle malformed site entries`
- `test: cover CLI version output`
- `docs: explain config file precedence`

## Pull requests

1. Push your branch to your fork.
2. Open a pull request against `tomi3-11/sentinel-monitor:main`.
3. Complete the pull request template.
4. Link the related issue using GitHub's closing keywords only when the PR fully resolves it (for example, `Closes #30`).
5. Explain the problem, the approach, important trade-offs, and any limitations.
6. Include test and lint results. Include documentation updates for user-facing changes.
7. Keep the PR focused and respond constructively to review feedback.

A maintainer may ask for changes, request clarification, or close a PR that is out of scope. Please do not force-push over review feedback without communicating when the change would make existing review comments difficult to follow.

## Review and merge

Submitting a PR does not guarantee that it will be merged. Changes are reviewed for correctness, maintainability, scope, tests, and compatibility. Maintainers make the final merge decision.

Please be patient: this is a community project, and review time can vary. You can ask for an update politely if a PR has been waiting for a reasonable period.

## Questions

For usage and development questions, see [SUPPORT.md](SUPPORT.md). For security vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
