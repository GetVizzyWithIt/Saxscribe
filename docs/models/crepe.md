# Model card: CREPE (via torchcrepe), with pYIN fallback

## Model details
- **What it does**: estimates the pitch of a single melodic line every 10 ms, with a confidence for each frame.
- **Developed by**: CREPE by Kim, Salamon, Li and Bello (NYU, 2018); torchcrepe is Max Morrison's PyTorch port.
- **Type**: convolutional network on 1024-sample windows of 16 kHz audio; outputs a probability over 360 pitch bins 20 cents apart (about C1 to B7). "Full" capacity model.
- **Licence**: MIT (CREPE and torchcrepe).
- **How Saxscribe calls it**: `layers/contour.py` → `torchcrepe.predict(audio, 16000, hop=160, fmin, fmax, "full", return_periodicity=True)`, range from the horn profile; confidence median-filtered over 3 frames; voiced when confidence > 0.5 and loudness > 1% of peak. MPS, retried on CPU on failure.
- **Fallback**: pYIN (Mauch & Dixon, 2014; librosa), frame 1024, same hop; used when torchcrepe is missing or `--contour-tool pyin`.
- **Citation**: Kim et al., "CREPE: A Convolutional Representation for Pitch Estimation", ICASSP 2018.

## Intended use
- **In Saxscribe**: Layer 2 for every use case. The contour is the record of bends, scoops and vibrato, and feeds the `segment` and `contour` note tools and each note's cents deviation.
- **Out of scope**: more than one sounding line (a mix that wasn't separated, or bleed in the stem).

## Factors
- Clean solo sax: near target.
- Separated stems with bleed: pitch accuracy falls with how much else is in the stem (73% on Omnibook stems, 21–42% on ensemble mixes).
- Altissimo and growl: not yet measured separately.

## Metrics
Raw pitch accuracy (±50 cents) on voiced frames, plus voicing recall and false alarm, with mir_eval.

## Training data
Per the paper: synthesised datasets re-rendered from real recordings so the pitch labels are exact (RWC-synth and MDB-stem-synth), which include wind instruments but no dedicated sax set.

## Evaluation data
All answer-key sets; see the log.

## Quantitative results
Default settings, 2026-11-02 ([log](../evaluation/log.md)):

| Set | Pitch accuracy | Target |
| --- | --- | --- |
| choralebricks (38 parts) | 98.9% | 97% solo |
| bach10 (10) | 96.9% | 97% solo |
| urmp (11) | 94.4% | 97% solo |
| omnibook stems (46) | 73.3% | 90% mix |

Note: our pitch accuracy gives each answer-key frame its note's fixed pitch,
so deep vibrato or bends cost a little even when the contour is right.

## Ethical and licensing considerations
MIT; no limits.

## Caveats and recommendations
- Pitch is close to solved on clean sax; spend effort on note boundaries and separation first.
- URMP's 16_Surprise scored 81% under every tool and needs a listen.
- Candidate swap for real time: PESTO.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | Contour layer with torchcrepe full, pYIN fallback | #1 |
