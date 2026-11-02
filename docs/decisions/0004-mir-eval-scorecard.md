# ADR-0004: Every model change is measured with mir_eval against fixed targets

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: requirements doc
- **PR**: #3

## Context
Without fixed measurement, "better" is a feeling, and numbers can't be compared
with published work.

## Decision
`python -m saxscribe score` scores pitch, onsets, notes and beats with
mir_eval at standard tolerances, against the requirements' v1 targets, on
fixed answer-key sets split by tune. A change without a before/after
scorecard is not done.

## Consequences
- Every result is traceable in [evaluation/log.md](../evaluation/log.md).
- Notation quality (edits per 100 notes) still needs a hand count.
