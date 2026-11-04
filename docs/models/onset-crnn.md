# Model card: sax onset model (CRNN, experimental)

## Model details
- **What it does**: marks the moment each sax note starts, including a same-pitch note tongued again, from the sound of the stem.
- **Developed by / version / date**: Saxscribe build thread; first run, 2026-11-04 (training finished 04:11 UTC). Experimental, not in the app.
- **Type**: small convolutional-recurrent network (CRNN), about 0.15M weights. Input is a log-mel spectrogram (128 bands, 30 Hz–8 kHz, 22.05 kHz audio, 10 ms hop) plus its positive frame-to-frame difference. Three conv blocks (two 3×3 convolutions with batch norm and ReLU, frequency max-pool 4), a two-layer bidirectional GRU (64 units), and a per-frame sigmoid.
- **Source and licence**: our code (training script copy at `/mnt/project-files/scripts/train_onset.py`). Weights derive from GRFIA-RealSax (CC BY-NC-SA 4.0) and the Omnibook (CC BY 4.0), so they are for personal, non-commercial use only.
- **How Saxscribe calls it**: not wired in yet. Checkpoint `~/saxscribe-runs/exp/2026-11-04-onset-model/onset_crnn.pt` on the Mac; frame threshold 0.7, at most one onset per 30 ms. Plan: [onset model plan](https://claude.ai/artifact/FU1G7EehsP3qVnragnApGx).
- **Citation**: none (in-house).

## Intended use
- **In Saxscribe**: Layer 3 (notes), to split notes Basic Pitch merges, chiefly soft re-tongued repeats with little loudness dip (the onset recall still lost since #52, [log E29](../evaluation/log.md), [E31](../evaluation/log.md)). U1 own takes first.
- **Out of scope**: full-band mixes (trained on solo sax only); deciding pitch; deleting notes. It may only add note starts, never remove notes ([ADR-0016](../decisions/0016-notation-never-drops-notes.md)).

## Factors
Trained on alto and tenor, solo, studio and practice-room takes. Untested on bari, soprano, band stems, subtone and growl. Register and articulation effects not yet measured.

## Metrics
Onset F1, precision and recall with mir_eval at 50 ms, plus recall on same-pitch repeats. Recall comes first: a missed onset is a missing note.

## Training data
GRFIA-RealSax alto and tenor plus the Omnibook, train tunes only (split by tune): 811 takes, 3.27 hours, all saxophone. Labels: 1.0 on the onset frame, 0.5 on its neighbours; same-pitch repeats (starting less than 150 ms after the previous note ends) weighted ×3; loss BCE with positive weight 5. AdamW 1e-3, one-cycle schedule, 6000 steps, batch 24, 4 s crops, gain jitter. 7242 s on the Mac (MPS).

## Evaluation data
Held out: URMP, Bach10 and ChoraleBricks in full, and GRFIA test tunes (235 takes). GRFIA test tunes share the player and room with training, so those scores are optimistic.

## Quantitative results
First run, against librosa's `onset_detect` (not against Basic Pitch, the current default) ([log E35](../evaluation/log.md)). F1 / precision / recall / repeat recall:

| Set | CRNN | librosa |
| --- | --- | --- |
| URMP | 20.8 / 66.9 / 14.1 / 8.4% | 65.3 / 55.0 / 81.5 / 67.3% |
| Bach10 | 83.1 / 78.3 / 88.8 / 89.2% | 68.4 / 52.3 / 99.4 / 100% |
| ChoraleBricks | 57.9 / 62.4 / 55.4 / 55.7% | 53.0 / 42.6 / 72.7 / 78.0% |
| GRFIA alto test | 76.6 / 74.2 / 79.8 / 86.7% | 58.5 / 42.6 / 95.0 / 97.0% |
| GRFIA tenor test | 72.8 / 70.9 / 75.2 / 80.7% | 60.9 / 46.0 / 93.3 / 92.2% |

## Ethical and licensing considerations
GRFIA's non-commercial licence carries to the weights: fine for Austin's personal use, not for a release. Audio stays on the Mac.

## Caveats and recommendations
- Higher F1 on four of five sets comes from precision; recall and repeat recall are lower than librosa's on every set, which is the wrong trade for a never-drop tool.
- URMP fails (14% recall). The threshold (0.7) was chosen on training data and is too strict; a looser re-check is next. URMP's recording conditions differ from the training data, so poor generalisation is also possible.
- Next: lower the threshold on a validation split, compare against Basic Pitch's own onsets, then try it only as a splitter of long same-pitch notes.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-04 | First training run, interim results, not adopted | — (docs only) |
