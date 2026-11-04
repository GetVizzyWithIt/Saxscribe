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
- [x] Join notes Basic Pitch cuts in two (PR #10). Scored before/after: hurts URMP, Bach10 and ChoraleBricks by merging real repeats; off by default (PR #22). Omnibook run pending
- [ ] Split notes, second attempt: a better re-attack detector or a trained onset head
- [x] Segmenter and contour-cutter runs on the Omnibook: Basic Pitch stays best (64.2% vs 59.8% and 58.3%)
- [x] Weakest Omnibook solos: the answer keys are an octave off in long passages (log E10)
- [x] Flag octave disagreements with the key in the scorecard (PR #23)
- [x] Omnibook grading limited to the answer key's span (PR #16); re-run: note F1 64%, onset F1 86%
- [ ] Note ends: note F1 drops ~9 points when offsets count
- [ ] Articulation tags (slur/tongued first, then scoop, fall, bend, vibrato)
- [ ] Austin's first etude takes → 20-take frozen test set
- [ ] Trained note/onset head (on Filosax when granted, Austin's takes, Omnibook train split)
- [ ] Tenor check: first evidence from GRFIA-RealSax, tenor note F1 57.8% vs alto 66.5% with final answer keys (log E22); still to do on band records (JazzSAMBA tenor takes, Weimar tenor solos with Austin's records)
- [ ] Range rules per horn and altissimo up to written A7 (PR #69 merged; synthetic altissimo 15/24 → 24/24 alto, log E34). Real GRFIA altissimo scorecards pending; decide whether to move suspected overtones by default
- [ ] Trill tag, so a trilled passage reads as one written trill while every alternation stays in notes.json (GRFIA trill takes 24%, log E20)

**Gate:** solo targets (pitch 97%, onset F1 90%, note F1 80%) on Filosax test
split and on 20 of Austin's recordings.

## Phase 2: the sax out of a full band — started

Goal: full-mix targets. Currently 4–17% note F1 on ensemble mixes, because
Demucs' "other" stem carries every non-drum, non-bass, non-vocal instrument.

- [x] Pick the stem the sax actually lands in, sum when split (PR #24): 10 Parker records 50.6% → 56.4% note F1, 110 → 64 s/min
- [x] Measure Demucs alternatives: htdemucs_ft and BS-RoFormer lose to htdemucs_6s on Parker records and Blues for Mary Jane, and are 3–4× slower; keep htdemucs_6s (log E25, ADR-0027)
- [x] Two averaged Demucs shifts by default (+0.8 / +1.9 points, +50% time; PR #61, log E30)
- [ ] Onset model trained on sax, for the soft same-pitch repeats still missed since #52 (log E31)
- [ ] Sax-vs-rest separation fine-tune (GPU, Colab) on JazzSAMBA stems and mixes
- [ ] Fallback: instrument-conditioned transcription (MuScriptor) on the "other" stem
- [ ] Ten records Austin wants to learn as the fixed full-mix test set

**Gate:** full-mix targets, and onset F1 beats Basic Pitch on the same mixes.

## Phase 3: notation for the stand

Goal: a score Austin would put on the stand, with few edits.

- [x] PDF export via MuseScore (PR #12)
- [x] Never drop notes when the beat grid is missing; MuseScore macOS crash (PR #15)
- [x] Triplet markings MuseScore rejects (PR #17). PDF now complete: test Parker solo, 2 pages, all 398 notes, proper beaming and triplets
- [x] Readability pass (PR #21): swung eighths, triplets, multi-bar rests, one spelling per part (log E7)
- [x] MuseScore accepts every file: off-grid points after triplets moved to sixteenths (PR #26)
- [ ] On real recordings: too many 32nds and triplets (log E12). Cause on lone sax: the beat tracker finds too few beats; PR #29 (merged) takes the beat from the notes, Parker test solo 32nds 80 → 1 (log E13)
- [ ] Rhythm quantisation on real records: Blues for Mary Jane check shows extra triplets, sixteenths and ties, pickups early or late (log E18). Current focus
- [x] Rhythm scorecard on Weimar (PR #53): baseline exact position 58.7%, right beat 89.3% (log E24)
- [x] Ballads and slow tunes: sextuplet and 32nd grids on slow or busy beats (PR #64): ballads 17% → 36%, slow 34% → 44%, all 63% → 66% position read (log E32). Ceiling near 70% for ballads (free-time tuplets)
- [x] Choose rhythm per phrase instead of per beat: PR #66 on fast beats, up tempo 75% → 77%, all 66% → 67%, triplet over-count gone (log E33)
- [x] `position_read` measure so correct swing notation isn't counted wrong (PR #55): 63.1% on all solos, 57.6% on saxes (log E28)
- [ ] Rhythm accuracy against the Omnibook's printed rhythm, and against GRFIA audio-to-score's written scores once aligned
- [x] PDF header: artist, title and a "Transcribed with Saxscribe" line (Austin, 2026-11-03; PR #30)
- [x] Syncopations as one note instead of tied eighths (PR #32; ties 46 → 41, log E14)
- [x] Key for blues tunes (PR #34; Weimar 49% → 60%, blues 47% → 70%, log E15)
- [x] Band records: write only where the sax plays (PR #35; 0 answer-key notes lost, 7XTyc 56% → 62%, log E16). One wrong 8 s cut on an older take is being fixed
- [x] Copy finished sheet music to `~/Desktop/Saxscribe` with title and artist (PR #42)
- [ ] Remove short ghost notes without losing real ones (55 extra notes on Blues for Mary Jane, log E19)
- [ ] MusicXML title from the song metadata (was "Transcription"; fix to confirm)
- [ ] Chromatic runs: sharps going up, flats going down (PR #44, open)
- [ ] Notation fidelity check in the scorecard (notes written = notes detected)
- [ ] Hand-count edits per 100 notes on 10 fixed tunes
- [ ] Chord-aware spelling (Weimar chords; existing chord model for records)
- [ ] Phrase marks, meters other than 4/4, pickups
- [ ] Personal answer keys from Austin's paper transcriptions (OMR → MusicXML → align). First: Blues for Mary Jane (Getz, 4 pages, concert C); intro and choruses 1–2 hand-entered and scored (note F1 54%, 70% without note ends; log E19); rest waits on OMR

**Gate:** edits per 100 notes ≤5 solo, ≤15 full mix.

## Product track (UI thread)

Runs alongside the phases. Design doc: https://claude.ai/artifact/WDFJbXxU1WtLeQmSPDkKrB

1. **v1**: upload a file, get a PDF; optional scrolling play-along. iPad Safari over home Wi-Fi, served by the Mac. Built in PR #14 (`python -m saxscribe app`); PR #19 added live progress and step timers, Stop / Run again / Remove per take, and a required solo-or-band choice. PR #27: the PDF button falls back to printable pages when no PDF was made. First real test: Austin's band recording "Blues for Mary Jane".
2. Results page (PR #38): scorecard history per set over time, a marker per model change, the change-by-change table.
3. Viewer and looper (stacked lanes: audio, pitch line, notes, notation at the bottom).
4. Developer compare view against an answer key.
5. Editor; edits saved as diffs (training data).
6. Library and review queue.
7. Timing and intonation report for Austin's own takes.

## Later

- Any-instrument transcription: separate every instrument, one profile, answer-key set and model per instrument.
- Real-time mode (PESTO pitch tracker is the candidate).
- MIDI wind controller as a source of perfectly labelled practice data.
