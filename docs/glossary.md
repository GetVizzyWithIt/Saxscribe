# Glossary

Plain-language meanings of terms used in the code and these docs.

## Music and saxophone

| Term | Meaning |
| --- | --- |
| Concert pitch | The pitch that actually sounds. Everything is stored this way |
| Written pitch | What a sax player reads. Alto/baritone in Eb, tenor/soprano in Bb |
| Transposition | Alto sounds a major 6th below written; tenor a major 9th; baritone an octave plus a major 6th |
| Altissimo | Notes above the horn's normal top (above high F#) |
| Articulation | How a note starts and joins: tongued (re-attacked), slurred (no new attack) |
| Scoop / fall / bend | Pitch sliding up into a note, falling off the end, or bending in the middle |
| Subtone, growl | Breathy soft tone; rough tone from humming or throat while playing |
| Swing ratio | How much longer the first eighth of a pair is: 1 = straight, 2 = triplet swing (2:1) |
| Quantization | Snapping played times onto a grid of written note values |
| Enharmonic spelling | Choosing between names for the same pitch (F# vs Gb) |
| Downbeat | Beat 1 of a bar |
| OMR | Optical music recognition: reading printed sheet music into MusicXML |

## Signal and transcription

| Term | Meaning |
| --- | --- |
| Stem | One instrument's audio on its own, from a multitrack or a separator |
| Source separation | Splitting a mix into stems (Demucs) |
| f0 / pitch contour / pitch line | The fundamental frequency over time; Layer 2 |
| Voiced frame | A 10 ms slice where the sax is sounding a pitch |
| Confidence / periodicity | The pitch tracker's sureness that there is one clear pitch |
| Onset / offset | When a note starts / ends |
| Cents | Hundredths of a semitone; 50 cents = a quarter tone |
| Note event | One note: onset, offset, pitch, cents off, loudness, tags |
| Segmentation | Cutting a continuous pitch line into separate notes |
| Split note | One played note written as two (the main solo error so far) |
| Monophonic / polyphonic | One note at a time / several |
| Chroma | How much of each of the 12 pitch classes sounds at each moment |
| DTW (dynamic time warping) | Stretching one sequence onto another to line them up; used to align a score to a take |
| Beat grid | The tracked beats the notation is quantized against |

## Evaluation and ML

| Term | Meaning |
| --- | --- |
| Answer key / ground truth | The correct notes for a recording, to score against |
| mir_eval | The standard music-information-retrieval scoring library |
| Precision / recall | Of the notes we wrote, how many are right / of the right notes, how many we found |
| F1 | The balance of precision and recall (their harmonic mean) |
| Onset F1 | F1 counting only note starts (±50 ms) |
| Note F1 | F1 where start, pitch and end must all be right |
| Raw pitch accuracy | Share of sounding frames where our pitch is within 50 cents |
| Scorecard | A run of the tool over an answer-key set, with the metrics |
| Train / test split | Data used to tune or train vs. data kept back to measure; split by tune |
| Leakage | When test material (or the same performance) also influences training, inflating scores |
| Fine-tune | Further training of a pretrained model on our data |
| Augmentation | Altering training audio (pitch shift, stretch, reverb, noise) to make more examples |
| MPS / Core ML | Apple's GPU backend for PyTorch / Apple's model runtime |
| Checkpoint / weights | A saved trained model |
| Model card / datasheet | Standard documents describing a model / a dataset |
| ADR | Architecture decision record: one page per lasting decision |
| CRISP-DM | The common six-phase data-science project cycle |

## Project terms

| Term | Meaning |
| --- | --- |
| Layer | One of isolate, contour, notes, notation; each its own file(s) |
| Take folder | `<file>.saxscribe/`, holding every layer for one recording |
| Notes tool | Which method makes Layer 3: `basic_pitch` (default), `basic_pitch_join`, `segment`, `contour`; `basic_pitch_raw` is an alias of the default |
| Horn / instrument profile | Pitch range plus transposition (alto, tenor, baritone) |
| Fixture | The synthetic 10-second alto phrase the tests run on |
| Tier A–E | Label quality levels in [data/README.md](data/README.md) |
| The game | Songs in the Key of Life, the sibling project whose front end was copied |
| `not_sax` / `maybe_not_sax` | Note tags. `not_sax`: kept in notes.json but off the sheet (e.g. below the horn's low note, PR #81). `maybe_not_sax`: may be another instrument's solo; stays on the sheet and is asked about in the play-along (PR #121) |
| Review flags | Bars or notes Austin marks in the play-along by error type, saved to `flags.json`; never change the transcription (PR #116) |
