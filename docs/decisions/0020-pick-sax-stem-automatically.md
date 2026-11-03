# ADR-0020: Pick the sax stem automatically, and sum stems when it is split

- **Date**: 2026-11-03
- **Status**: Proposed (PR #24 open)
- **Decided by**: Claude (routine, from scorecard evidence)
- **PR**: #24

## Context
Demucs `htdemucs_6s` has no sax stem. Layer 1 always took "other" unless
`--stem` said otherwise. On some Parker records the sax lands in "guitar", or
is split between "guitar" and "other", so the pitch line and notes followed
the wrong instrument or half the sax.

## Decision
For full mixes, pick the stem that carries the clearest single melody line,
and sum stems when the sax is split between them. `--stem` still overrides,
and all six stems stay in `stems/` to audition.

## Consequences
- Worst Parker band record: note F1 24% → about 58% ([log E11](../evaluation/log.md)).
- A first step toward any-instrument transcription: choosing a stem by what it
  contains instead of by its name.
- Does not help when other horns share the stem (URMP, Bach10 mixes); that still needs a better separator (Phase 2).
