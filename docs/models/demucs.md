# Model card: Demucs (htdemucs_6s)

## Model details
- **What it does**: splits a full mix into six stems: drums, bass, vocals, guitar, piano, other.
- **Developed by**: Meta AI Research (Rouard, Massa, Défossez). Hybrid Transformer Demucs, v4.
- **Type**: hybrid network that works on both the waveform and the spectrogram, with a transformer between them. `htdemucs_6s` is the experimental six-stem variant of the four-stem `htdemucs`.
- **Licence**: MIT (code and weights).
- **How Saxscribe calls it**: `frontend.separate_stems()` runs `python -m demucs -n htdemucs_6s -d <mps|cpu>`; only with `transcribe --mix` or the `*-mix` scorecard sets. Stem choice: `--stem`, default `other`.
- **Citation**: Rouard, Massa, Défossez, "Hybrid Transformers for Music Source Separation", ICASSP 2023.

## Intended use
- **In Saxscribe**: Layer 1 for U2 (records with a band). Not used on solo takes.
- **Out of scope**: separating sax from other horns, strings or woodwinds. It has no sax stem; the sax lands in "other" together with every instrument that isn't drums, bass, vocals, guitar or piano.

## Factors
- Works best when the sax is the only melodic instrument outside piano and guitar (a classic quartet).
- Fails when other horns or strings play at the same time: they share the "other" stem.
- The six-stem model's piano stem is known to be weaker than its other stems (per the Demucs authors); piano can bleed into "other".

## Metrics
Not scored directly (no separated-sax answer keys yet). Judged through the
downstream pitch accuracy and note F1 on the `*-mix` sets, compared with the
same parts' solo recordings.

## Training data
MUSDB18-HQ plus an internal set of several hundred songs, per the paper; four-stem
targets plus guitar and piano for the six-stem model. Saxophone is not a target
class. *To verify*: exact training mix for the six-stem variant.

## Evaluation data
`urmp-mix` (11 parts), `bach10-mix` (10 chorales), `omnibook-mix` (Parker records, run pending).

## Quantitative results
Downstream, default tools, 2026-11-02 ([log](../evaluation/log.md)):

| Set | Pitch accuracy | Note F1 | Same parts recorded alone |
| --- | --- | --- | --- |
| urmp-mix | 41.6% | 17.1% | 94.4% / 64.4% |
| bach10-mix | 21.4% | 3.9% | 96.9% / 87.5% |

The drop from solo to mix is the separator's: the stem follows violin,
clarinet, bassoon or brass instead of the sax.

## Ethical and licensing considerations
MIT; no limits for this use. Records fed to it are Austin's own copies and stay on the Mac.

## Caveats and recommendations
- The URMP and Bach10 mixes are harder than a jazz record (the sax is often an inner voice), so they are stress tests, not forecasts.
- Next: benchmark BS-RoFormer and UVR models on the same sets; then a sax-vs-rest fine-tune using JazzSAMBA's stems and mixes (Phase 2).

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | Copied from the game analyzer; default stem "other" | #1 |
