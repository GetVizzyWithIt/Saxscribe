# ADR-0036: Gated two-separator hybrid on band records; genre only a hint

- **Date**: 2026-11-05
- **Status**: Proposed (agreed direction; the hybrid test is running in the build thread)
- **Decided by**: Austin with Claude (2026-11-05, 05:06–05:09 UTC)
- **Relates to**: [ADR-0016](0016-notation-never-drops-notes.md), [ADR-0028](0028-two-demucs-shifts-by-default.md), [ADR-0034](0034-hide-notes-the-pitch-line-does-not-back.md)

## Context
Sax-specific separators are cleaner than Demucs on band records but sometimes lose real sax passages. The local Mega 53-stem model and the MVSep website model reached Pennies From Heaven 57.2% / 58.1% and Parker 60.4% / 61.0%, against Demucs's 49.2% and 57.8%. But they lost parts of Parker solos (6Cbwc, BRfYc) and scored lower on Blues for Mary Jane ([log E51, E52](../evaluation/log.md)). Austin asked whether separation could work in stages, gated on how certain each part is.

## Decision
On band records, decide phrase by phrase:
1. Run a sax-specific separator and Demucs side by side.
2. Where both hear a sax line, use the cleaner sax-specific stem.
3. Where the sax stem goes quiet but Demucs's pitch line still hears a sax-like line, fall back to Demucs for that stretch, so real playing is never lost.
4. Where the signals disagree, tag the notes "check me" for the editor rather than hiding or deleting them.

**Genre stays a hint only.** It never decides what is sax, because the sax sounds much the same across styles and a genre guess could talk the tool out of a real note. Revisit only if the "check me" cases cluster by style. Austin agreed on 2026-11-05.

## Consequences
- Each stage is judged with the band-record measures Sax found (recall) and Sax purity (precision) (PR #90), as well as note F1, and must not lose solo passages.
- Separation time roughly doubles on band records (two separators).
- Thresholds for steps 3 and 4 are tuned on the test sets; this ADR is updated with the numbers when the build thread settles them.
