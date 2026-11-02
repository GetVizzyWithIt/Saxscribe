# Datasheet: URMP (University of Rochester Multi-modal Music Performance)

## Motivation
Made by Li, Liu, Dinesh, Duan and Sharma (Rochester, 2018) for audio-visual
analysis of chamber music: each part recorded separately, then mixed, with video.

## Composition
- 44 classical ensemble pieces (duets to quintets). 10 include saxophone, giving 11 sax parts.
- Per part: isolated audio (`AuSep_*.wav`), human-checked pitch line
  (`F0s_*.txt`: time, Hz) and notes (`Notes_*.txt`: onset s, Hz, duration s).
  Per piece: mix (`AuMix_*.wav`), score MIDI and PDF, video.
- Tier A: human-checked notes.
- The sax is often an inner voice next to strings, flute, clarinet or brass.

## Collection process
Musicians recorded parts one at a time to a guide, then were mixed.

## Preprocessing and labelling
Loader (`load_urmp`, PR #8) reads `Notes_*.txt`, converts Hz to concert MIDI.
The F0 file path is kept for later pitch-line scoring.

## Uses
- **Role**: `urmp` = solo test; `urmp-mix` = separation stress test (full-mix targets).
- **Do not use for**: forecasting jazz-record performance; these mixes are harder than a quartet record.

## Distribution
Dryad doi:10.5061/dryad.ng3r749, CC0, 12.1 GB. Folder `URMP/`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
2026-11-02: solo pitch 94.4%, note F1 64.4%; mix note F1 17.1%. 16_Surprise
scores 81% pitch under every tool; needs a listen. See the [log](../../evaluation/log.md).
