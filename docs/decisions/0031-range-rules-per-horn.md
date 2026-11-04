# ADR-0031: Range rules per horn; altissimo kept, unplayable notes moved by octaves

- **Date**: 2026-11-04
- **Status**: Accepted (PR #69 merged; scorecards in, log E38)
- **Decided by**: Claude (range thread), at Austin's request
- **PR**: #69
- **Relates to**: [ADR-0005](0005-instrument-profiles-alto-first.md), [ADR-0016](0016-notation-never-drops-notes.md)

## Context
The pitch search was capped below the altissimo range (tenor 1100 Hz, alto
1600 Hz), so high notes could not be transcribed, and nothing checked whether a
note was playable. Pitch detectors also misread a low note with a weak
fundamental as its octave.

## Decision
- Keep a range table per horn (lowest key, top keyed note, top altissimo note, written pitch) and derive the concert range and pitch search limits from it. The note search (Basic Pitch) reaches written A7 on alto and tenor; the pitch line (CREPE) stops at 1600 Hz after PR #74.
- Never move a note for being high while it is within the altissimo range; tag it `altissimo`.
- Move only notes no sax can play, by octaves (or an octave and a fifth for a 3rd partial), and keep the detector's pitch as `detected_pitch`.
- Tag suspected overtones from the stem spectrum but leave them as heard by default (`--range-rules overtones` moves them).
- Never delete a note; when many notes are out of range, suspect the wrong horn and move nothing.

## Consequences
- On a synthetic phrase, altissimo notes found 15/24 → 24/24 (alto) and 12/24 → 24/24 (tenor); note F1 92.6% → 100% and 89.6% → 100% ([log E34](../evaluation/log.md)). On GRFIA altissimo-tagged takes (8 per horn) no change either way, alto 71.5% and tenor 47.6% note F1 before and after; those takes stay below written A6, so they can't show the raised ceiling. On the Omnibook (45 solos) note and onset F1 were flat; pitch accuracy fell 74.2% → 72.4% because the raised CREPE ceiling (2000 Hz) failed on three solos, not because of the rules. PR #74 caps CREPE at 1600 Hz; Basic Pitch keeps the full range ([log E37](../evaluation/log.md)). Final cards ([log E38](../evaluation/log.md)): Omnibook pitch back to 74.3% with #74; GRFIA alto note F1 75.2% → 75.1%, pitch 90.0% → 90.0%; tenor note F1 66.1% → 65.8%. A stray top overtone tagged `altissimo` on very short takes costs 0.07–0.27 points; Moving suspected overtones by default was tested ([log E39](../evaluation/log.md)): Omnibook note F1 −0.35, tenor −0.01, alto flat, and where the key could judge, the key agreed with the moved pitch 6 times and the original 129 times. Overtones therefore stay tag only by default.
- The table is per instrument, so other instruments need only the same three numbers.
- Settled (E39): suspected overtones are tagged, not moved, by default; the tag test is too loose to act on. On band records a bass note an octave below could also fake a lower fundamental.
