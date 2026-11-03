# ADR-0024: PDFs only for app runs, never in tests or scorecards

- **Date**: 2026-11-03
- **Status**: Proposed (PR #36 open)
- **Decided by**: Claude (build thread), after MuseScore pop-ups during batch runs on the Mac
- **PR**: #36
- **Refines**: [ADR-0012](0012-pdf-via-musescore.md)

## Context
Scorecard and test runs transcribe hundreds of takes. Each one launched
MuseScore to engrave a PDF, which opened windows on Austin's Mac and slowed
the runs, while no scorecard ever reads a PDF.

## Decision
Test and scorecard runs always skip PDF rendering. PDFs are made only for
user-facing runs (the app, and `transcribe` when MuseScore is set up).
MusicXML and MIDI are still written in every run.

## Consequences
- Batch runs no longer open MuseScore windows, and are faster.
- PDF engraving is no longer exercised by the scorecard, so a MuseScore
  regression shows up only in app use. The MusicXML checks (notes written,
  tuplets MuseScore accepts) still run.
