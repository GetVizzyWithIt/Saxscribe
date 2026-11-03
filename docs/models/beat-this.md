# Model card: Beat This!

## Model details
- **What it does**: finds beats and downbeats in a recording.
- **Developed by**: Foscarin, Schlüter, Widmer (JKU Linz), 2024.
- **Type**: transformer over a spectrogram, predicting beat and downbeat frames directly, without the dynamic Bayesian network (DBN) clean-up older trackers needed.
- **Licence**: MIT (code and checkpoints), *to verify* for checkpoints.
- **How Saxscribe calls it**: `frontend.detect_beats()` → `File2Beats(checkpoint_path="final0", dbn=False)` on the full `source.wav`; CPU retry on GPU failure. Falls back to librosa's beat tracker (and a 4/4 low-end-energy guess for downbeats) if fewer than 8 beats are found or the model can't load.
- **Citation**: Foscarin, Schlüter, Widmer, "Beat this! Accurate beat tracking without DBN postprocessing", ISMIR 2024.

## Intended use
- **In Saxscribe**: Layer 3 beats and downbeats; Layer 4 uses them as the grid for quantizing and bar lines.
- **Out of scope**: solo sax with no rhythm section is a weak case (few percussive cues); expect drift.

## Factors
Band present vs. solo horn; swing; rubato; tempo changes.

## Metrics
Beat F1 at ±70 ms (mir_eval), only on sets whose answer keys have beats (Omnibook downbeats; Filosax). Not yet reported separately.

## Training data
Per the paper: a large collection of public beat-annotated datasets across genres, including jazz. "final0" is one of the checkpoints trained on all training data. *To verify* the exact list.

## Evaluation data
Pending: Omnibook (downbeats), Filosax when granted.

## Quantitative results
None reported yet. On the synthetic fixture it placed the last bar one beat later than librosa did, which is why the notation test now uses the fixture's true grid (PR #7).

## Ethical and licensing considerations
No known limits.

## Caveats and recommendations
- On unaccompanied sax it can find almost no beats; before PR #15 the notation step then dropped most notes (42 of 398 in the first PDF render). See [log E5](../evaluation/log.md).
- On the Parker test solo (sax alone) it found 13 beats in 90 s, and the filled grid read 162 BPM for a ~261 BPM solo. PR #29 takes the beat from the notes in that case ([log E13](../evaluation/log.md)).
- Add a beat F1 column to the Omnibook scorecard summary.
- For Austin's solo takes, a click track or backing track would give the grid.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | Copied from game analyzer | #1 |
| 2026-11-02 | Notation no longer drops notes when beats are missing | #15 |
| 2026-11-03 | Sparse beats on lone sax: notation takes the beat from the notes | #29 |
