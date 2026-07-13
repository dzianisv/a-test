# Quickstart

## Install

**Not yet published to PyPI** (see [README.md](../README.md#install) / [VERSIONING.md](VERSIONING.md) for why). Install from source, pinned to a commit SHA:

```bash
pip install "git+https://github.com/dzianisv/a-test.git@<commit-sha>"
```

Or clone directly:

```bash
git clone https://github.com/dzianisv/a-test
cd a-test
pip install -e .
```

## Android quickstart

Requirements: `adb` in PATH, connected device or emulator, LLM API key.

```bash
export OPENAI_API_KEY=sk-...

a-test run \
  --target android \
  --case examples/android/calculator_math.py \
  --output-dir /tmp/a-test-output

open /tmp/a-test-output/demo.gif
```

## Browser quickstart

Requirements: `bun` in PATH (https://bun.sh), built extension directory, Azure CUA credentials.

```bash
export AZURE_CUA_API_KEY=...
export AZURE_CUA_BASE_URL=https://...

a-test run \
  --target browser \
  --case browser/cases/google-oauth.ts \
  --extension /path/to/ext/dist/prod-unpacked \
  --output-dir /tmp/a-test-output

open /tmp/a-test-output/demo.gif
```

## View GIF output

```
/tmp/a-test-output/
  step-01-screenshot.png
  step-02-tap.png
  ...
  demo.gif
```

`demo.gif` shows each step the agent took. Scan it to see where it succeeded or got confused.
