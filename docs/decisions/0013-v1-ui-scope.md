# ADR-0013: v1 = upload audio, download PDF, optional play-along; local web app for iPad

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Austin

## Context
The requirements describe an editor, looper and performance report. Austin
wants to prove transcription quality first.

## Decision
- v1: upload an audio file, get a downloadable PDF of the sheet music, plus an optional scrolling play-along view.
- No microphone input or practice feedback yet (liked for later).
- A local web app served by the Mac, used mostly on iPad Safari over home Wi-Fi: touch-first, QR code to open, a practice layout for the music stand.
- Layout: stacked lanes on one timeline, notation at the bottom; alto (Eb) by default with a toolbar switch to tenor (Bb) and concert.
- First tune: Stan Getz, "Pennies from Heaven". Design doc: https://claude.ai/artifact/WDFJbXxU1WtLeQmSPDkKrB

## Consequences
- Resolves the requirements' open question "web editor or Godot editor": web.
- The editor (edits as diffs = training data) follows after v1.
