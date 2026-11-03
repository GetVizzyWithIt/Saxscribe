# ADR-0023: On band records, write only where the sax plays

- **Date**: 2026-11-03
- **Status**: Accepted (PR #35 merged; 0 answer-key notes lost on the Parker band records)
- **Decided by**: Claude (routine; to be confirmed by the scorecard)
- **PR**: #35
- **Amends**: [ADR-0016](0016-notation-never-drops-notes.md)

## Context
On a band record the sax stem still carries sound when the sax lays out:
piano bleeding through during a piano solo, junk during a bass solo, drum
hits during a break. Basic Pitch turns that into notes, so Blues for Mary
Jane printed about 419 bars for a 148-bar Getz solo. ADR-0016 says the score
must write every note in `notes.json`.

## Decision
Find the stretches where the horn plays (the stem's share of the mix and how
clearly it holds one pitch, per 2 s window). Notes outside them stay in
`notes.json`, tagged `not_sax`, and are left off the score, the MIDI and the
scorecard. Only stretches of 8 s or more are cut, with 2 s given back at each
end, so phrase starts and ends are never cut. Solo takes are never cut.

## Why this keeps the fidelity rule
ADR-0016 is about never losing the sax's notes. These notes are judged not to
be the sax at all. Nothing is deleted: the note layer is untouched, the tag
says why each note is off the score, and `notation.json` indices still point
into `notes.json`.

## Consequences
- Blues for Mary Jane: the piano solo (195–294 s) and bass solo (305–368 s) are cut, about 500 non-Getz notes; Parker 7XTyc note F1 56% → 62% with the drum break removed ([log E16](../evaluation/log.md)).
- Risk: a quiet or breathy sax passage judged "not sax" would vanish from the score and from grading. Guard (added to PR #35): the cut stretches are recorded in `take.json` (notes layer, `sax_cuts`), and the scorecard counts answer-key notes inside them, per take ("N in cut stretches") and in a "Sax-span check" total line, so a cut that hides real sax shows up as a number, not silence. On the Parker band records it found 0 answer-key notes in cut stretches. One wrong 8 s cut was seen on an older take where separation put the sax in the guitar stem.
- ADR-0016's rule now reads: the score writes every note in `notes.json` except those tagged `not_sax`.
