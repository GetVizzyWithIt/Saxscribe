# ADR-0021: Take the beat from the notes when the beat tracker finds too few beats

- **Date**: 2026-11-03
- **Status**: Accepted (PR #29 merged)
- **Decided by**: Claude (routine, from readability evidence)
- **PR**: #29

## Context
Notation snaps notes to the beat grid from Beat This!. On a lone sax with no
rhythm section the tracker finds few beats: 13 in 90 s on the Parker test
solo, about 1.5 real beats apart. Filling the gaps evenly gave 162 BPM for a
solo at about 261 BPM, so swung eighths were written as triplets and 32nds.

## Decision
When filling the tracker's gaps would invent more of the grid than the
tracker found, and there are at least 16 notes, derive the beat from the note
onsets (autocorrelation over 80–300 BPM, then a beat-by-beat walk that leans
toward nearby notes, with the beat length held within 10%). Dense tracked
grids, such as band recordings, are kept unchanged. notation.json and the log
say which source the grid came from.

## Consequences
- Parker test solo: 32nds 80 → 1, plain eighths 88 → 231, squeezed notes 85 → 1, tempo 162 → 264 BPM, every note kept ([log E13](../evaluation/log.md)).
- Notes, onset and pitch scores are unaffected; the change is in Layer 4 only.
- A note-derived grid can lock onto the wrong level (half or double time) on sparse or rubato playing; the shortest-strong-lag rule and the clarity threshold guard against this but it is not yet scored. Rhythm accuracy against printed Omnibook rhythm is the next measure.
- Supports [ADR-0016](0016-notation-never-drops-notes.md) and [ADR-0018](0018-swing-aware-notation.md).
