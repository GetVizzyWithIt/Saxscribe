# ADR-0033: Nothing below the horn's low note on the sheet

- **Date**: 2026-11-04
- **Status**: Accepted (PR #81 merged)
- **Decided by**: Austin (2026-11-04, 11:24 am PT)
- **PR**: #81
- **Refines**: [ADR-0031](0031-range-rules-per-horn.md)

## Context
ADR-0031 kept notes up to 2 half steps below the lowest key (`BEND_ROOM`), as a
possible lipped-down or flat low note, and only tagged them red. On Pennies From
Heaven that let 14 piano or bass notes (written A3 on tenor) onto the sheet
([log E40](../evaluation/log.md)). Austin: soprano, alto and tenor never play
below low B♭; low A belongs to the bari.

## Decision
- On every take, a note below the horn's lowest written note is tagged `not_sax` and `below_range` and left off the notation.
- It stays in `notes.json` (never deleted, [ADR-0016](0016-notation-never-drops-notes.md)).
- The pitch search still reaches `BEND_ROOM` below the low note, so such notes are found and tagged rather than misread as another pitch.
- Bari's low A is its lowest note, so nothing changes for bari.

## Consequences
- Note F1: Pennies From Heaven +0.11 (4 notes hidden), GRFIA alto +0.03 (8), Omnibook about 0 (3) ([log E43](../evaluation/log.md)).
- On a fresh Pennies run one hidden note was real sax (−0.12 onset recall); it is still in `notes.json`.
- A real low B♭ played very flat would be hidden; it is still in `notes.json` and can be restored in the editor.
