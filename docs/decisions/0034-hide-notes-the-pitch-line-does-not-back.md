# ADR-0034: On band records, hide notes the sax's pitch line doesn't back up

- **Date**: 2026-11-04
- **Status**: Accepted (PR #93 merged 2026-11-05; same code as #84, which was closed without merging)
- **Decided by**: Claude (build thread), from the Pennies From Heaven piano-bleed review
- **PR**: #93 (first opened as #84)
- **Relates to**: [ADR-0016](0016-notation-never-drops-notes.md), [ADR-0023](0023-write-only-where-the-sax-plays.md)

## Context
On Pennies From Heaven, 87 notes in the tenor's range in the keyed half (9% of the
sheet) are piano or bass, and a 39 s piano solo put about 65 notes on the sheet
([log E46](../evaluation/log.md)). Demucs leaves Oscar Peterson's piano inside the
same "vocals + other" stem as the sax, so separation can't remove it. The CREPE
pitch line follows the sax and ignores most of the piano.

## Decision
In `layers/bleed.py`, on mix takes only, tag a note `not_sax` with a reason and leave it off the sheet:
- `no_pitch_line`: the pitch line is unvoiced for 8 s or more around it (a solo by another instrument).
- `off_line`: the line is voiced for at least 80% of the note but never on its pitch or its octave, and more than a semitone away on at least 60% of frames.

Notes stay in `notes.json` (never deleted). Solo takes are untouched.

## Consequences
- Note F1 ([log E48](../evaluation/log.md)): Pennies From Heaven 49.2% → 49.8% (the 3:42–4:21 piano solo hidden), Parker band records 57.6% → 57.8%, Blues for Mary Jane 56.0% → 56.2%; solo sets unchanged.
- At most one real sax note hidden per set; it can be restored in the editor. Austin checked the 93 suspect notes on Pennies From Heaven by eye and confirmed they are not sax (2026-11-04).
- Piano notes under held sax notes are only partly caught; keeping the note the pitch line follows where two overlap is the next step.
