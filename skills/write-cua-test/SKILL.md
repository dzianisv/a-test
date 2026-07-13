---
name: write-cua-test
description: Write a new computer-use agent (CUA) test case for a-test. Use when asked to add a test for an Android app or browser extension behavior.
---

# Write a CUA Test Case

## Schema

Every a-test test case is a `TestCase` dataclass:

```python
from a_test import TestCase

case = TestCase(
    name="feature_smoke",              # snake_case, unique
    instruction="...",                  # NL goal — what the agent should DO
    successCriteria="...",             # what PASS looks like on screen
    failureCriteria="...",             # early-abort signal (optional but recommended)
    maxSteps=25,                       # hard cap on LLM turns
    # verification=Verification(prompt="YES/NO: does the screen show X?")  # optional
)
```

## Instruction-writing rules
1. Be specific: name buttons, screens, text. "Tap the blue 'Submit' button" beats "submit the form."
2. Include wait hints: "Wait up to 10 seconds for the results screen."
3. State done condition explicitly: "Report done when the success dialog is visible."
4. State fail condition: "Report fail if an error banner appears."
5. Never use `enter` key to submit — always tap the send/submit button.

## successCriteria / failureCriteria
- successCriteria: plain English — what the verifier looks for on screen.
- failureCriteria: early-abort trigger (error message text, crash indicator).

## Running a case

```bash
# Android (adb device required)
a-test run --target android --case examples/android/calculator_math.py

# Browser (bun required)
a-test run --target browser --case examples/vibebrowser/vibe-install-smoke.yaml \
  --output-dir /tmp/out
# No --extension flag: to test a Chrome extension, write a case whose goal
# navigates to the Chrome Web Store listing and installs it via the browser UI.

# View the GIF
open /tmp/a-test-output/demo.gif   # macOS
xdg-open /tmp/a-test-output/demo.gif  # Linux
```

## Reading the output
Screenshots named `step-NNN_*.png` show what the agent saw and did at each step.
`demo.gif` is assembled from all steps — scan it to see where the agent got confused.
The pass/fail verdict is in `result.json` (Android: `{"verdict", "reason", "steps"}`)
or `verification.json` (browser). The CLI also prints `RESULT: pass` / `RESULT: fail`
and exits non-zero on fail.

## Common pitfalls
- `maxSteps` too low: raise to 30–40 for multi-step flows.
- Instruction too vague: add button names, expected text.
- Missing `successCriteria`: add it — the verifier judges the final screenshot against it.
- Android: set one provider — `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY` (+ `AZURE_OPENAI_ENDPOINT`), `AZURE_DEV_AI_API_KEY` (+ `AZURE_DEV_AI_BASE_URL`), `GEMINI_API_KEY`, or `XAI_API_KEY`.
- Browser: ensure `AZURE_CUA_API_KEY` + `AZURE_CUA_BASE_URL` are set.
