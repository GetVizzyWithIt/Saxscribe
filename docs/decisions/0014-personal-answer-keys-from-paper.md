# ADR-0014: Austin's paper transcriptions become personal answer keys via OMR

- **Date**: 2026-11-02
- **Status**: Accepted, not started
- **Decided by**: Austin (source); Claude (method)

## Context
Austin owns many printed jazz transcriptions for alto and tenor, and the
records they come from. Paired, they are full-mix answer keys on music he
actually wants to learn.

## Decision
Scan one PDF per tune (noting recording and horn) → optical music recognition
(Audiveris or oemer) → MusicXML → hand fix → align to the record with the
`answer-key` aligner → `pairs` scorecard set. Audio stays private on the Mac.

## Consequences
- Printed transcriptions carry editorial choices; treat them as tier B until spot-checked.
- Written pitch differs by horn; the horn must be recorded per scan.
