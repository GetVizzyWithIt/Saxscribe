# ADR-0030: Choose triplet or plain feel per phrase on fast beats

- **Date**: 2026-11-04
- **Status**: Proposed (PR #66 open)
- **Decided by**: Claude (build thread), from the Weimar rhythm scorecard; Austin's rhythm brief asked for rhythm chosen per phrase
- **PR**: #66
- **Refines**: [ADR-0029](0029-finer-grids-for-slow-and-busy-beats.md)

## Context
Choosing the feel beat by beat made fast runs flip between triplets and plain
eighths, writing about 37% more triplets than the Weimar transcribers ([log E33](../evaluation/log.md)).

## Decision
Pick each beat's grid with a best-path search over the phrase (an empty beat
ends a phrase). A change between triplet and plain feel costs 0.4 beats on beats
shorter than 0.45 s; slower beats switch freely. A beat's feel is read from its
own note starts only.

## Consequences
- Weimar position read: up tempo 74.8% → 77.0%, all 444 solos 65.9% → 67.4%; slow tunes and ballads unchanged; every note still written.
- Triplets fall from 1.37× to 0.76× of Weimar's count; a higher switch cost scored more but halved real triplets, so it was rejected.
- Some real triplets in fast passages may now be written as plain eighths; check on Austin's own transcriptions.
