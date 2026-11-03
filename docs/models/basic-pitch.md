# Model card: Basic Pitch

## Model details
- **What it does**: turns audio into note events (start, end, pitch, loudness) for any instrument.
- **Developed by**: Spotify Audio Intelligence Lab (Bittner et al., 2022).
- **Type**: small convolutional network (under 20k parameters) on a harmonic constant-Q spectrogram; predicts onsets, active notes and fine pitch, then a rule-based step turns those into notes.
- **Licence**: Apache 2.0.
- **How Saxscribe calls it**: `frontend.basic_pitch_notes()` → `predict(onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=50 ms, min/max frequency from the horn, melodia_trick=True)`. Core ML backend on the Mac, ONNX elsewhere; one automatic retry because the first Core ML call sometimes fails while loading. Output then goes through the [note rules](note-rules.md) (one-line, split-note join).
- **Citation**: Bittner, Bosch, Rubinstein, Meseguer-Brocal, Ewert, "A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription and Multipitch Estimation", ICASSP 2022.

## Intended use
- **In Saxscribe**: Layer 3 default for all use cases; also the baseline the v1 gate must beat on mixes.
- **Out of scope**: articulation (no tags), sub-50 ms grace notes.

## Factors
- Splits held and tongued-repeat notes: writes 1.05–1.45× the answer key's notes on URMP, 1.5–3.2× on Omnibook stems.
- Note ends: note F1 is 8–16 points lower when offsets count.
- Polyphonic by design; bleed in a separated stem becomes extra notes.

## Metrics
Onset F1 and note F1 (with and without offsets), mir_eval, 50 ms / 50 cents / 20% offset.

## Training data
Per the paper: a mix of datasets covering voice, guitar, piano and multitrack recordings (GuitarSet, iKala, MAESTRO, MedleyDB-Pitch, Slakh). Saxophone appears only inside MedleyDB-Pitch and Slakh's synthesised tracks. *To verify* against the paper.

## Evaluation data
All answer-key sets.

## Quantitative results
Default (Basic Pitch, before the split-note join), 2026-11-02 ([log](../evaluation/log.md)):

| Set | Onset F1 | Note F1 | Note F1, no offsets |
| --- | --- | --- | --- |
| bach10 | 92.2% | 87.5% | 92.2% |
| choralebricks | 86.7% | 77.8% | 86.5% |
| urmp | 81.6% | 64.4% | 80.8% |
| omnibook stems | 60.4% | 45.0% | — |

Published reference: on Filosax, CREPE Notes reports note F-measure 82.3 against Basic Pitch's 75.5 (Riley & Dixon, SMC 2023). Our own CREPE Notes style cutter did not reproduce that gap on URMP or ChoraleBricks (see [note rules](note-rules.md)).

## Ethical and licensing considerations
Apache 2.0; no limits.

## Caveats and recommendations
- The split-note join (PR #10) aimed at its main failure but merged real repeats and lowered scores (log E8); off by default again in PR #22, available as `basic_pitch_join`.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | Copied from game; minimum note 50 ms (game used 80 ms) | #1 |
| 2026-11-02 | Split-note join added after it by default | #10 |
| 2026-11-02 | Join off by default again | #22 |
