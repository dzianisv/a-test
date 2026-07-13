# browser/

Computer-use (CUA) test runner for browser targets. `runner.ts` is a
Bun/TypeScript program that drives a real Chrome browser over the Chrome
DevTools Protocol (CDP) while a vision/LLM model decides what to click, type,
or wait for, based on a natural-language test case.

## What's in this directory

- `runner.ts` — the CUA runner itself.
- `cases/` — exists but is currently **empty**, tracked only via a
  `.gitkeep` placeholder. It's a placeholder for browser-specific test case
  files; none exist yet.
- `Dockerfile` — builds a headless, X11-backed Chrome environment for running
  the runner in CI or containers.
- `setup-chrome-profile.sh` — standalone helper for preparing an unpacked
  extension directory + matching Chrome user-data directory from an
  extension zip (see below).
- `package.json`, `bun.lock` — Bun package manifest/lockfile for this
  directory.

Real, working test cases live outside this directory, under `../examples/`
(relative to `browser/`): `examples/open-weather.yaml`,
`examples/install-extension.yaml`, `examples/android-settings.yaml`,
`examples/vibebrowser/*.yaml`, `examples/dual-surface/*.ts`, and
`examples/browser/install_auth.py`.

## CLI usage

```
bun runner.ts --test-case <name|path> --output-dir <dir> [--url <url>] [--max-steps <n>]
```

Required:
- `--test-case` — Test case basename or file path (`.ts`, `.yaml`, `.yml`, or
  `.json`).
- `--output-dir` — Directory for screenshots and log outputs.

Optional:
- `--url` — Starting URL for the browser (overrides the test case's `url`
  field).
- `--max-steps` — Override the maximum number of automation steps.
- `--help` — Print this usage text.

Example, running a real case from `examples/`:

```bash
bun runner.ts --test-case ../examples/open-weather.yaml --output-dir ./out
```

There is no `--extension`, `--extension-path`, or `--channel` flag — the
runner's CLI surface is exactly the four flags listed above.

## Dockerfile

The image is based on Ubuntu 22.04 and installs Xvfb, xdotool, scrot, ffmpeg,
and related X11/headless dependencies, plus Chrome For Testing (CFT) rather
than Chrome Stable — Chrome 142+ dropped `--load-extension` from branded
Chrome, and CFT still supports it. It also installs Node.js 22 and Bun, and
copies `package.json`, `runner.ts`, `cases/`, and `setup-chrome-profile.sh`
into `/app`. If `/app/extension.zip` is present at build time it is unzipped
to `/app/extension`. The entrypoint starts Xvfb on display `:99` and then
execs `bun /app/runner.ts` with whatever CLI arguments are passed to
`docker run`, so it forwards directly to the runner's CLI described above.

## setup-chrome-profile.sh

```bash
./setup-chrome-profile.sh <extension-zip-path>
```

Unzips the given extension zip into a workdir and creates a matching Chrome
user-data directory, then prints `extension_zip=`, `extension_dir=`, and
`chrome_user_data_dir=` key=value lines. It's a standalone helper for
preparing an extension + profile directory pair for manual or future
extension-based browser testing — `runner.ts` has no flag that consumes its
output today. Note: the script's default workdir path predates the current
`browser/` layout, so double-check the printed paths before relying on them.

## More info

For the broader test-authoring workflow, CI wiring, and project overview,
see:
- `../docs/quickstart.md`
- `../docs/ci.md`
- the root `../README.md`
