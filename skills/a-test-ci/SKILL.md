---
name: a-test-ci
description: Wire a-test into GitHub Actions CI. Use when asked to add CUA tests to a CI pipeline for an Android app or browser extension.
---

# a-test in GitHub Actions CI

## Android: reusable action or raw emulator-runner

Preferred — use the repo's reusable composite action:

```yaml
# .github/workflows/android-cua.yml
name: Android CUA
on: [push, pull_request]

jobs:
  cua:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dzianisv/a-test/.github/actions/a-test-android@main
        with:
          case: examples/android/calculator_math.py
          output-dir: /tmp/cua-output
        env:
          AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
          AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: cua-output
          path: /tmp/cua-output/
```

The action wraps `reactivecircus/android-emulator-runner@v2` plus KVM/ffmpeg setup — see
[.github/actions/a-test-android/action.yml](../../.github/actions/a-test-android/action.yml) and the
in-repo equivalent, [.github/workflows/android-cua.yml](../../.github/workflows/android-cua.yml), which
installs the package from source (`pip install -e .`) instead of PyPI.

## Browser: Xvfb + real Chrome (no container image)

There is no published Docker image for browser CUA runs today. CI drives a real, visible Chrome
under Xvfb with `xdotool`/`scrot`/`ffmpeg` for input and recording — see
[.github/workflows/browser-cua.yml](../../.github/workflows/browser-cua.yml):

```yaml
# .github/workflows/browser-cua.yml
name: Browser CUA
on: [push, pull_request]

jobs:
  browser-cua:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - run: cd browser && bun install
      - run: |
          sudo apt-get update
          sudo apt-get install -y xvfb xdotool scrot ffmpeg
          google-chrome --version
      - run: |
          Xvfb :99 -screen 0 1920x1080x24 &
          echo "DISPLAY=:99" >> $GITHUB_ENV
      - run: |
          a-test run --target browser --case examples/open-weather.yaml \
            --output-dir /tmp/browser-cua-output
        env:
          AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
          AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
          DISPLAY: ":99"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: browser-cua-output
          path: /tmp/browser-cua-output/
```

Or use the reusable action, which does the same steps and checks out `browser/` from
`dzianisv/a-test` internally:

```yaml
- uses: dzianisv/a-test/.github/actions/a-test-browser@main
  with:
    case: examples/open-weather.yaml
    output-dir: /tmp/browser-cua-output
  env:
    AZURE_CUA_API_KEY: ${{ secrets.AZURE_CUA_API_KEY }}
    AZURE_CUA_BASE_URL: ${{ secrets.AZURE_CUA_BASE_URL }}
```

Test cases for the browser runner live under [examples/](../../examples/) (`.yaml`/`.json`/`.ts`),
not a `browser/cases/` directory. There is no `--extension` or `--channel` CLI flag — the browser
runner (`browser/runner.ts`) accepts `--test-case`, `--output-dir`, `--url`, `--max-steps`, and
`--help`; the `a-test` CLI wraps it as `a-test run --target browser --case <path> [--output-dir
<dir>] [--url <url>] [--max-steps N]`.

## pytest integration (Android)

```python
# tests/test_my_feature.py
import pytest
from a_test import TestCase

def test_onboarding(cua_case):
    case = TestCase(
        name="onboarding",
        instruction="Complete the onboarding flow and reach the home screen.",
        successCriteria="Home screen with dashboard is visible",
        maxSteps=30,
    )
    result = cua_case(case)
    assert result["status"] == "success"
```

```bash
pytest tests/ --co  # list tests
pytest tests/test_my_feature.py -v
```

## Env vars reference

| Var | Used by |
|-----|---------|
| `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`) | Android runner (`a_test/client.py`) and browser runner (`browser/runner.ts`) |
| `AZURE_DEV_AI_API_KEY` + `AZURE_DEV_AI_BASE_URL` | Android + browser runners (Azure Dev AI) |
| `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` | Android runner only (Azure OpenAI) |
| `GEMINI_API_KEY` | Android runner only (Gemini) |
| `XAI_API_KEY` | Android runner only (xAI/Grok) |
| `AZURE_CUA_API_KEY` + `AZURE_CUA_BASE_URL` | Android + browser runners (Azure CUA endpoint, used in CI) |
| `HAI_API_KEY` (+ optional `HAI_BASE_URL`, `HAI_MODEL`) | Both runners — enables Holo grounding for tap-target resolution; no-op if unset |
| `CUA_MODEL` | Both runners — override the model name |
| `CUA_TOOL_TYPE` | Browser runner only — override the Responses API tool type (`computer` vs `computer_use_preview`) |
| `CHROME_PATH` | Browser runner only — override the Chrome binary path |
