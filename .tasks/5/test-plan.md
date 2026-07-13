## Modality

Real recorded-video integration test plus workflow artifact and public README verification.

## Setup

Download `https://raw.githubusercontent.com/dzianisv/opencode-mobile/main/docs-site/demo.mp4`.

## Steps

1. Invoke `a_test.recording.assemble_gif_from_video()` against the public recording.
2. Inspect GIF duration and counted frames with `ffprobe`.
3. Invoke the helper with a missing path and confirm it returns `None`, retaining the screenshot fallback.
4. After merge, run the Android OpenCode workflow and open the public README GIF.

## Pass criterion

The public GitHub README displays a multi-step animated OpenCode GIF generated from the recorded MP4, with the MP4 retained as a secondary full-recording link.
