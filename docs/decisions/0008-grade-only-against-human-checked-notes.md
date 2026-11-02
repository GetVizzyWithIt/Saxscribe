# ADR-0008: Grade only against human-checked or aligned notes

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Claude (routine)
- **PR**: #8

## Context
JazzSAMBA's sax MIDI (`*.transcribed.derived.mid`) and MedleyDB-Pitch's note
files are another model's output. Scoring against them would measure
agreement with that model, not correctness.

## Decision
Answer keys are human-checked notes (tier A) or scores aligned to the
performance (tier B). Machine-made notes (tier D) are never graded against;
they may be used as drafts to correct, or for separation work.

## Consequences
JazzSAMBA has no scorecard set for notes. It stays valuable for separation
(stems vs mixes) and as tenor audio.
