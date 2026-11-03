# Upstream model review: what the makers of our models say

- **Date**: 2026-11-03
- **Scope**: every third-party model Saxscribe runs (Demucs, CREPE via
  torchcrepe, Basic Pitch, Beat This!) and the other libraries in
  `requirements.txt`, read against their own READMEs, licences, source code and
  papers. Our own [model cards](README.md) say how each model does on our test
  sets; this page says what the upstream authors document, where that
  disagrees with our cards, and which settings or replacements to try next.
- **Sources read**: the projects' current GitHub repos (cloned 2026-11-03:
  `adefossez/demucs` at v4.1.0, `facebookresearch/demucs`, `marl/crepe`,
  `maxrmorrison/torchcrepe`, `spotify/basic-pitch`, `CPJKU/beat_this` v1.1.0,
  `CPJKU/beat_this_annotations`, `ZFTurbo/Music-Source-Separation-Training`),
  PyPI release lists, and the repos of the alternatives named below.
  Statements marked *to verify* come from memory of a paper, not from a file
  read today.

## The short version

1. **Three of our test sets overlap the models' training data.** CREPE was
   trained on Bach10 (including its sax part) and MedleyDB; Basic Pitch on
   MedleyDB-Pitch; Beat This! on Filosax and JAAH. So our Bach10 pitch score
   (96.9%) is on audio CREPE has already seen, and Filosax or MedleyDB-Pitch,
   once we have them, would be unfair tests for those models. GRFIA,
   ChoraleBricks, URMP, the Omnibook and Austin's own answer keys are not in any
   training list we found, so they are the fair ones.
2. **CREPE's default smoothing draws a fake slide on every wide leap.**
   torchcrepe's Viterbi step (on by default; we don't change it) only lets the
   pitch move 2.2 semitones per 10 ms frame. An octave leap becomes a 50 ms
   ramp through five wrong pitches; a fourth, 20 ms. Checked with the exact
   transition table from torchcrepe's source (below). This costs pitch
   accuracy right after leaps, can make the `segment` and `contour` tools cut
   extra notes on the ramp, and makes a wrong octave "sticky" once entered.
   Half-step and whole-step trills pass through untouched, so CREPE is not
   why trills score low.
3. **Two Basic Pitch steps we leave on are likely makers of extra and split
   notes.** `infer_onsets` adds a note start wherever loudness jumps (vibrato
   swells, growl, a push on a long note), and `melodia_trick` builds notes out
   of leftover energy that had no attack. Both are on by default and
   `predict()` doesn't expose `infer_onsets`. We also run with a 50 ms shortest
   note where Basic Pitch's default is 127.7 ms. All three can be tested
   without running the network again (see "Settings to test").
4. **The Demucs six-stem weights are probably non-commercial.** The Demucs
   author now writes that `htdemucs_6s` "was trained only on Meta internal
   dataset, which likely means CC-NC-BY license is applicable". Our card says
   "MIT (code and weights)" and "MUSDB18-HQ plus an internal set". Fine for
   Austin's personal use; a blocker if Saxscribe were ever sold. Demucs is
   also no longer actively developed (the author says only "important bug
   fixes" will be made).
5. **Versions drift.** Three dependencies have moved a major or minor version
   since we wrote `requirements.txt` (Demucs 4.1.0, librosa 1.0.0, Beat This!
   1.1.0 on PyPI), and Beat This! is installed from the tip of its git repo with
   no pin. A fresh install on the Mac today would not match the one that
   produced our scorecards, and `take.json` doesn't record package versions.

What to try first, in order (details at the end): Basic Pitch decoding
settings, then an onset-timing bias check on runs we already have, then a
wider CREPE decoder, then SwiftF0 as a second pitch tracker, then a separator
bake-off. Fine-tuning Basic Pitch on GRFIA is the bigger step after those.

## At a glance

| Model | We ask for | Latest | Licence (code / weights) | OK for us? | Trained on sax? |
| --- | --- | --- | --- | --- | --- |
| Demucs `htdemucs_6s` | `demucs>=4.0.1` | 4.1.0 (2026-07-11) | MIT / unclear, "likely CC BY-NC" | Yes, personal non-commercial use | No sax target; sax ends up in "other" or "guitar" |
| CREPE "full" via torchcrepe | `torchcrepe>=0.0.22` | 0.0.24 | MIT / MIT | Yes | Some: Bach10 sax, MedleyDB, NSynth reeds |
| Basic Pitch (ICASSP 2022 model) | `basic-pitch>=0.4` | 0.4.0 (repo last commit 2025-11) | Apache 2.0 / Apache 2.0 | Yes | Little: MedleyDB-Pitch and Slakh's synthesised horns |
| Beat This! `final0` | git main, unpinned | 1.1.0 (2026-04-14, now on PyPI) | MIT / MIT | Yes | Filosax (sax over backing tracks) and JAAH (jazz) are in its training data |

Other libraries in `requirements.txt` and their licences: librosa (ISC; pYIN
fallback, onset strength, beat fallback), music21 (BSD-3), verovio (LGPL-3,
used as a library, fine), mir_eval (MIT), mido (MIT), mirdata (BSD-3; imported
for Filosax but not listed in `requirements.txt`). MuseScore (GPL-3) runs as a
separate program, which the GPL allows. None limits a personal tool.

## Test sets that the models have already seen

| Our set | CREPE | Basic Pitch | Beat This! | Effect on our numbers |
| --- | --- | --- | --- | --- |
| Bach10 | **trained on it** | no | no | Bach10 pitch accuracy (96.9%) is a "seen" score; note F1 is fair for Basic Pitch |
| MedleyDB-Pitch (pending) | **trained on MedleyDB** | **trained on it** | no | Don't use as a test set for either; fine as fine-tuning data |
| Filosax (pending) | no | no | **`final0` trained on it** | A Filosax beat F1 with `final0` would flatter it. Beat This! ships `single_final*` and `fold*` checkpoints for fair tests on its own training sets |
| GRFIA, ChoraleBricks, URMP, Omnibook, Austin's keys | not listed | not listed | not listed | Fair |

Sources: CREPE README ("The provided model is trained using ... MIR-1K,
Bach10, RWC-Synth, MedleyDB, MDB-STEM-Synth, NSynth"); Basic Pitch training
scripts (`basic_pitch/data/datasets/`: GuitarSet, iKala, MAESTRO,
MedleyDB-Pitch, Slakh); Beat This! README ("trained on all data except the
GTZAN dataset") and its annotations repo (asap, ballroom, beatles, candombe,
filosax, groove_midi, gtzan, guitarset, hainsworth, harmonix, hjdb, jaah, rwc,
simac, smc, tapcorrect). Beat This!'s README itself warns that "results may be
unfairly good if you run inference on any file from the training datasets".

## Demucs (Layer 1, `--mix` only)

**What the authors say**
- Hybrid Transformer Demucs v4. The four-stem models were trained on MUSDB
  HQ plus 800 extra songs. The six-stem `htdemucs_6s` "was trained only on
  Meta internal dataset" (licence section of the README).
- `htdemucs_6s` is "experimental": "okay quality for guitar, but a lot of
  bleeding and artifacts for the piano source". There is no wind, brass or
  sax stem in any Demucs model.
- `htdemucs_ft` (four stems, each fine-tuned) is the better-quality model,
  about four times slower.
- `--shifts N` averages N shifted passes and improves quality at N times the
  cost ("don't use it unless you have a GPU"; MPS counts). `--overlap 0.25`
  default "is probably fine". Transformer models cap the segment at 7.8 s.
- The original Meta repo is unmaintained; the author's fork
  (`adefossez/demucs`) is "officially maintained" but gets only important
  fixes.
- **Version 4.1.0 (2026-07-11)** drops torchaudio from inference (audio goes
  through `sphn` or ffmpeg) and hosts weights on Hugging Face. Our
  `torch<2.9` / `torchaudio<2.9` cap exists because Demucs 4.0.1 saved audio
  through torchaudio. With 4.1.0 that reason goes away, but 4.1.0 also changes
  how audio is read and written, so it is a change to score, not a free
  upgrade.

**How we call it**: `python -m demucs -n htdemucs_6s -d mps|cpu`, defaults
otherwise (shifts 1, overlap 0.25), then our own stem pick and sax-span cut.

**Where it disagrees with our card** ([demucs.md](demucs.md)): weights licence
(card: MIT) and training data (card: MUSDB18-HQ plus internal; the six-stem
model is internal data only).

**Relevant to sax and jazz**: no sax target, so in a quartet the sax shares
"other" with anything that isn't drums, bass, vocals, guitar or piano, and the
weak piano stem means piano bleeds into "other". That matches what we saw
(sax sometimes lands in "guitar"; our stem pick and sax-span guard work around
it).

**Alternatives**
- `htdemucs_ft` "other" stem: same family, higher quality, no piano or guitar
  stem (so piano stays in "other"). Cheap to test; MIT code, weights trained
  on MUSDB plus extra songs (research-use licence questions as above).
- BS-RoFormer, Mel-RoFormer and SCNet models from
  ZFTurbo/Music-Source-Separation-Training (MIT code). On the same benchmark
  (MVSep's Multisong set) their table gives the "other" stem 5.7–5.9 dB for
  HTDemucs and 6.5–6.9 dB for the best SCNet and BS-RoFormer models. Higher is
  cleaner; about 1 dB is a clearly audible step. Weights licences vary model by model and
  mostly inherit MUSDB's research-only terms; none of the public checkpoints
  has a sax stem.
- Hosted services (for example MVSep) list instrument-specific models, but the
  weights aren't public and the audio would leave the Mac. Not without
  Austin's OK.
- The bigger win is still the one on our roadmap: a sax-vs-rest fine-tune,
  which the MSST training code supports.

## CREPE via torchcrepe (Layer 2)

**What the authors say**
- CREPE: a network that reads 1024-sample windows of 16 kHz audio and gives a
  probability for each of 360 pitch bins, 20 cents apart. The released model
  was trained on MIR-1K, Bach10, RWC-Synth, MedleyDB, MDB-STEM-Synth and
  NSynth, "composed of vocal and instrumental audio".
- torchcrepe converts the original "tiny" and "full" weights. Unlike the
  original, it decodes with **Viterbi by default** to remove "double/half
  frequency errors" by "penalizing large pitch jumps".
- The README advises masking low-confidence frames (an example threshold of
  0.21 after a 3-frame median filter), `threshold.Hysteresis` against noisy
  voicing, and `threshold.Silence(-60 dB)` because "CREPE was not trained on
  silent audio" and can be confident in silence.

**How we call it**: `torchcrepe.predict(..., "full", return_periodicity=True)`
with the horn's range as fmin/fmax, so the default Viterbi decoder; confidence
median-filtered over 3 frames; voiced when confidence > 0.5 and loudness above
1% of the take's peak. Our loudness gate does the job of the Silence
threshold. Our 0.5 confidence cut is stricter than the README's 0.21 example,
which keeps out noise but may drop soft, breathy or half-valved notes.

**The leap problem, checked**: torchcrepe's Viterbi transition table is
`max(12 − |bin jump|, 0)` (`torchcrepe/decode.py`), so any jump of 12 bins
(240 cents) or more in one frame has zero probability. Feeding that exact table
a clean jump (one-hot input, librosa's Viterbi, same as torchcrepe uses)
gives:

| Jump | Frames off the new note | Time spent on in-between pitches |
| --- | --- | --- |
| Half step, whole step | 0 | 0 ms |
| Minor third | 1 | 10 ms |
| Fourth | 2 | 20 ms |
| Octave | 5 | 50 ms |
| Half-step or whole-step trill, 70 ms per note | 0 of 70 | none |
| Minor-third trill, 70 ms per note | 9 of 70 | 10 ms per change |

(Script: a 40-frame jump test and a 70-frame trill test using the transition
from torchcrepe 0.0.24; the network itself isn't involved, so this is the
decoder's built-in limit, not a guess about the model.)

What this means for us: the contour layer draws a slide that wasn't played on
every leap bigger than a whole step, which shows up in the play-along view,
in cents-off-pitch for the first frames of each note, in the `segment` and
`contour` note tools, and in frame pitch accuracy. Basic Pitch (the default
note tool) doesn't read the contour, so default note F1 is not affected.

**Alternatives for pitch**
- A wider decoder of our own (a few lines): Viterbi with a small cost for any
  jump instead of a ban, plus an extra cost for exactly ±12 semitones, which
  keeps the octave protection but allows real leaps. Or torchcrepe's
  `weighted_argmax` (the original CREPE behaviour) as a control.
- **SwiftF0** (MIT, 2025): 14k-parameter model, 46.9–2093.8 Hz (alto
  altissimo fits), top pitch F1 of 19 trackers in its author's benchmark, tied
  with RMVPE, very fast on CPU. Training data *to verify* in its training repo.
  The best candidate for a second tracker.
- RMVPE and FCPE (both MIT): built for singing voice inside mixes; worth a look
  only for band records, after SwiftF0.
- PESTO (LGPL-3): tiny and real-time, but the packaged model was trained on
  MIR-1K (singing) only. Keep it for a future real-time mode, as the card
  already says.

## Basic Pitch (Layer 3 notes, default)

**What the authors say**
- Instrument-agnostic, polyphonic, "works best on one instrument at a time".
  Trained on GuitarSet, iKala, MAESTRO, MedleyDB-Pitch and Slakh (the
  training and data scripts are now in the repo, `basic_pitch/train.py` and
  `basic_pitch/data/`, so fine-tuning is possible; they use TensorFlow).
- Defaults: onset threshold 0.5, frame threshold 0.3, shortest note 127.7 ms,
  `melodia_trick=True`. In the note-building step (`note_creation.py`)
  `infer_onsets=True` "add[s] additional onsets when there are large
  differences in frame amplitudes", a note keeps going until 11 frames
  (about 128 ms) fall below the frame threshold, and the melodia step
  creates notes from remaining energy even where no onset fired.
- Supports Python 3.7–3.11; Core ML on macOS, ONNX/TFLite elsewhere. Our Mac
  scorecards run Core ML and the Linux tests run ONNX; small numeric
  differences between them are possible.

**How we call it**: `predict(onset_threshold=0.5, frame_threshold=0.3,
minimum_note_length=50, min/max frequency from the horn, melodia_trick=True)`,
then our one-line rule. We use Basic Pitch's own defaults except the shortest
note (50 ms vs 127.7 ms), chosen to keep fast runs.

**Relevant to our weak spots**
- *Extra and split notes*: the three settings above (`infer_onsets`,
  `melodia_trick`, a short minimum) all add notes. On a monophonic horn the
  amplitude-jump onsets are the most likely cause of a held note being cut in
  two at a vibrato swell or growl. Whether they matter is a measurement, not a
  certainty: slurred notes with weak attacks may need the melodia step.
- *Trills*: no Basic Pitch setting writes "one trilled note". GRFIA writes a
  trill as one note, so anything that writes each alternation scores low
  there; that is a notation problem for our own code.
- *Onset timing*: Basic Pitch works in frames of about 11.6 ms and reports the
  frame where the onset peaks. Our GRFIA onset recall gap may be a constant
  lag we can measure and remove before blaming the model.
- *Training domain*: almost no real jazz sax. That is the case for a
  fine-tune on GRFIA (and Filosax when it arrives), which the released
  training code makes practical in Colab.

**Alternatives for notes**
- Fine-tuned Basic Pitch on GRFIA's training split (non-commercial licence,
  fine for us): the most direct attack on extra/split notes, onsets and
  sax-specific attacks. Colab job; the weights come back as a Core ML model.
- MuScriptor (Kyutai, 2026; CC BY-NC 4.0, gated download, about 1.3 B
  parameters, instrument-conditioned): worth one comparison on band records,
  because it transcribes the sax straight from the mix. Heavy for the Mac;
  licence fine for personal use.
- YourMT3+ (GPL-3 code): multi-instrument, strong on URMP-style ensembles;
  comparison only, never copied into the repo.
- CREPE Notes (GPL-3): we already re-implemented the method
  ([ADR-0006](../decisions/0006-own-crepe-notes-implementation.md)); the
  leap problem above may be part of why our segmenter underperforms the
  paper.

## Beat This! (Layer 3 beats)

**What the authors say**
- Transformer beat and downbeat tracker, no DBN needed. `final0`–`final2`
  are trained on 16 datasets except GTZAN, including Filosax (sax over backing
  tracks), JAAH (jazz), Candombe, GuitarSet (solo guitar) and Groove MIDI. So
  jazz and swing are in-domain.
- Code and weights MIT; "some of the training files are fully copyrighted or
  under limited Creative Commons licenses, and it is up to the user to assess
  whether this may impact their use case". No issue for a personal tool.
- v1.1.0 (2026-04-14) fixed checkpoint downloads "after server-side update"
  and is now on PyPI as `beat-this`.

**How we call it**: `File2Beats(checkpoint_path="final0", dbn=False)` on the
full mix, which is the authors' default. The `dbn=True` option needs madmom,
whose models are CC BY-NC-SA; no reason to switch.

**Relevant to sax and jazz**: fine on band records. On a lone horn it finds
few beats; nothing in its training set is unaccompanied wind, so that is
expected, and our notes-based beat (PR #29) is the right answer there. GRFIA
takes are played to a metronome that isn't in the audio, so the grid must come
from the tempo in the score, not from beat tracking.

**Alternatives**: none worth testing now. madmom is older and its models are
non-commercial; All-In-One adds structure labels on top of Demucs and madmom.

## Settings to test, in order

Each one changes output, so each needs a scorecard before and after
(GRFIA alto and tenor, URMP, ChoraleBricks, Omnibook stems, and the Blues for
Mary Jane key), plus the "no real note lost" check.

1. **Basic Pitch decoding grid** (cheap: run the network once per take, keep
   its raw output, then re-run only `basic_pitch.note_creation.model_output_to_notes`).
   Try `infer_onsets` off, `melodia_trick` off, shortest note 50 / 80 /
   127.7 ms, onset threshold 0.5 / 0.6. Targets extra and split notes.
   Watch note recall, not just F1.
2. **Onset bias check** (no new run: from existing GRFIA runs, take
   matched notes and average est − ref onset time per tool). If there is a
   steady lag, shift by it; if the spread is wide, the problem is real
   detection, not timing.
3. **CREPE decoder**: current Viterbi vs `weighted_argmax` vs a wide Viterbi
   with an octave penalty. Score pitch accuracy, octave errors, and the
   `segment` tool's note F1 and onset F1. Also try confidence 0.3 vs 0.5.
4. **SwiftF0** as `--contour-tool swiftf0`, scored the same way, and on
   Demucs stems for octave drops.
5. **Separator bake-off** on `omnibook-mix` and Blues for Mary Jane:
   `htdemucs_6s` (now) vs `htdemucs_6s --shifts 2` vs `htdemucs_ft` "other" vs
   one BS-RoFormer "other" model. Record seconds per minute too.
6. **Fine-tune Basic Pitch on GRFIA** (Colab), after 1 shows what the
   decoding settings alone can do.

## Housekeeping

- Pin what the scorecards ran on: `demucs==4.0.1` (or move to 4.1.0 after a
  scorecard), `beat-this==1.1.0` from PyPI instead of git main,
  `librosa<1.1` until 1.0 is scored, and add `mirdata` with a one-line
  reason. First step: `pip freeze` on the Mac to see what is actually
  installed.
- Record package versions (and the Beat This! checkpoint name) in `take.json`
  and in each scorecard results line, so a change in a library is as visible
  as a change in our code.
- Fix the [Demucs card](demucs.md): weights licence and six-stem training
  data. Add the training-overlap notes to the CREPE, Basic Pitch and Beat This!
  cards.
