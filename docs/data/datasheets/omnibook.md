# Datasheet: Charlie Parker Aligned Omnibook

## Motivation
Made by Riley and Dixon (Queen Mary University of London, 2025) to give
jazz-solo transcription research real performances with note-level answer
keys: the solos in the Charlie Parker Omnibook lined up with the recordings
they were transcribed from.

## Composition
- 50 Charlie Parker alto solos. Per solo: sax stems separated from the record,
  the full record, the Omnibook score (MusicXML and MIDI), MIDI aligned to the
  performance, and downbeats.
- 46 of the 50 have performance-aligned MIDI; the other 4 are skipped.
- One player, one horn (alto), bebop era recordings, mono or early stereo.
- Labels: the published transcription, warped onto the performance. Tier B:
  aligned, then refined (`*-fine-aligned.mid`); not every note is human-checked
  against the audio, and the Omnibook itself has editorial choices (it is a
  transcription, not a recording log).

## Collection process
Commercial Parker recordings; stems separated by the dataset authors.

## Preprocessing and labelling
Saxscribe's loader (`score/refs.py: load_omnibook`, PR #5) pairs
`audio_stems/<id>.wav` with `midi_performance_aligned/<id>-fine-aligned.mid`
by ID. An earlier version wrongly paired records with `midi_original` (the
score timing), which is why the loader matches by ID now. `omnibook-mix` uses
the full records and runs them through Demucs first.

## Uses
- **Role**: main jazz test set (`omnibook`, `omnibook-mix`); notation check
  against an expert transcription; alto training data in Phase 1 (train split only).
- The stems already come from a separator, so `omnibook` is held to the
  full-mix targets, not the solo ones.
- **Do not use for**: claims about Austin's own tone; solo-recording targets.

## Distribution
Zenodo record 14628467, open, CC BY 4.0, 1.35 GB. Folder `CharlieParkerOmnibook/`.

## Maintenance
Checksums in `datasets/manifest.json`. Note: the manifest's description says
"no isolated stems", which conflicts with the `audio_stems/` folder the loader
reads; to be corrected.

## Known issue
Each performance-aligned MIDI covers roughly one chorus of the solo, while the stem runs longer. Until PR #16, notes after the key ended counted as wrong, understating every Omnibook score. Grade only inside the key's time span.

## Saxscribe results
2026-11-02 default tools: pitch 73.3%, onset F1 60.4%, note F1 45.0%; Basic
Pitch writes 1.5–3.2× too many notes (both understated, see Known issue; re-run pending). Segmenter, contour and mix runs pending.
See the [log](../../evaluation/log.md).
