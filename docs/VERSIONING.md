# Versioning & Pinning Policy

## Current state

No git tags or GitHub releases exist yet for this repo (`git tag -l` is empty).
A real, tag-triggered publish pipeline already exists
(`.github/workflows/publish-pypi.yml`, PyPI Trusted Publishing to the
`a-test` project under the `pypi` environment), but it has never fired because
no `vX.Y.Z` tag has been pushed. Until the first tag is cut and published:

- `pip install a-test` does **not** resolve to anything real.
- The npm name `a-test-cua` (see `package.json`) is reserved but unpublished.
- Every `uses: dzianisv/a-test/.github/actions/...` reference in this repo's
  own docs is a **placeholder**, not a working example, until pinned.

## Policy: pin to a commit SHA, never a branch

Until the first tagged release ships, every consumer of this project —
`pip install git+https://...`, `bun add github:...`, and any
`uses: dzianisv/a-test/.github/actions/...` GitHub Action reference — **must**
pin to a specific commit SHA. Do not pin to `@main` or any other branch name.

Why: a branch ref is mutable and can change under a consumer at any time
(silent behavior changes, supply-chain risk). This project's own testing
conventions already require commit-SHA-pinned dependencies elsewhere (e.g.
`agentprobe-cua`/`a-test-cua` as a devDependency in downstream consumers) —
this policy keeps that same bar for consuming this repo itself.

How to find a commit to pin to:

```bash
git ls-remote https://github.com/dzianisv/a-test.git main
```

or copy a commit SHA from the GitHub UI's commit history. Prefer a commit that
has a green CI run (Lint, Android CUA, Browser CUA, External Consumer) before
pinning to it.

## Future state

Once a `vX.Y.Z` tag is pushed (an owner/release decision — see
`RELEASE_CHECKLIST.md`), `publish-pypi.yml` will publish that build to PyPI
automatically, and:

- `README.md`/`docs/quickstart.md` install instructions will switch to the
  real `pip install a-test`.
- Action usage examples will switch from a commit-SHA placeholder to the
  released tag (e.g. `@v0.1.0`), with SHA-pinning still documented as the
  stricter alternative for supply-chain-sensitive consumers.
- This doc will gain a real "latest release" pointer instead of the
  `git ls-remote` workaround above.

See `CHANGELOG.md` for the (currently empty, `[Unreleased]`-only) release log.
