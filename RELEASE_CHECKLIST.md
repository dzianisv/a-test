# a-test Release Readiness Checklist

## PRD Requirements
- [ ] Framework is easy to install and use (pip install a-test — blocked until first tagged release; source install pinned to a commit SHA works today, see docs/VERSIONING.md)
- [ ] README has quickstart for install and use (Android + Browser)
- [ ] README has CI integration quickstart (GitHub Actions)
- [ ] Reusable GitHub Action helpers created (a-test-android, a-test-browser)
- [ ] Example test cases demonstrate real use (not just "verify UI visible")

## TDD Requirements
- [ ] CUA loop passes for Android target (adb + vision model)
- [ ] CUA loop passes for Browser target (CDP + xdotool + vision model)
- [ ] Test case schema supports YAML/JSON/Python (all three formats)
- [ ] CLI accepts `--target`, `--case`, `--output-dir`, `--url`, `--model`
- [ ] Output artifacts: screenshots, demo.gif, result.json, recording.mp4
- [ ] Verification step runs post-loop (judge final screenshot against success criteria)

## CI/Quality
- [ ] All CI jobs pass: Lint, Browser CUA, Android CUA, CUA Chrome Extension
- [ ] Browser CUA test (open-weather.yaml) — fetches real data, agent confirms visible
- [ ] Android CUA test (calculator_math.py) — computes 27+18, agent verifies the result 45
- [ ] Chrome Extension test — verifies Vibe extension is published on CWS
- [ ] Webapp test (vibebrowser.app) — navigates live site, confirms loads

## Documentation
- [ ] README.md: Install section ✅
- [ ] README.md: Quickstart Android ✅
- [ ] README.md: Quickstart Browser ✅
- [ ] README.md: Example test case YAML ✅
- [ ] README.md: CI integration (one-liner Actions) ✅
- [ ] README.md: CI manual setup (detailed YAML) ✅
- [ ] README.md: Demo GIFs or videos from CI runs
- [ ] docs/ci.md: Composite action usage guide ✅
- [ ] docs/ci.md: Manual workflow templates ✅

## Pre-Release Actions
- [ ] Run full test suite locally and in CI
- [ ] Verify demo artifacts (GIFs/videos) are meaningful
- [ ] Commit or upload demo artifacts to repo or release notes
- [ ] Docs/actions/examples pin to a commit SHA, not `@main` (docs/VERSIONING.md) — see PR remediating install/reuse audit findings
- [ ] Create and push a `vX.Y.Z` tag (the Publish to PyPI workflow publishes it automatically)
- [ ] Configure PyPI Trusted Publishing for `dzianisv/a-test`, workflow `publish-pypi.yml`, environment `pypi`
