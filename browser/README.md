# CUA Nightly Tests

This folder contains a Bun-based Computer Use (CUA) runner for real Google Chrome extension OAuth checks.

## Prerequisites

- One actor credential to drive the interactive computer-use loop (Responses API,
  `client.responses.create` with the `computer`/`computer_use_preview` tool):
  - `AZURE_CUA_API_KEY` (+ optional `AZURE_CUA_BASE_URL`), or
  - `AZURE_DEV_AI_API_KEY` + `AZURE_DEV_AI_BASE_URL` (an alternate Azure OpenAI
    resource/deployment, e.g. sourced from `~/.env.d/azure-dev.env`), or
  - `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`)
- Optionally, `HAI_API_KEY` (H Company's Holo Models API, https://hub.hcompany.ai)
  to use Holo as an independent anti-hallucination verifier via Chat Completions
  (`core/vision.ts`'s `visionJudge`, `apiStyle: "chat"`) instead of having the
  actor re-check its own screenshot. Holo only implements `/chat/completions` (no
  `/responses`), so `HAI_API_KEY` alone cannot drive the interactive loop -- it
  must be set alongside one of the actor credentials above.
- Unpacked extension directory (or unzip via `setup-chrome-profile.sh`)
- Host dependencies installed (or run in `tests/cua/Dockerfile` image)

## Local Docker pattern

`docker build -t vibe-cua-test tests/cua && docker run -e OPENAI_API_KEY=... vibe-cua-test`

Example with explicit args:

```bash
docker build -t vibe-cua-test tests/cua
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -v "$PWD/dist:/workspace/dist:ro" \
  vibe-cua-test \
  --extension-path /workspace/dist/prod-unpacked \
  --test-case /app/cases/google-oauth.ts \
  --output-dir /workspace/dist/google-oauth-cdn \
  --channel cdn
```

## Specific case execution

```bash
bun tests/cua/runner.ts \
  --extension-path dist/prod-unpacked \
  --test-case tests/cua/cases/google-oauth.ts \
  --output-dir tests/cua/output/google-oauth-cdn \
  --channel cdn

bun tests/cua/runner.ts \
  --extension-path dist/prod-webstore-unpacked \
  --test-case google-oauth \
  --output-dir tests/cua/output/google-oauth-cws \
  --channel cws
```

`--test-case` accepts absolute path, relative path, or basename from `tests/cua/cases` (or `/app/cases` inside the Docker image).

## Prepare extension and Chrome profile

```bash
tests/cua/setup-chrome-profile.sh dist/prod.zip
```

Script output uses `key=value` lines:
- `extension_dir`: unpacked extension path for `--extension-path`
- `chrome_user_data_dir`: reusable Chrome profile directory

## Debugging screenshots

The runner saves artifacts in `--output-dir`:
- `step-00.png` initial screenshot sent with instruction
- `step-XX-aY.png` latest screenshot captured after each CUA action/tool output
- `step-XX-aY-action-screenshot.png` explicit screenshot action captures
- `runner-log.jsonl` model output, actions, and execution results

Use these files to inspect why OAuth navigation succeeded or failed.

## Adding cases

1. Create `tests/cua/cases/<name>.ts`.
2. Export a case object with at least:
   - `instruction`
   - `successCriteria` (or legacy `criteria`)
   - optional `failureCriteria`, `extensionId`, `maxSteps`, `name`
3. Recommended export style:
   - named export (for example `export const myCase = { ... }`)
   - plus `export default myCase`
4. Run with `--test-case <basename|path>`.
