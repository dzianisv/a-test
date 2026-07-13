## Problem / Goal / Success Metric

Android CUA captures a full MP4 recording but publishes a GIF built from screenshots. One-step flows consequently produce a static GIF. Prefer a GIF converted from the actual recording, preserve screenshot assembly when capture fails, and embed the resulting OpenCode demo in the public README.

Success metric: `open https://github.com/dzianisv/a-test#opencode-mobile-android-onboarding--real-coding-task` shows a multi-step animated OpenCode GIF; the MP4 remains a secondary full-recording link.

## Current State

- `a_test/loop.py:256-279` starts and stops Android screen recording, writes `<case>.mp4`, then ignores it while calling screenshot-only `assemble_gif(output_dir)`.
- `a_test/recording.py:122-186` filters `step-*.png` and uses ffmpeg's concat demuxer for `demo.gif`.
- `.github/workflows/cua-android-app.yml:93-101` already uploads both `demo.gif` and `opencode-smoke.mp4`.
- `README.md:90-98` shows a static OpenCode screenshot and only an external MP4 link.

## Proposed Design

1. Add `assemble_gif_from_video(video_path, output_dir)` in `a_test/recording.py`. It uses the repository's existing two-pass ffmpeg palette pattern, verifies each ffmpeg command succeeds, and returns `None` for missing, empty, or failed video output.
2. In `run_case`, retain `rec_local` outside `finally`, record whether `stop_screen_recording` pulled the MP4, and prefer `assemble_gif_from_video(rec_local, output_dir)`. If recording is unavailable or conversion fails, run unchanged `assemble_gif(output_dir)`.
3. Convert the public, provenance-linked OpenCode MP4 to `docs/showcase/opencode-smoke.gif`; replace the static README screenshot with this GIF and retain the external MP4 as the secondary full-recording link.
4. Update documentation describing `demo.gif` to make recorded-video conversion and screenshot fallback explicit.

## Alternatives Considered

- Keep screenshot concat and duplicate final frame: rejected because it cannot show movement or agent interaction between screenshots.
- Convert only the static external OpenCode MP4: rejected because future Android artifacts would still publish static GIFs.
- Replace GIF with MP4/WebM only: rejected because the requested, embeddable README proof is GIF and MP4 remains useful as full recording.

## Risks & Mitigations

- GIF size/cost: downscale and use a capped frame rate; source OpenCode recording converts to 395 KiB.
- ffmpeg conversion failure: return `None` and preserve existing screenshot GIF behavior.
- Recording absent or empty: use existing fallback unchanged.
- Stale showcase bytes: derive `docs/showcase/opencode-smoke.gif` from the cited public MP4 and visually sample frames before commit.

## Touched Surface

- `a_test/recording.py`
- `a_test/loop.py`
- `README.md`
- `docs/showcase/opencode-smoke.gif`
- `PRD.md`
- `TDD.md`
