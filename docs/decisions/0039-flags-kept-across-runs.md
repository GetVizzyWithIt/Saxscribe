# ADR-0039: Review flags are kept across re-runs and compared, never deleted

- **Date**: 2026-11-09
- **Status**: Accepted
- **Decided by**: Austin (approved the play-along feedback reviewer spec)
- **PR**: #138

## Context
Austin flags problems in the play-along (PR #116). When a song is transcribed
again with a newer pipeline, the notes change under his old flags. Deleting
those flags or re-pointing them would lose the record of what he heard and when.
Calling a flag "fixed" because the notes changed would also be wrong: a change
is not proof of a fix.

## Decision
Every flag keeps the run it was made on (`run`, `run_name`). The run id is the
time the notes layer was made, read from `take.json`. A newer run never deletes
or edits old flags. The reviewer compares each old flag with the current run's
notes in its bars and labels it **Changed now** or **Still the same**, never
"fixed". Bars played through without a flag are stored per run as **looks right**.

## Alternatives considered
- Clear flags on every re-run: simple, but loses Austin's feedback, which is
  training and test data.
- Mark a flag "fixed" when the notes change: claims more than we know, and
  could hide a change that made things worse.

## Consequences
- `flags.json` grows across runs; old files still load.
- Flags become a running before/after record for each pipeline change on
  Austin's own songs.
- Only Austin can say a flag is resolved.
