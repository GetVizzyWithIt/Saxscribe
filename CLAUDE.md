# Sax Transcription Tool (saxscribe)

## What this project is
A tool that transcribes saxophone performances to notes and readable
notation, for one user: Austin, a saxophone player on an Apple Silicon Mac
(M3 Pro). Two uses: review his own recordings, and learn other players' solos
from full-band recordings. The requirements doc ("Sax Transcription Tool —
Requirements and Project Instructions") is the source of truth; ask for it if
it is not attached. Alto first; check transfer to tenor once alto works.

## How to work
- Build in small, runnable steps. Every pull request leaves the CLI working:
  `python -m saxscribe transcribe file.wav` runs end to end.
- Measure before and after any model change. Report onset F1, note F1 and
  pitch accuracy with mir_eval on the fixed test set. A change with no
  scorecard is not done.
- Reuse before building. Start from Demucs, CREPE/torchcrepe, Basic Pitch,
  Beat This! and music21. Build only the pieces nothing provides: note
  segmentation under slurs, articulation tags, swing quantization, the editor.
- Keep the four layers separate on disk: stem, pitch contour, note events,
  notation. Never discard a lower layer to produce a higher one.
- Fidelity over playability. This tool is the opposite of the Songs in the Key
  of Life chart model: it must not learn to omit notes. If a shortcut from the
  game would do that, say so and don't take it.
- Separate from the game. `saxscribe/frontend.py` is a private copy of the
  game analyzer's front end. Never import from the game repo, and never bring
  over anything from its chart model.
- Explain choices in plain language. Austin is a strong analyst and a
  musician, not an ML researcher. Name the model and the metric, say what it
  does, skip the jargon.
- Mac first. Inference runs locally on MPS or Core ML. Anything that needs a
  real GPU goes in a Colab notebook with the weights brought back.
- Record every take and every edit. Edited transcriptions are training data;
  store them with the original model output as a diff.

## Conventions
- Python 3.11, same venv layout as the game analyzer (own environment, see
  setup_mac.sh). Add dependencies to requirements.txt with a one-line reason.
- Concert pitch stored; display transposed (E-flat or B-flat) on request.
- Tests for every layer on the 10-second synthetic fixture (tests/fixture.py).
  Run `python -m pytest` before opening a PR.
- Branches named claude/..., one PR per change, with the scorecard in the PR
  description.
- No audio files or datasets in the repo. Paths to them live in a local
  config (config.local.*, ignored by git).

## When unsure
Draft the smallest version, run it on the fixture, and show the result. Ask
one question at a time. Prefer a working rough cut to a plan.
