## Approach Summary

Make Android `demo.gif` derive from the actual captured MP4, using screenshot assembly only as a compatible fallback. Publish a visually inspected OpenCode GIF in the README from the provenance recording.

## Tradeoff: Speed vs Quality

- chosen: balanced
- rationale: retain a compact GIF and existing fallback while verifying real video content rather than adding new dependencies or changing CI topology.

## Tasks

| # | Title | Files | Depends on | Parallel group | Suggested model |
|---|---|---|---|---|---|
| 1 | Add MP4-first GIF assembly | `a_test/recording.py`, `a_test/loop.py` | — | A | claude-sonnet-5 |
| 2 | Publish meaningful OpenCode showcase | `docs/showcase/opencode-smoke.gif`, `README.md`, `PRD.md`, `TDD.md` | — | A | claude-sonnet-5 |
| 3 | Run real-recording validation | task evidence only | 1, 2 | B | claude-sonnet-5 |

## Parallel Groups

- **A**: Tasks 1 and 2 touch separate files and can proceed independently.
- **B**: Task 3 runs after both implementation tasks.

## Done Criteria

- `assemble_gif_from_video()` converts a non-empty recording into a multi-frame `demo.gif`; a failed/missing recording falls back to existing screenshot GIF behavior.
- README embeds `docs/showcase/opencode-smoke.gif`; sampled frames show meaningful interaction; MP4 link remains secondary.
- The real provenance MP4 passes through the new code path to a GIF longer than one second; the public README renders that GIF after merge.

## Rollback Plan

Revert the MP4-first call to restore screenshot-only GIF assembly and remove the showcase asset/link in a single commit.
