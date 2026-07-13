# Examples index

Every test case under `examples/`, grouped by target. "CI-covered" links to the
workflow that runs it on push/PR; "Manual" cases are not wired into CI (usually
because they need infrastructure this repo doesn't build in CI, e.g. a
pre-loaded browser extension profile or a specific device capability) — run
them locally with `a-test run --target <target> --case <path>`.

See [AGENTS.md](../AGENTS.md) for what counts as a *meaningful* CUA demo vs. a
static-verification anti-pattern.

## Android

| File | Format | Description | CI |
|---|---|---|---|
| `android/calculator_math.py` | Python | Flagship example: computes 27 + 18 on the AOSP Calculator keypad and verifies the result is 45. | [`android-cua.yml`](../.github/workflows/android-cua.yml) |
| `android/opencode-smoke.yaml` | YAML | Installs the opencode Mobile APK from F-Droid and verifies its main UI renders after launch. | [`cua-android-app.yml`](../.github/workflows/cua-android-app.yml) |
| `android/opencode_checks.py` | Python | **Reference/pattern only, not a runnable `TestCase`.** Deterministic REST-API helpers (poll opencode's `/session` endpoint) meant to be paired with `opencode-smoke.yaml`'s CUA run for a layered assertion. Copy and adapt for your own app's API. |  |
| `android/network_drop.py` | Python | Drops Wi-Fi/data mid-operation via `adb`, then verifies the app shows an offline state and recovers when connectivity returns. | Manual — needs `adb shell svc wifi/data` toggle support on the target device/emulator, which isn't validated on the shared CI runner image. |
| `android-settings.yaml` | YAML | Opens Android Settings and navigates to "About phone", confirming the target screen renders. Canonical CLI example referenced in [PRD.md](../PRD.md). | Manual — needs a connected Android device/emulator; not wired to a CI job. |

## Browser

| File | Format | Description | CI |
|---|---|---|---|
| `open-weather.yaml` | YAML | Fetches live weather data on a real site and confirms the temperature is visible. | [`browser-cua.yml`](../.github/workflows/browser-cua.yml) |
| `install-extension.yaml` | YAML | Generic Chrome Web Store install template — installs the extension at `url` and confirms onboarding/auth UI appears. Swap `url` for any CWS listing. | Manual — the Vibe-specific fork of this pattern (`vibebrowser/vibe-install-smoke.yaml`) is what actually runs in CI. |
| `browser/install_auth.py` | Python | Illustrative wrapper showing how to shell out to the `a-test` CLI from Python for a browser case with an extension loaded. The referenced case path is a placeholder — swap in your own `.ts` case. | Manual/reference only. |

## VibeBrowser (Chrome extension)

See also [`vibebrowser/README.md`](vibebrowser/README.md).

| File | Format | Description | CI |
|---|---|---|---|
| `vibebrowser/vibe-install-smoke.yaml` | YAML | Installs the Vibe extension from the real Chrome Web Store and verifies the onboarding/auth UI appears. | [`cua-chrome-extension.yml`](../.github/workflows/cua-chrome-extension.yml) |
| `vibebrowser/vibebrowser-webapp.yaml` | YAML | Loads the vibebrowser.app landing page and confirms content renders. | [`cua-chrome-webapp.yml`](../.github/workflows/cua-chrome-webapp.yml) |
| `vibebrowser/vibe-settings-provider.yaml` | YAML | Navigates to the Vibe extension's settings page and confirms a provider/model selector is visible. | Manual — requires a Chrome profile with the Vibe extension already loaded (`CUA_EXTENSION_ID` env var). |
| `vibebrowser/vibe-sidepanel-smoke.yaml` | YAML | Opens the Vibe extension side panel and confirms Vibe-branded UI renders without errors. | Manual — requires a Chrome profile with the Vibe extension already loaded. |

## Dual-surface (terminal + browser)

| File | Format | Description | CI |
|---|---|---|---|
| `dual-surface/chrome-sync-login.ts` | TypeScript | Drives a real `xterm` + Chrome side by side to verify a terminal login syncs into the browser session. | [`cua-chrome-sync-login.yml`](../.github/workflows/cua-chrome-sync-login.yml), [`cua-chrome-sync-login-hcompany.yml`](../.github/workflows/cua-chrome-sync-login-hcompany.yml) |
| `dual-surface/terminal-and-browser.ts` | TypeScript | Coordinates a terminal task and a browser task in the same run. | [`cua-dual-surface.yml`](../.github/workflows/cua-dual-surface.yml) |

## Other files

- `screenshots/android/`, `screenshots/browser/` — committed demo GIFs/screenshots from past runs, referenced for illustration only; not test cases.
