# Datasheet: GRFIA audio-to-score (saxophone), "GRFIA-RealSax"

Format: Gebru et al., "Datasheets for Datasets" (CACM 2021), trimmed. Written
2026-11-03 from the dataset page and the coordinator's summary; items marked
*to verify* need checking against the download.

## Motivation
Made by the GRFIA group (Pattern Recognition and Artificial Intelligence,
DLSI, University of Alicante) for audio-to-score research: going from a
recording straight to a written score. Paper and funding: *to verify*.
Pointed out by Austin on 2026-11-03. Loader added in PR #33, fixed in PR #40.

## Composition
- **One item**: a short recording of a real alto or tenor sax, with the
  written score for that take and technique tags.
- **Size**: 1,026 takes, about 3 hours.
- **Horns**: alto and tenor (split between them *to verify*).
- **Labels**: the written score (notes and rhythm as notated, not times in
  the audio), plus tags for techniques such as growl, bend, fall and vibrato.
- **What the labels are not**: the notes are **not time-aligned** to the
  audio. They say what was meant to be played, not exactly when.
- **Players and material**: one player, per the loader (`PERFORMER` column); written melodies, exercises and scales. Overlap with other sets: none known.
- **Technique tags** (columns in the index, read by the loader): altissimo, bend, breath, fall, false fingering, glissando, growl, trill, vibrato.

## Collection process
Real players recording real horns. Room, microphones and number of players:
*to verify*.

## Preprocessing and labelling
- Creators: scores are Humdrum **kern (`krn/<horn>/*.krn` or `.skm`), audio in `real/<horn>/*.wav`, plus an index with tempo, performer and tags.
- Pitch: the kern files sit an octave above concert pitch for both horns (checked on real takes); the loader subtracts 12.
- Saxscribe (`score/kern.py`, `score/refs.py: load_grfia`, PR #33): reads the kern (ties joined, chords to top note, grace notes skipped), lines each score up with its take using the etude aligner (`score/align.py`: chroma DTW, then onsets snapped to heard attacks), and caches the key as JSON under `~/saxscribe-runs/keys/grfia-<horn>/`.
- Takes whose length is outside 0.8–1.6× the score's length at its tempo (count-ins, repeats) are skipped and logged. Since PR #40, zero-length notes are dropped from keys and a take that can't be scored no longer stops the run.
- The aligned keys are machine-made and not yet spot-checked: tier B.

## Uses
- **Scorecard sets**: `grfia-alto`, `grfia-tenor` (PR #33).
- **Role in Saxscribe**:
  - **Notation answer key** (Phase 3): the written score is exactly the
    target for "notes to readable sheet music", including rhythm. This is the
    first set that can measure rhythm accuracy, not only note timing.
  - **Note-level test or training** once aligned (tier B after alignment and
    spot-checks; the raw score alone is not graded against at note level).
  - **Technique tags** (tier C): first labelled real-sax examples for
    articulation tags (growl, bend, fall, vibrato).
  - **Tenor check**: a source of real tenor takes.
- **Split**: by tune, as everywhere ([data/README.md](../README.md#splits-and-leakage)).
- **Do not use for**: anything commercial (licence); grading note timing
  before alignment.

## Distribution
- Page: https://grfia.dlsi.ua.es/audio-to-score/
- Licence: non-commercial (exact terms *to verify*). Fine for a single-user
  tool; weights trained on it stay private.
- Access: open download. The datasets thread is downloading it to the Mac
  under `~/mir_datasets/` (folder name and manifest entry *to verify*).

## Maintenance
Version, md5 and folder recorded in `datasets/manifest.json` once downloaded.

## Saxscribe results
- Preliminary (2026-11-03): first 10 alto takes, pitch 80% correct with no octave errors ([log E17](../../evaluation/log.md)). Full run over about 1,000 takes in progress.
