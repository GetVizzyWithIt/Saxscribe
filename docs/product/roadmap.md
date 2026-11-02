# Roadmap

Phases end when their gate is **measured and met**, not when features are
built. No dates. Status as of 2026-11-02.

## Phase 0: wiring and baseline — done

Goal: `python -m saxscribe transcribe file.wav` runs end to end, and a
baseline scorecard exists for every later phase to beat.

- [x] Four-layer pipeline, CLI, synthetic fixture tests (PR #1)
- [x] Notation: beat grid, swing, key, spelling, MusicXML concert and written (PR #2)
- [x] Scorecard with mir_eval, answer-key alignment for etudes (PR #3)
- [x] Omnibook loader on its real layout (PR #5), fixture fix (PR #7)
- [x] Answer-key sets: URMP (PR #8), ChoraleBricks and Bach10 (PR #9)
- [x] Baseline scorecards on the Mac ([evaluation log](../evaluation/log.md))

**Gate:** baseline measured. Met 2026-11-02.

## Phase 1: notes you can trust on solo sax — in progress

Goal: meet the solo targets on clean recordings. Pitch is already near target
(94–99% on solo sets); the loss is in note boundaries.

- [x] CREPE Notes style segmenter as a candidate notes tool (PR #6). Lost to
      Basic Pitch on URMP and ChoraleBricks.
- [x] Join notes Basic Pitch cuts in two, unless the audio shows a re-attack (PR #10)
- [ ] Before/after scorecard for PR #10 on URMP, Bach10, ChoraleBricks, Omnibook (running on the Mac)
- [ ] Segmenter and contour-cutter runs on the Omnibook (running on the Mac)
- [x] Omnibook grading limited to the answer key's span (PR #16); re-run: note F1 64%, onset F1 86%
- [ ] Note ends: note F1 drops ~9 points when offsets count
- [ ] Articulation tags (slur/tongued first, then scoop, fall, bend, vibrato)
- [ ] Austin's first etude takes → 20-take frozen test set
- [ ] Trained note/onset head (on Filosax when granted, Austin's takes, Omnibook train split)
- [ ] Tenor check (JazzSAMBA tenor takes, Weimar tenor solos with Austin's records)

**Gate:** solo targets (pitch 97%, onset F1 90%, note F1 80%) on Filosax test
split and on 20 of Austin's recordings.

## Phase 2: the sax out of a full band — next

Goal: full-mix targets. Currently 4–17% note F1 on ensemble mixes, because
Demucs' "other" stem carries every non-drum, non-bass, non-vocal instrument.

- [ ] Measure Demucs alternatives (BS-RoFormer, UVR community models) on
      urmp-mix, bach10-mix, omnibook-mix and JazzSAMBA stem-vs-mix pairs
- [ ] Sax-vs-rest separation fine-tune (GPU, Colab) on JazzSAMBA stems and mixes
- [ ] Fallback: instrument-conditioned transcription (MuScriptor) on the "other" stem
- [ ] Ten records Austin wants to learn as the fixed full-mix test set

**Gate:** full-mix targets, and onset F1 beats Basic Pitch on the same mixes.

## Phase 3: notation for the stand

Goal: a score Austin would put on the stand, with few edits.

- [x] PDF export via MuseScore (PR #12)
- [x] Never drop notes when the beat grid is missing; MuseScore macOS crash (PR #15)
- [ ] Triplet markings MuseScore rejects (PR #17, open)
- [ ] Notation fidelity check in the scorecard (notes written = notes detected)
- [ ] Hand-count edits per 100 notes on 10 fixed tunes
- [ ] Chord-aware spelling (Weimar chords; existing chord model for records)
- [ ] Phrase marks, meters other than 4/4, pickups
- [ ] Personal answer keys from Austin's paper transcriptions (OMR → MusicXML → align)

**Gate:** edits per 100 notes ≤5 solo, ≤15 full mix.

## Product track (UI thread)

Runs alongside the phases. Design doc: https://claude.ai/artifact/WDFJbXxU1WtLeQmSPDkKrB

1. **v1**: upload a file, get a PDF; optional scrolling play-along. iPad Safari over home Wi-Fi, served by the Mac. Built in PR #14 (`python -m saxscribe app`).
2. Viewer and looper (stacked lanes: audio, pitch line, notes, notation at the bottom).
3. Developer compare view against an answer key.
4. Editor; edits saved as diffs (training data).
5. Library and review queue.
6. Timing and intonation report for Austin's own takes.

## Later

- Any-instrument transcription: separate every instrument, one profile, answer-key set and model per instrument.
- Real-time mode (PESTO pitch tracker is the candidate).
- MIDI wind controller as a source of perfectly labelled practice data.
