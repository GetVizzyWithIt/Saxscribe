# ADR-0018: Readable notation over literal rhythm, without dropping notes

- **Date**: 2026-11-02
- **Status**: Accepted (PR #21 merged)
- **Decided by**: Claude (routine)
- **PR**: #21

## Context
The first complete PDF kept every note but read badly: 32nds and dotted
figures where a player would write swung eighths, empty bars written one by
one, and F#/Gb mixed in one line.

## Decision
The notation layer writes what a sax player would read: swung pairs as plain
eighths, real triplets as triplets, runs of empty bars as one numbered rest,
and one enharmonic spelling per part chosen from the horn's key. The exact
played timing stays in `notes.json` and `score.mid`, so nothing is lost by
simplifying the written rhythm.

## Consequences
- Fidelity holds: every note is still written (checked on the synthetic solos).
- Readability is measured on synthetic swing solos for now; the real test is
  edits per 100 notes on Austin's 10 fixed tunes.
