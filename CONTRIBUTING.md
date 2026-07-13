# Contributing to a-test

Thanks for your interest in contributing to `a-test`, a test harness for computer-use agents
testing Android apps and web apps. This guide covers local setup, how to validate your changes,
and what we expect in a pull request.

## Local Setup

`a-test` has two parts: a Python CLI/package (`a_test/`) and a Bun/TypeScript browser runner
(`browser/`).

```bash
# Python package (editable install)
pip install -e .

# Browser backend (Bun/TypeScript runner, run from a repo checkout)
cd browser && bun install
```

Requires Python >= 3.10. See [pyproject.toml](pyproject.toml) for the full dependency list
(`openai>=1.0`, `pyyaml>=6.0`).

Once installed, the CLI entrypoint is `a-test`:

```bash
a-test run --target {android,browser} --case <path> \
  [--output-dir <dir>] [--model <name>] [--url <url>] \
  [--max-steps N] [--include-xml] [--speed-multiplier N]
```

## Running the Test Suite

The internal Python logic (judge, grounding, case-loading) is covered by a unit test suite:

```bash
python -m pytest tests/ -q
```

## Running Lint

```bash
python -m pyflakes a_test/
```

Both commands are wired into CI (`.github/workflows/lint.yml`); please run them locally before
opening a PR.

## Writing New Test Cases

If your contribution adds or changes CUA (computer-use agent) test cases, start here:

- [docs/writing-cases.md](docs/writing-cases.md) — the `TestCase` schema (`name`, `instruction`,
  `successCriteria`, `failureCriteria`, `maxSteps`, optional `Verification`).
- [skills/write-cua-test/SKILL.md](skills/write-cua-test/SKILL.md) — a step-by-step skill for
  authoring new CUA test cases.

## Testing Philosophy

The primary way we validate `a-test`'s product behavior is with real, agent-driven CUA/E2E
tests — against a real Android emulator, a real browser, and real websites — not mocks. Per
[AGENTS.md](AGENTS.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), demo artifacts must show
**meaningful agent interaction** (e.g. the agent computes 27+18 and verifies the result is 45),
not just static UI recognition (e.g. "a keypad exists").

The `tests/` directory unit tests are an intentional, narrower exception: they cover internal
Python logic (judge, grounding, case-loading) that doesn't need a live device or browser. Please
don't add more mocked unit tests as a general substitute for CUA coverage — if you're testing
product/agent behavior, add or extend a real CUA test case instead of mocking it.

## Pull Request Expectations

- Keep changes scoped to a single concern; avoid unrelated refactors in the same PR.
- Include real verification output in your PR description (e.g. `pytest` and `pyflakes` results,
  or a CUA test run) — don't just claim it passes.
- Never commit secrets, API keys, or `.env` files.
- Never commit demo screenshots, GIFs, or video recordings into the repo (see
  [.gitignore](.gitignore) — `*.gif`, `*.mp4`, `step-*.png`, `stage-*.png` are ignored except for
  a few curated example assets). Instead, publish demo evidence as PR/issue attachments via the
  GitHub UI, following
  [skills/a-test-video-github-upload/SKILL.md](skills/a-test-video-github-upload/SKILL.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License (see
[LICENSE](LICENSE)).
