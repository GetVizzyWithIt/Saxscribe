# ADR-0005: Alto first, tenor first-class, organised per instrument

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Austin

## Context
The requirements said "alto or tenor first; check transfer later". Austin chose
alto, then added that he plays both and his transcriptions cover both. Later he
set the long-term goal: transcribe any instrument by separating each one and
using instrument-specific models.

## Decision
- Alto is the default (`--horn alto`); tenor and baritone are switchable profiles (range + transposition).
- Datasets, scorecard sets and future models are organised per instrument, so
  a new instrument is a new profile, set and model, not a rewrite.
- Planned rename: "horn" → "instrument" in code when that code is next touched.

## Consequences
- Tenor gets its own scorecards (JazzSAMBA tenor, Weimar tenor with Austin's records, Filosax).
- Datasets with other instruments (URMP, FiloBass, TinySOL) are kept for later instruments.
