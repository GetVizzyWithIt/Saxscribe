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
- The aligned keys are machine-made and not yet spot-checked: tier B. Known issue: on short, repetitive exercises (scales, patterns) the alignment can slip by a repeat; these are the worst-scoring takes (E20). Metronome takes are aligned on the beat since PR #46; PR #47 picks per take between the beat and the older alignment by pitch agreement.
- Labelling convention: a trill is written as one note in the score, so a transcription that writes every alternation scores low on trill takes. Score trill takes separately or by tag.

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
- 2026-11-03, full run (about 950 takes, provisional until alignment slips on short repetitive exercises are fixed) ([log E20](../../evaluation/log.md)):
  - Alto: pitch 84%, onset recall 71%, note F1 58% (71% without offsets). Tenor: pitch 85%, onset recall 68%, note F1 54% (67% without offsets). Octave errors 0.1% on both.
- After PR #46 re-aligned the metronome takes on the beat ([log E21](../../evaluation/log.md)): alto 65%, tenor 53%; one-pitch drills 25% → 79% alto, 35% → 79% tenor. 14 alto and 14 tenor scale takes now slip by one step; PR #47 picks the better alignment per take (expected ~70% alto, ~62% tenor). These are answer-key changes, not transcription changes.
  - Trill takes: note F1 24% (score writes one trilled note; we write each alternation). Bends and falls: alto pitch 71–78%. Vibrato: no effect.
- Superseded: the 10-take preliminary (pitch 80%, E17).
