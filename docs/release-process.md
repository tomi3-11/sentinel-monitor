# Release Process

This document describes the current automated release workflow for maintainers.

## Before a release

1. Ensure the intended changes are merged into `main`.
2. Update the version in `pyproject.toml`.
3. Update `uv.lock` so its project version matches.
4. Add a release entry to `CHANGELOG.md`.
5. Open and merge a focused release-preparation pull request.
6. Confirm CI passes on the resulting `main` commit.

Use the project's existing versioning convention and ensure the Git tag exactly matches the package version, prefixed with `v`.

## Triggering a release

Create and push a version tag that matches `pyproject.toml`:

```bash
git switch main
git pull --ff-only
git tag vX.Y.Z
git push origin vX.Y.Z
```

Replace `X.Y.Z` with the version in `pyproject.toml`. Do not tag a version that has not been prepared and merged.

## Automation

The tag workflow in `.github/workflows/automatic-release.yaml`:

1. Runs Ruff.
2. Runs tests on Python 3.11, 3.12, and 3.13.
3. Verifies the tag version matches the package version.
4. Builds the distribution with `uv build`.
5. Creates a GitHub Release.
6. Dispatches the PyPI publishing workflow.

The publishing workflow in `.github/workflows/publish.yaml` builds the package and publishes it using PyPI Trusted Publishing.

## Verification

After pushing a tag, check the Actions tab for both the automatic release workflow and the PyPI publishing workflow. Confirm that the GitHub Release exists and that the expected version is available on PyPI before announcing the release.

If publishing needs recovery, the PyPI workflow supports manual dispatch. Select the intended release tag as the ref and verify the resulting run carefully.

## Important

- Never commit PyPI tokens or other publishing credentials to the repository.
- Do not move or reuse an already-published version tag.
- If a release workflow fails, investigate and correct the cause before retrying.
- Keep the changelog consistent with the actual contents of the release.
