# ADR-0007: Pair Omnibook stems with performance-aligned MIDI by ID

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Claude (bug fix)
- **PR**: #5

## Context
The first loader matched files by loose names and paired full records with
`midi_original` (the score's timing, not the performance).

## Decision
Pair `audio_stems/<id>.wav` with `midi_performance_aligned/<id>-fine-aligned.mid`
by ID; skip the 4 solos with no aligned MIDI; `omnibook-mix` uses the records.

## Consequences
46 of 50 solos are scored. Loaders for new sets are checked against real files
on the Mac before their scorecard counts.
