# ADR-0003: Store concert pitch, transpose only for display

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: requirements doc; Austin (alto default, tenor switch)
- **PR**: #2

## Context
Austin plays alto (Eb) and tenor (Bb); answer keys come in both sounding
pitch (ChoraleBricks `pitch`) and written pitch (etudes, his printed transcriptions).

## Decision
Every layer stores concert (sounding) pitch. Written parts are produced at the
notation step (`score-<horn>.musicxml`, `score-<horn>.pdf`). Inputs in written
pitch are converted on the way in (`answer-key --score-pitch written`, the default).

## Consequences
- One source of truth for scoring; transposition bugs can only affect display.
- Every scanned transcription must record its horn.
