# ADR-0032: Don't move suspected overtones; overtone check off by default

- **Date**: 2026-11-04
- **Status**: Accepted (PR #78)
- **Decided by**: Claude (range thread), from the Mac scorecards; Austin's range brief asked for overtones to be considered and for no notes to be deleted
- **PR**: #78
- **Refines**: [ADR-0031](0031-range-rules-per-horn.md)

## Context
ADR-0031 left open whether notes the stem spectrum flags as overtones (a lower
note's partials at least 0.3 as loud as the shared ones) should be moved down
to that lower note by default. Moving a real high note down would write a wrong
note, which breaks the fidelity rule ([ADR-0016](0016-notation-never-drops-notes.md)) in spirit.

## Evidence ([log E39](../evaluation/log.md))
Mac, main `4ed61f2`, default (`out`) vs `--range-rules overtones`:

| Set | Note F1 | Moved notes the key could judge: lower note / note as heard |
| --- | --- | --- |
| Omnibook (45 solos) | 64.20% → 63.85% (without offsets 78.79% → 78.30%) | 6 / 116 |
| GRFIA tenor (473 takes) | 65.84% → 65.83% | 0 / 11 |
| GRFIA alto (479 takes) | 75.10% → 75.10% | 0 / 2 |

Of the 135 flagged notes the key could judge, 6 were overtones and 129 were the note as heard.

## Decision
- Never move suspected overtones by default.
- In the default mode (`out`), don't run the overtone check and add no `overtone` tag: a tag that is wrong about 95% of the time would mislead editing and end up in edited takes saved as training data.
- Keep the check in `--range-rules overtones` (moves) and `flag` (tags) for tuning. The Omnibook solos with wrong moves (wkTyc, N3fYc, V3fYc, KRfYc) are the study set.
- Notes above the altissimo range still use the spectrum to choose between an octave and an octave-and-a-fifth move (ADR-0031).

## Consequences
- Scores are unchanged: the default never moved overtone notes, and tags are not scored.
- Real low notes read an octave high are not caught by this check for now. Revisit if a tighter test (for example the lower octave held across the whole note in the stem) beats 50% on the key.
