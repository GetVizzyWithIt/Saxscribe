# Datasheet: ChoraleBricks

## Motivation
Made by AudioLabs Erlangen as a modular set of chorale recordings, each part
recorded alone, for source separation and transcription research.

## Composition
- 10 chorales, parts recorded on many instruments (flute, oboe, clarinet,
  trumpet, brass, sax). Saxophone: 20 alto (`*_as.wav`) and 18 baritone
  (`*_bs.wav`) tracks.
- Per track: human-checked notes CSV (start, end, sounding MIDI pitch, cents,
  plus `pitch_written`), f0 CSV, score alignments, MIDI/MusicXML/MEI.
- Tier A.

## Collection process
Real players, each part recorded on its own.

## Preprocessing and labelling
Loader (`load_choralebricks`, PR #9) grades against the `pitch` column
(sounding pitch), never `pitch_written`. Each answer key carries its horn, so
baritone parts get the baritone's range.

## Uses
- **Role**: `choralebricks` = solo test, alto and baritone.
- Could later yield synthetic ensemble mixes (mix sax with other parts) for separation training.

## Distribution
Zenodo 20849469, open, CC BY 4.0, 1.16 GB. Folder `ChoraleBricks/`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
2026-11-02: pitch 98.9%, onset F1 86.7%, note F1 77.8% (segmenter 60.3%).
Upper alto parts 86–96% note F1; inner alto parts 53–74%. See the [log](../../evaluation/log.md).
