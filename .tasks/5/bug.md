## Bug: Android demo GIF ignores the screen recording

### Symptoms
The generated OpenCode artifact `demo.gif` has a 0.04-second duration and one static frame, while `opencode-smoke.mp4` was recorded during the same run.

### Reproduce
```bash
gh run download 29215549469 --name cua-android-output-demo-4 --dir /tmp/a-test-opencode-demo
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/a-test-opencode-demo/demo.gif
```

Confirmed: yes — output is `0.040000`.

### Root Cause
`a_test/loop.py` records `<case>.mp4`, but calls `a_test.recording.assemble_gif(output_dir)`, which only concatenates `step-*.png`. The OpenCode smoke case has one screenshot, and the concat output becomes a one-frame GIF.

### Regression Test
Run `assemble_gif_from_video()` against the provenance OpenCode Mobile `docs-site/demo.mp4`; it must produce a `demo.gif` with duration greater than one second and multiple frames. This command fails before the fix because the MP4 conversion API does not exist.
