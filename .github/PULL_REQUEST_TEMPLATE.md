<!--
Thanks for contributing to a-test! Please fill this out — see CONTRIBUTING.md for details on
local setup, running the test suite, and our real-CUA-only testing philosophy.
-->

## What does this PR do?

<!-- Briefly describe the change and why it's needed. -->

## How was this verified?

<!--
Real verification, not just "it should work". Include actual command output where possible:
- `python -m pyflakes a_test/` (or the relevant package)
- `python -m pytest tests/ -q`
- A real CUA test run (`a-test run --target android|browser --case <path> ...`) with the
  resulting result.json/GIF, if this touches the CUA loop, judge, grounding, or a runner.
-->

## Checklist

- [ ] Changes are scoped to a single concern (no unrelated refactors).
- [ ] I ran the relevant checks above and included their output.
- [ ] No secrets, API keys, or `.env` files are included in this PR.
- [ ] No test-run screenshots/GIFs/videos (per-run `--output-dir` artifacts, e.g. `step-*.png`,
      `recording.mp4`) are committed to the repo — publish those as PR/issue attachments instead,
      see [skills/a-test-video-github-upload/SKILL.md](../skills/a-test-video-github-upload/SKILL.md).
      Curated, reviewed public demo assets under `assets/`, `docs/showcase/`, or
      `examples/screenshots/` (see [README.md](../README.md#demo-agents-in-action)) are fine to commit.
- [ ] If this adds product/agent-behavior coverage, it's a real CUA/E2E test case (not a new mock
      or unit test) — see [CONTRIBUTING.md](../CONTRIBUTING.md#testing-philosophy).
