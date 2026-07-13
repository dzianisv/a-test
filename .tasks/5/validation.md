## Validation plan for 5

### Tier

e2e

### Test cases

| # | Input | Expected behavior | Channel |
|---|---|---|---|
| 1 | Linked public OpenCode `docs-site/demo.mp4` | New converter writes a multi-frame GIF lasting over one second | Local ffmpeg through production `a_test.recording` API |
| 2 | Missing MP4 path | Converter returns `None`; screenshot fallback remains selected | Local `a_test.run_case` code path |
| 3 | GitHub Actions Android OpenCode workflow | Artifact contains an animated `demo.gif` sourced from recording | `cua-android-app.yml` workflow artifact |
| 4 | Public a-test README | Animated OpenCode GIF displays connection setup and loaded sessions; MP4 remains link | GitHub README |

### Pass criterion

The public GitHub README displays a multi-step animated OpenCode GIF generated from the recorded MP4, while retaining the MP4 as a secondary full-recording link.

### Evidence

Record GIF duration/frame count, inspect samples spanning the start, connection entry, and loaded-session end state, and open rendered README bytes from GitHub after merge.
