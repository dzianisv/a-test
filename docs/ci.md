# CI Integration

## Quick start: reusable actions

The easiest way to add a-test to any GitHub Actions workflow is via the
reusable composite actions in this repo.

### Unified action (recommended)

`a-test-android`, `a-test-browser`, and `a-test-desktop` (documented below)
are still valid and fully supported — but the default recommended
integration path is now the single unified `a-test` action, which
auto-detects which of the three to run from the `script` path:

```yaml
- uses: dzianisv/a-test/.github/actions/a-test@main
  with:
    script: examples/open-weather.yaml
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

Auto-detection rules (skipped entirely if you set `environment` explicitly):

1. `script` ends in `.ts` → `desktop`.
2. Else `script`'s path/filename contains `android` (case-insensitive) → `android`.
3. Else → `browser` (default fallback).

Set the `environment` input to `android`, `browser`, or `desktop` to override
auto-detection outright. Other inputs mirror the per-surface actions:
`output-dir`, `model`, plus the surface-specific `url` (browser),
`api-level`/`apk-path` (android), and `hai-base-url` (desktop) — all are
no-ops when a different environment is selected. As with every action in
this repo, there is no input for any API key; secrets are always supplied
via the calling job's `env:` block.

Reach for the per-surface actions directly (below) when you need
per-surface-only tuning or want to hard-pin a workflow to a single surface.

### Android

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-android@main
  with:
    case: path/to/my-test.yaml
    api-level: '33'
    apk-path: path/to/app.apk   # optional
    output-dir: /tmp/cua-output
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

The action handles: `pip install a-test`, `ffmpeg`, KVM device, and the emulator runner.

### Browser

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-browser@main
  with:
    case: path/to/my-test.yaml
    output-dir: /tmp/cua-output
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

The action handles: `pip install a-test`, bun, browser runner deps, `xvfb`, `xdotool`, `scrot`, `ffmpeg`, and Xvfb startup.

### Desktop (Terminal + Browser)

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-desktop@main
  with:
    case: examples/dual-surface/chrome-sync-login.ts
    output-dir: /tmp/cua-output
  env:
    # Azure (or swap for OPENAI_API_KEY/OPENAI_BASE_URL, or HAI_API_KEY/HAI_BASE_URL)
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-desktop@main
  with:
    case: examples/dual-surface/terminal-and-browser.ts
    output-dir: /tmp/cua-output
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-desktop@main
  with:
    case: examples/dual-surface/chrome-sync-login.ts
    output-dir: /tmp/cua-output
    model: holo3-1-35b-a3b
  env:
    HAI_API_KEY: ${{ secrets.HAI_API_KEY }}
    # HAI_BASE_URL optional — defaults to https://api.hcompany.ai/v1/
```

The action handles: `pip install a-test`, bun, a sparse checkout of `core`,
`surfaces`, and `examples/dual-surface`, `xvfb`, `xdotool`, `scrot`, `ffmpeg`,
`xterm`, `bsdutils` (for the `script` command used by `chrome-sync-login.ts`),
and Xvfb startup. The vision-judge backend is auto-detected at runtime by the
script itself, in priority order: `AZURE_CUA_API_KEY` (+ `AZURE_CUA_BASE_URL`),
then `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`), then `HAI_API_KEY` (+ optional
`HAI_BASE_URL`) — the action has no `input` for any API key, only the `case`,
`output-dir`, `model`, and `hai-base-url` inputs shown above.

## Android emulator (manual)

Uses `reactivecircus/android-emulator-runner@v2` on `ubuntu-latest`.

Key setup steps:
1. `pip install a-test` + `sudo apt-get install -y ffmpeg`
2. Enable KVM (required for hardware acceleration):
   ```yaml
   - name: Enable KVM
     run: |
       echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
       sudo udevadm control --reload-rules
       sudo udevadm trigger --name-match=kvm
   ```
3. Pass each command as a separate line in `script:` — backslash line continuations
   **do not work** because each line is run via `/usr/bin/sh -c` independently.

Required secrets: `AZURE_CUA_API_KEY`, `AZURE_CUA_BASE_URL`.

## Browser (manual)

Runs on `ubuntu-latest` with `Xvfb` for a virtual display.

Key setup steps:
1. `pip install a-test`, install bun via `oven-sh/setup-bun@v2`
2. `cd browser && bun install`
3. `sudo apt-get install -y xvfb xdotool scrot ffmpeg`
4. Start Xvfb and export `DISPLAY=:99`

## Uploading artifacts

Always upload output with `if: always()` so screenshots and the result.json are
available after both pass and fail:

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: cua-output-${{ github.run_number }}
    path: /tmp/cua-output/
    retention-days: 14
    if-no-files-found: warn

- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: cua-output-demo-${{ github.run_number }}
    path: |
      /tmp/cua-output/demo.gif
      /tmp/cua-output/*.mp4
    retention-days: 30
    if-no-files-found: warn
```

## Chrome-Sync Login on H Company Holo

[`cua-chrome-sync-login-hcompany.yml`](../.github/workflows/cua-chrome-sync-login-hcompany.yml)
runs the same test as `cua-chrome-sync-login.yml`
(`examples/dual-surface/chrome-sync-login.ts`), but backs the final vision-judge
call with [H Company](https://hub.hcompany.ai)'s Holo Models API instead of
Azure/OpenAI. It triggers on `workflow_dispatch` and a daily `schedule` — not on
every push/PR — since it depends on the `HAI_API_KEY` secret and exercises H
Company's hosted API.

The workflow itself is now a thin wrapper: a "Verify HAI_API_KEY secret is
configured" step (fails fast with `::error::` if the secret is unset) followed
by a single `uses: ./.github/actions/a-test-desktop` step — the same
reusable action documented in [Desktop (Terminal + Browser)](#desktop-terminal--browser)
above, also used by `cua-chrome-sync-login.yml` and `cua-dual-surface.yml`. No
install/Xvfb/run steps are duplicated inline anymore.

Set `HAI_API_KEY` (see [Required GitHub repository secrets](#required-github-repository-secrets))
and the workflow picks the H Company backend automatically: `chrome-sync-login.ts`
checks `AZURE_CUA_API_KEY` and `OPENAI_API_KEY` first (unchanged for the existing
workflow), then falls back to `HAI_API_KEY`, pointing the OpenAI-compatible client
at `https://api.hcompany.ai/v1/` (override with `HAI_BASE_URL`) with model
`holo3-1-35b-a3b` (H Company's free tier) via the Chat Completions API — Holo's
API only implements `POST /chat/completions`, not the Responses API used for
Azure/OpenAI, so `core/vision.ts`'s `visionJudge` branches on `apiStyle: "chat"`
for this backend.

## Required GitHub repository secrets

Configure these under **Settings → Secrets and variables → Actions** (or
`gh secret set NAME` from a checkout with `repo` scope). Never print, log, or
commit the secret values themselves — only the names below are needed to wire
up a workflow.

| Secret | Used by | Notes |
| --- | --- | --- |
| `AZURE_CUA_API_KEY` | `cua-chrome-sync-login.yml`, `cua-dual-surface.yml`, `cua-chrome-webapp.yml`, `a-test-android`/`a-test-browser`/`a-test-desktop` actions, unified `a-test` action | Azure OpenAI-compatible CUA planner/vision key. |
| `AZURE_CUA_BASE_URL` | same as above | Azure endpoint base URL paired with `AZURE_CUA_API_KEY`. |
| `HAI_API_KEY` | `cua-chrome-sync-login-hcompany.yml`, `a-test-desktop` action, unified `a-test` action, `a_test/grounding.py`, `bench/backends.yaml` (`holo` entry) | H Company Holo Models API key. Create one at [portal.hcompany.ai](https://portal.hcompany.ai); the free tier (`holo3-1-35b-a3b`) is rate-limited to 5 req/min. |
| `HAI_BASE_URL` | `a-test-desktop` action (optional `hai-base-url` input), unified `a-test` action (same input) | Optional override for the H Company Holo Models API base URL; defaults to `https://api.hcompany.ai/v1/` if unset. |

`gh secret set` example (run locally — this reads the value from your own
terminal/clipboard and uploads it directly to GitHub; it is never displayed,
logged, or written to a file by this repo's tooling):

```bash
gh secret set HAI_API_KEY --repo dzianisv/a-test
```

## pytest integration

The `a-test` package registers a `pytest11` entry point so pytest picks up
the `cua_case` fixture automatically:

```bash
pip install a-test
pytest tests/
```

No `conftest.py` needed — the fixture is auto-loaded.

## Publishing to PyPI

The [Publish to PyPI workflow](../.github/workflows/publish-pypi.yml) builds,
checks, smoke-tests, and publishes a release when a `vX.Y.Z` tag is pushed.
Before the first release, configure a PyPI Trusted Publisher with:

| PyPI setting | Value |
| --- | --- |
| Owner | `dzianisv` |
| Repository | `a-test` |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` |

The workflow uses GitHub OIDC and does not require a `PYPI_TOKEN` repository
secret.

## Full workflow templates

See [skills/a-test-ci/SKILL.md](../skills/a-test-ci/SKILL.md) for full
copy-paste workflow YAML.
