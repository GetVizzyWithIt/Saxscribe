# ADR-0029: Finer beat grids for slow and busy beats

- **Date**: 2026-11-04
- **Status**: Accepted (PR #64 merged)
- **Decided by**: Claude (build thread), from the Weimar rhythm scorecard
- **PR**: #64
- **Refines**: [ADR-0018](0018-swing-aware-notation.md)

## Context
With only quarter and triplet grids, a slow or busy beat holding 6 or 8 notes
had two notes land on one spot, and the later notes were pushed into the next
slot, so whole runs were written late. Ballads were written in the right place
17% of the time and slow tunes 34% ([log E28](../evaluation/log.md), [E32](../evaluation/log.md)).
The busy beats also misled the swing reading.

## Decision
- Offer sextuplet (6 per beat) and 32nd (8 per beat) grids only on beats that last at least 0.6 s or hold 5 or more note starts, with a small penalty (0.07) so plain grids win when they fit.
- Read swing only from beats with one or two notes.
- When two notes land on one spot, move the later one by its beat's own grid step.
- Write sextuplet beats as 3:2 triplet sixteenths, so every tuplet MuseScore sees is 3:2.

## Consequences
- Weimar position read: ballads 16.9% → 36.2%, slow 34.3% → 44.0%, all 444 solos 63.1% → 65.9%; up tempo unchanged (+0.7). Every note still written.
- Slightly more triplets are written (1.29× → 1.37× Weimar's count).
- Rejected: finer grids everywhere (hurts up tempo), and a lay-back shift before quantising (up tempo collapses).
- About a third of ballad notes are free-time tuplets (5, 7, 9+ per beat) that no grid matches; choosing rhythm per phrase is the next step.
