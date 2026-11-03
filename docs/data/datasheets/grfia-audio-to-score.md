# Datasheet: GRFIA audio-to-score (saxophone)

Format: Gebru et al., "Datasheets for Datasets" (CACM 2021), trimmed. Written
2026-11-03 from the dataset page and the coordinator's summary; items marked
*to verify* need checking against the download.

## Motivation
Made by the GRFIA group (Pattern Recognition and Artificial Intelligence,
DLSI, University of Alicante) for audio-to-score research: going from a
recording straight to a written score. Paper and funding: *to verify*.
Pointed out by Austin on 2026-11-03.

## Composition
- **One item**: a short recording of a real alto or tenor sax, with the
  written score for that take and technique tags.
- **Size**: 1,026 takes, about 3 hours.
- **Horns**: alto and tenor (split between them *to verify*).
- **Labels**: the written score (notes and rhythm as notated, not times in
  the audio), plus tags for techniques such as growl, bend, fall and vibrato.
- **What the labels are not**: the notes are **not time-aligned** to the
  audio. They say what was meant to be played, not exactly when.
- **Players, style, overlap with other sets**: *to verify*.

## Collection process
Real players recording real horns. Room, microphones and number of players:
*to verify*.

## Preprocessing and labelling
- Creators: score format (MusicXML, kern or other) *to verify*.
- Saxscribe: none yet. Before it can grade anything, each score has to be
  aligned to its take with the etude aligner (`score/align.py`, DTW, as for
  Austin's etudes), then spot-checked.

## Uses
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
None yet.
