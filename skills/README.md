# Skills Index

This file indexes the skills defined in this directory (each with its own `SKILL.md`).

## write-cua-test

- **name:** `write-cua-test`
- **description:** Write a new computer-use agent (CUA) test case for a-test. Use when asked to add a test for an Android app or browser extension behavior.
- **When to use:** use when authoring a new a-test `TestCase` (Android `.py` or browser `.yaml`/`.ts`), writing instructions/success/failure criteria, or debugging why a case's steps/GIF/`result.json` don't match expectations.
- [write-cua-test/SKILL.md](write-cua-test/SKILL.md)

## a-test-video-github-upload

- **name:** `a-test-video-github-upload`
- **description:** Produce, upload, and VALIDATE visual proof (video / GIF / screenshot) on a GitHub PR or issue for a-test runs. Use when a task's deliverable is a recording, demo, or screenshot that must be visible on GitHub, or before claiming any uploaded media is "done".
- **When to use:** use when uploading and validating a video/GIF/screenshot as proof-of-work on a GitHub PR or issue, and before ever claiming an uploaded video/GIF is "done".
- [a-test-video-github-upload/SKILL.md](a-test-video-github-upload/SKILL.md)

## a-test-ci

- **name:** `a-test-ci`
- **description:** Wire a-test into GitHub Actions CI. Use when asked to add CUA tests to a CI pipeline for an Android app or browser extension.
- **When to use:** use when adding or configuring GitHub Actions workflows that run a-test CUA tests for Android (emulator-runner) or browser (containerized Chrome) targets, or wiring pytest integration and required env vars/secrets.
- [a-test-ci/SKILL.md](a-test-ci/SKILL.md)
