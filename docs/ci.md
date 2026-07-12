# CI Integration

## Quick start: reusable actions

The easiest way to add agentprobe to any GitHub Actions workflow is via the
reusable composite actions in this repo.

### Android

```yaml
- uses: dzianisv/agentprobe/.github/actions/agentprobe-android@main
  with:
    case: path/to/my-test.yaml
    api-level: '33'
    apk-path: path/to/app.apk   # optional
    output-dir: /tmp/cua-output
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

The action handles: `pip install agentprobe`, `ffmpeg`, KVM device, and the emulator runner.

### Browser

```yaml
- uses: dzianisv/agentprobe/.github/actions/agentprobe-browser@main
  with:
    case: path/to/my-test.yaml
    output-dir: /tmp/cua-output
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

The action handles: `pip install agentprobe`, bun, browser runner deps, `xvfb`, `xdotool`, `scrot`, `ffmpeg`, and Xvfb startup.

## Android emulator (manual)

Uses `reactivecircus/android-emulator-runner@v2` on `ubuntu-latest`.

Key setup steps:
1. `pip install agentprobe` + `sudo apt-get install -y ffmpeg`
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
1. `pip install agentprobe`, install bun via `oven-sh/setup-bun@v2`
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

Set `HAI_API_KEY` (see [Required GitHub repository secrets](#required-github-repository-secrets))
and the workflow picks the H Company backend automatically: `chrome-sync-login.ts`
checks `AZURE_CUA_API_KEY` and `OPENAI_API_KEY` first (unchanged for the existing
workflow), then falls back to `HAI_API_KEY`, pointing the OpenAI-compatible client
at `https://api.hcompany.ai/v1/` with model `holo3-1-35b-a3b` (H Company's free
tier) via the Chat Completions API — Holo's API only implements
`POST /chat/completions`, not the Responses API used for Azure/OpenAI, so
`core/vision.ts`'s `visionJudge` branches on `apiStyle: "chat"` for this backend.

## Required GitHub repository secrets

Configure these under **Settings → Secrets and variables → Actions** (or
`gh secret set NAME` from a checkout with `repo` scope). Never print, log, or
commit the secret values themselves — only the names below are needed to wire
up a workflow.

| Secret | Used by | Notes |
| --- | --- | --- |
| `AZURE_CUA_API_KEY` | `cua-chrome-sync-login.yml`, `cua-chrome-webapp.yml`, `agentprobe-android`/`agentprobe-browser` actions | Azure OpenAI-compatible CUA planner/vision key. |
| `AZURE_CUA_BASE_URL` | same as above | Azure endpoint base URL paired with `AZURE_CUA_API_KEY`. |
| `HAI_API_KEY` | `cua-chrome-sync-login-hcompany.yml`, `agentprobe/grounding.py`, `bench/backends.yaml` (`holo` entry) | H Company Holo Models API key. Create one at [portal.hcompany.ai](https://portal.hcompany.ai); the free tier (`holo3-1-35b-a3b`) is rate-limited to 5 req/min. |

`gh secret set` example (run locally — this reads the value from your own
terminal/clipboard and uploads it directly to GitHub; it is never displayed,
logged, or written to a file by this repo's tooling):

```bash
gh secret set HAI_API_KEY --repo dzianisv/agentprobe
```

## pytest integration

The `agentprobe` package registers a `pytest11` entry point so pytest picks up
the `cua_case` fixture automatically:

```bash
pip install agentprobe
pytest tests/
```

No `conftest.py` needed — the fixture is auto-loaded.

## Full workflow templates

See [skills/agentprobe-ci/SKILL.md](../skills/agentprobe-ci/SKILL.md) for full
copy-paste workflow YAML.
