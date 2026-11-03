# ADR-0016: Notation never drops a detected note

- **Date**: 2026-11-02
- **Status**: Accepted (PR #15 and PR #17 merged; 398 of 398 notes on the re-check). Amended by [ADR-0023](0023-write-only-where-the-sax-plays.md) (proposed): notes tagged `not_sax` on band records are kept in `notes.json` but not printed
- **Decided by**: Claude (bug fix under the fidelity rule)
- **PR**: #15

## Context
The first real PDF had 42 of 398 notes. Beat This! found almost no beats on
unaccompanied sax, and notes that couldn't be placed on the grid were silently
left out. That breaks the project's core rule: fidelity over playability.

## Decision
The notation layer must write every note in `notes.json`. When the beat grid
is missing or too sparse, it falls back to a grid it can build rather than
skipping notes.

## Consequences
- Add a notation fidelity check to scorecards and tests: notes written = notes detected.
- Silent drops anywhere in the pipeline are treated as bugs, not tuning.
