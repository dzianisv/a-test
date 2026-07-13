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

Once v0.1.0 ships to PyPI:

```bash
pip install a-test
```

## Android quickstart

Requires: `adb` in PATH, a connected device or emulator, an Azure OpenAI key.

```bash
export AZURE_CUA_API_KEY=...
export AZURE_CUA_BASE_URL=https://<your-resource>.openai.azure.com/
export AZURE_CUA_MODEL=gpt-5.4

a-test run \
  --target android \
  --case examples/android/calculator_math.py \
  --output-dir /tmp/a-test-output

open /tmp/a-test-output/demo.gif
```

## Browser quickstart

Requires: `bun` in PATH (https://bun.sh), `xdotool`, `scrot`, `ffmpeg`, and an Azure OpenAI key.

```bash
export AZURE_CUA_API_KEY=...
export AZURE_CUA_BASE_URL=https://<your-resource>.openai.azure.com/
export AZURE_CUA_MODEL=gpt-5.4

a-test run \
  --target browser \
  --case examples/open-weather.yaml \
  --output-dir /tmp/a-test-output

open /tmp/a-test-output/demo.gif
```

Instead of `AZURE_CUA_*`, you can also authenticate with `AZURE_OPENAI_API_KEY`
(+ `AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_BASE_URL`) or plain `OPENAI_API_KEY`
(+ optional `OPENAI_BASE_URL`).

### Testing a Chrome extension

There is no `--extension` flag. To test a Chrome extension, write a YAML case
whose goal navigates Chrome to the Chrome Web Store and installs the extension
through the normal browser UI, just like a user would. See
`examples/install-extension.yaml` for a real, working example of this pattern.

## View GIF output

`--output-dir` is whatever directory you pass on the command line; the
examples above use `/tmp/a-test-output` purely for illustration. Each run
writes:

```
<output-dir>/
  step-01-screenshot.png
  step-02-tap.png
  ...
  demo.gif
```

`demo.gif` shows each step the agent took. Scan it to see where it succeeded or got confused.
