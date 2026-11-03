# Product requirements: Saxscribe

| | |
| --- | --- |
| Owner | Austin (sole user) |
| Status | Phase 0 done, Phase 1 in progress |
| Source of truth | "Sax Transcription Tool — Requirements and Project Instructions" (2 Nov 2026). This page restates it in testable form and records changes since. |
| Last updated | 2026-11-02 |

## 1. Problem

A sax player who wants to know exactly what was played (on their own take or on
a record) has two options today: transcribe by ear with a pencil, or use a
general-purpose transcription tool that is built for piano and guitar and gets
sax wrong. Saxscribe should be good enough that Austin reaches for it before
his ear, and should get better from his corrections.

## 2. Users and use cases

One user: Austin, who plays alto and tenor, works on an M3 Pro MacBook and
practises from an iPad on the music stand.

| # | Use case | Input | Output | Main difficulty | Priority |
| --- | --- | --- | --- | --- | --- |
| U1 | Review my own playing | Phone or interface recording, alone or over a backing track | Notation plus a timing and intonation report | Cutting notes correctly under slurs and vibrato | First built (cleanest data) |
| U2 | Learn someone else's solo | Commercial record or live bootleg with a band | Lead-sheet style transcription with the audio aligned for looping | Isolating the sax from piano, guitar and other horns | The long-wanted one |
| U3 | Practice feedback over time | Many takes of one tune or exercise | Same pipeline, repeated; edits kept as the answer key | Consistency across sessions | Later |

## 3. Scope

### Goals (from the requirements doc)

| ID | Goal | How it is checked |
| --- | --- | --- |
| G1 | Solo recording to notes with ≥90% onset F1 and ≥95% pitch accuracy on Austin's playing | Scorecard on Filosax test split and on 20 of Austin's frozen takes |
| G2 | Sax inside a full-band mix, good enough that fixing is faster than transcribing by ear | Full-mix scorecard targets; edits per 100 notes |
| G3 | Keep detail notation loses: bends, scoops, falls, vibrato, growl, timing against the beat | Contour layer kept; articulation tags in notes.json (not built yet) |
| G4 | Readable notation: key, enharmonics, swing-aware rhythm, sensible rests and phrasing | Edits per 100 notes, hand-counted on 10 fixed tunes |
| G5 | All inference on the Mac | Speed target measured on the M3 Pro |
| G6 | Improve from corrections | Every edit stored as a diff against model output |

### Non-goals (for now)

- Polyphonic instruments (piano, guitar chords).
- Real-time transcription while playing.
- Automatic chord symbols (may use an existing chord model for spelling).
- A public product. Single user, so non-commercial model weights are acceptable.

### Scope changes since the requirements doc

| Date | Change | Decided by | Record |
| --- | --- | --- | --- |
| 2026-11-02 | Separate repo; the game's front end is copied, not shared as a package | Austin | [ADR-0001](../decisions/0001-separate-repo-copied-front-end.md) |
| 2026-11-02 | Alto first, tenor a first-class switch (Austin plays both) | Austin | [ADR-0005](../decisions/0005-instrument-profiles-alto-first.md) |
| 2026-11-02 | Long term: any instrument (separate every instrument, transcribe each with its own model). Sax first | Austin | [ADR-0005](../decisions/0005-instrument-profiles-alto-first.md) |
| 2026-11-02 | Work with the data already on the Mac; Filosax and MedleyDB become later training rounds | Austin | [ADR-0009](../decisions/0009-proceed-without-filosax.md) |
| 2026-11-02 | v1 UI = upload audio, download PDF sheet music, optional scrolling play-along. No mic input or practice feedback yet | Austin | [ADR-0013](../decisions/0013-v1-ui-scope.md) |
| 2026-11-02 | Austin's own paper transcriptions (alto and tenor) become personal answer keys via OMR | Austin | [ADR-0014](../decisions/0014-personal-answer-keys-from-paper.md) |

## 4. Functional requirements

Status key: **Done** = merged and tested; **Partial** = works but incomplete;
**Planned** = not started.

| ID | Requirement | Status | Where |
| --- | --- | --- | --- |
| F1 | **Isolate**: any audio in; sax stem plus accompaniment out; pass-through for solo takes; all stems kept to audition and pick | Done | `layers/isolate.py` |
| F2 | **Pitch contour**: f0 at 100 Hz or finer with per-frame confidence; never discarded | Done (100 Hz) | `layers/contour.py` |
| F3 | **Note events**: onset, offset, MIDI pitch, cents deviation | Done | `layers/notes.py` |
| F3a | Articulation tags: slur, tongued, scoop, fall, bend, vibrato depth/rate, growl | Planned (field exists, empty) | `notes.json` `tags` |
| F3b | Beats, downbeats, tempo | Done | Beat This!, librosa fallback |
| F3c | Key | Partial: found at notation step by music21, not stored in notes.json | `layers/notation.py` |
| F4 | **Notation**: quantized to beat grid, swing setting, key-driven spelling, rests | Done (4/4 only; no chord-aware spelling; no phrase marks). Fixed in PR #15: never drops notes without a beat grid. Readability pass merged (PR #21): swung eighths, triplets, multi-bar rests, one spelling per part; checked on synthetic solos so far | `layers/notation.py` |
| F4a | Export MusicXML and MIDI, audio kept aligned | Done | `score.musicxml`, `score.mid` |
| F4b | Export PDF sheet music (v1 UI) | Done when MuseScore is installed | `layers/engrave.py` |
| F5 | Transposition: store concert pitch, display Eb or Bb | Done (alto, tenor, baritone) | `horns.py` |
| F6 | Batch mode (folder in, transcriptions out) | Done | `transcribe <folder>` |
| F7 | Editor: fix pitch, split/merge, nudge onsets, change articulation, re-quantize; every edit saved as a diff | Planned (UI thread) | design doc |
| F8 | Loop practice: select bars, slow down with pitch kept, scrolling notation | Partial: v1 play-along with highlighting, tap-to-seek, 50% slow-down with pitch kept, stem toggle (PR #14); bar loops not yet | `python -m saxscribe app` |
| F13 | v1 web app: upload (alto/tenor, solo/band), download PDF/MusicXML/MIDI at alto, tenor or concert | Done (PR #14; progress, Stop/Run again and required solo-or-band choice in PR #19) | `python -m saxscribe app` |
| F9 | Performance report: per-note timing and intonation, per-take summary | Planned (Phase D in UI plan) | |
| F10 | Scorecard: score any layer on answer-key sets with mir_eval | Done | `score/` |
| F11 | Answer keys from a written score and a take (DTW alignment) | Done | `score/align.py` |
| F12 | Rebuild the dataset folder on any machine from a manifest | Done | `datasets.py` |

## 5. Quality requirements (v1 targets)

All scored with mir_eval; see [evaluation/protocol.md](../evaluation/protocol.md).

| Layer | Metric | Solo target | Full-mix target |
| --- | --- | --- | --- |
| Pitch contour | Raw pitch accuracy (±50 cents) on voiced frames | 97% | 90% |
| Note events | Onset F1 (±50 ms) | 90% | 75% |
| Note events | Note F1 (onset ±50 ms, pitch ±50 cents, offset 20% of duration) | 80% | 60% |
| Beats | Beat F1 (±70 ms) | 95% | 95% |
| Notation | Edits per 100 notes to an accepted score, hand-counted on 10 tunes | 5 | 15 |
| Speed | Seconds of compute per minute of audio, M3 Pro | 15 | 60 |

**v1 release gates** (both must hold):
1. Solo targets met on Filosax's test split *and* on 20 of Austin's own recordings.
2. Full-mix onset F1 beats Basic Pitch alone on the same mixes.

Filosax access is still pending, so gate 1 currently cannot be measured; see
[ADR-0009](../decisions/0009-proceed-without-filosax.md).

## 6. Constraints

- **Fidelity over playability.** The tool must never learn to drop notes to
  make a part easier. This is the line between Saxscribe and Songs in the Key
  of Life's chart model ([ADR-0001](../decisions/0001-separate-repo-copied-front-end.md)).
- **Mac-first inference** on MPS or Core ML; GPU training happens in Colab or a
  rented GPU, with weights brought back.
- **No audio or datasets in the repo**; paths live in `config.local.*`.
- **Python 3.11**, own virtual environment.
- **Licensing**: single user, so non-commercial weights are fine; GPL code is
  not copied into the repo ([ADR-0006](../decisions/0006-own-crepe-notes-implementation.md)).

## 7. Risks

| Risk | Likelihood | Current evidence | Fallback |
| --- | --- | --- | --- |
| No separator isolates sax well from a full mix | High | Mix sets score 4–17% note F1 (2026-11-02) | Instrument-conditioned transcription of the "other" stem (MuScriptor); prefer recordings where sax is prominent; sax-vs-rest separation fine-tune |
| Filosax access or terms block training | Medium | Access requested, not granted | Train on Austin's recordings plus augmentation; Filosax as test only |
| Articulation labels too subjective | Medium | Not started | Show articulation as a view of the contour rather than a prediction |
| Swing quantization unreadable | Medium | Swing auto-detect built; not yet hand-checked | Per-tune swing setting; raw timing as a second layer |
| Objectives drift toward the game's | Medium | Separate repos, separate scorecards | Keep the boundary in code review |
| Mac too slow to fine-tune | High | Not yet tried | Rented GPU per experiment; keep fine-tunes under 2 hours |
| Answer keys themselves are wrong (alignment, machine-made MIDI) | Medium | JazzSAMBA sax MIDI is machine-made | Grade only against human-checked notes ([ADR-0008](../decisions/0008-grade-only-against-human-checked-notes.md)) |

## 8. Open questions

- Is a MIDI wind controller available now or later? (Would make every
  practice session perfectly labelled.)
- Which ten records make the fixed full-mix test set? First candidate: Stan
  Getz, "Pennies from Heaven", with Austin's own printed transcription.
- When will Austin record the first alto etude takes (the start of the 20-take
  frozen test set)?
