# ADR-0031: Range rules per horn; altissimo kept, unplayable notes moved by octaves

- **Date**: 2026-11-04
- **Status**: Proposed (PR #69 open; real scorecards pending)
- **Decided by**: Claude (range thread), at Austin's request
- **PR**: #69
- **Relates to**: [ADR-0005](0005-instrument-profiles-alto-first.md), [ADR-0016](0016-notation-never-drops-notes.md)

## Context
The pitch search was capped below the altissimo range (tenor 1100 Hz, alto
1600 Hz), so high notes could not be transcribed, and nothing checked whether a
note was playable. Pitch detectors also misread a low note with a weak
fundamental as its octave.

## Decision
- Keep a range table per horn (lowest key, top keyed note, top altissimo note, written pitch) and derive the concert range and pitch search limits from it. The search now reaches written A7 on alto and tenor (CREPE's own limit is 2000 Hz).
- Never move a note for being high while it is within the altissimo range; tag it `altissimo`.
- Move only notes no sax can play, by octaves (or an octave and a fifth for a 3rd partial), and keep the detector's pitch as `detected_pitch`.
- Tag suspected overtones from the stem spectrum but leave them as heard by default (`--range-rules overtones` moves them).
- Never delete a note; when many notes are out of range, suspect the wrong horn and move nothing.

## Consequences
- On a synthetic phrase, altissimo notes found 15/24 → 24/24 (alto) and 12/24 → 24/24 (tenor); note F1 92.6% → 100% and 89.6% → 100% ([log E34](../evaluation/log.md)). Real scorecards pending.
- The table is per instrument, so other instruments need only the same three numbers.
- Open: whether to move suspected overtones by default; on band records a bass note an octave below could fake a lower fundamental.
