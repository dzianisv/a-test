# Agent Guidance for `browser/`

This file is loaded by AI coding assistants working in this directory.
Read it before modifying `runner.ts`, `Dockerfile`, or `setup-chrome-profile.sh`.

## What this directory actually is

`browser/` holds a Bun/TypeScript CUA (computer-use-agent) runner,
`runner.ts`, that drives a real Chrome browser via CDP while a vision/LLM
model decides what to click, type, or wait for. `cases/` is currently
**empty** — it's a placeholder for future browser-specific case files. Real,
working test cases live under `../examples/` (relative to `browser/`) as
`.yaml`, `.ts`, or `.py` files (e.g. `examples/open-weather.yaml`,
`examples/install-extension.yaml`, `examples/vibebrowser/*.yaml`,
`examples/dual-surface/*.ts`, `examples/browser/install_auth.py`).

There is no `tests/cua/` directory in this repo, no Vibe browser
extension/sidepanel/Co-Pilot feature under test here, and no
`--extension-path` / `--channel` flags on `runner.ts`. If you find guidance
referencing any of those, it does not apply to this repo — do not act on it.

## Real CLI surface (verify against `runner.ts`'s `printHelp()` before trusting this)

```
bun runner.ts --test-case <name|path> --output-dir <dir> [--url <url>] [--max-steps <n>]
```

- `--test-case` (required) — basename or file path, `.ts`/`.yaml`/`.yml`/`.json`.
- `--output-dir` (required) — directory for screenshots and log outputs.
- `--url` (optional) — overrides the test case's `url` field.
- `--max-steps` (optional) — overrides the maximum automation steps.
- `--help` — prints usage.

Do not invent additional flags. `browser/package.json`'s `"test"` script
currently points at a stale, nonexistent path
(`tests/cua/cases/google-oauth.ts`) — don't use it as a working example;
use the CLI form above directly with a real case path under `../examples/`.

## Anti-hallucination guard — real, and load-bearing

After the CUA loop itself reports success, `verifyResult()` in `runner.ts`
(around line 591) runs a second, independent check before the result is
finalized:

1. It takes a **fresh screenshot** — not the last frame from the loop, since
   the agent may have emitted a success claim while looking at the wrong
   page or state.
2. It calls a vision/judge model with the test case's `verification.prompt`
   field (test cases may define `verification: { prompt: "..." }`; see
   `examples/install-extension.yaml` for a real example).
3. It parses a YES/NO answer. If the answer is NO, or the verification API
   call itself errors, the result is flipped to FAIL and the verifier's
   evidence (or error) becomes the failure reason — even though the CUA
   loop claimed success.

This logic lives around `runner.ts:591-660` (the `verifyResult()` function)
and is gated in around `runner.ts:1053-1080`, where `testCase.verification?.prompt`
is checked and `verification.passed` decides the final pass/fail. If a case
has no `verification.prompt`, the runner falls back to asking the same
question using the case's `successCriteria` instead — so most non-trivial
cases still get a second-opinion check.

**Do not weaken this guard.** If you touch `verifyResult()` or the gating
logic around it, preserve: the fresh-screenshot capture, the YES/NO parse
against `verification.prompt` (or the `successCriteria` fallback), and the
rule that verification API errors force FAIL rather than silently passing.

## Where to add new test cases

Real case files belong under `../examples/` (`.yaml`, `.ts`, or `.py`), not
`browser/cases/` (which is an empty placeholder today). If you add a case
that reaches a state the CUA loop might mis-evaluate — which is essentially
any non-trivial end-to-end flow — give it a `verification.prompt` so the
post-loop guard described above actually runs against it.

## Debugging artifacts

The runner writes to `--output-dir`. Inspect these when a case fails:
- `runner-log.jsonl` — per-step model output, actions, and results.
- `verification.json` — the verifier's pass/fail, evidence, or error (only
  present when a verification step ran).
- `verification-screenshot.png` — the fresh screenshot the verifier judged.
- `step-*.png` — screenshots captured during the CUA loop itself.
