# ADR-0017: Grade only inside the answer key's time span

- **Date**: 2026-11-02
- **Status**: Proposed (PR #16 open)
- **Decided by**: Claude (bug fix)
- **PR**: #16

## Context
Each Omnibook aligned MIDI covers roughly one chorus, while the stem keeps
going. Notes the tool found after the key ended counted as false positives,
so every Omnibook score so far (note F1 45.0%) is understated.

## Decision
Score only the part of the recording the answer key covers.

## Consequences
- Earlier Omnibook rows in the evaluation log are marked understated and will be re-run.
- New loaders should state each key's coverage.
