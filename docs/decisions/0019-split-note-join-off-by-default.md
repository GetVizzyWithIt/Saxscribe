# ADR-0019: Split-note join off by default

- **Date**: 2026-11-02
- **Status**: Proposed (PR #22 open). Supersedes [ADR-0010](0010-join-split-notes.md)
- **Decided by**: Claude (routine, from the scorecard)
- **PR**: #22

## Context
The join from PR #10 was merged before its scorecard finished. The before/after
runs ([log E8](../evaluation/log.md)) show it lowers onset F1 and note F1 on both
clean sets: URMP note F1 64.4% → 62.8%, Bach10 87.5% → 77.1%. It merges real
repeated notes.

## Decision
`basic_pitch` is plain Basic Pitch again (plus the one-line rule). The join stays
available as `--notes-tool basic_pitch_join`; `basic_pitch_raw` remains an alias
of the default.

## Consequences
- Split notes are back as the main known solo loss; the fix needs a better
  re-attack detector (or a trained onset head), not a merge rule.
- Lesson recorded: a model change merges only after its scorecard
  ([ADR-0004](0004-mir-eval-scorecard.md)).
- ChoraleBricks and Omnibook before/after will confirm or qualify this; a narrower join rule may return.
