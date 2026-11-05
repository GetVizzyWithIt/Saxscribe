# Model card: Demucs (htdemucs_6s)

## Model details
- **What it does**: splits a full mix into six stems: drums, bass, vocals, guitar, piano, other.
- **Developed by**: Meta AI Research (Rouard, Massa, Défossez). Hybrid Transformer Demucs, v4.
- **Type**: hybrid network that works on both the waveform and the spectrogram, with a transformer between them. `htdemucs_6s` is the experimental six-stem variant of the four-stem `htdemucs`.
- **Licence**: code MIT. The `htdemucs_6s` weights were trained only on Meta's internal dataset, which the author says "likely means CC-NC-BY": non-commercial. Fine for a single-user tool; would matter for any public release ([upstream review](upstream-review.md)).
- **Maintenance**: the author's fork (adefossez/demucs) gets bug fixes only. Version 4.1.0 (2026-07-11) drops torchaudio for inference, which would let us lift the `torchaudio<2.9` cap.
- **How Saxscribe calls it**: `frontend.separate_stems()` runs `python -m demucs -n htdemucs_6s -d <mps|cpu>`; only with `transcribe --mix` or the `*-mix` scorecard sets. Stem choice: `--stem`; otherwise "other" until PR #24, which picks the stem with the clearest single melody line and sums stems when the sax is split.
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
Per the author's README, the `htdemucs_6s` weights were trained only on Meta's internal dataset (not MUSDB18-HQ plus internal, as this card said before). Stems: drums, bass, vocals, guitar, piano, other. Saxophone is not a target class ([upstream review](upstream-review.md)).

## Evaluation data
`urmp-mix` (11 parts), `bach10-mix` (10 chorales), `omnibook-mix` (10 Parker records).

## Quantitative results
Downstream, default tools, 2026-11-02 ([log](../evaluation/log.md)):

| Set | Pitch accuracy | Note F1 | Same parts recorded alone |
| --- | --- | --- | --- |
| urmp-mix | 41.6% | 17.1% | 94.4% / 64.4% |
| bach10-mix | 21.4% | 3.9% | 96.9% / 87.5% |

The drop from solo to mix is the separator's: the stem follows violin,
clarinet, bassoon or brass instead of the sax.

## Ethical and licensing considerations
Weights are likely non-commercial (CC-NC-BY, per the author); no limit for Austin's private use, but a blocker for any public release. Records fed to it are Austin's own copies and stay on the Mac.

## Caveats and recommendations
- On some Parker records the sax lands in "guitar" or is split between "guitar" and "other". Automatic stem choice (PR #24) lifted 10 Parker records from 50.6% to 56.4% note F1 (worst three: 24/30/25% → 56/49/41%) and cut time from 110 to 64 s per minute.
- The URMP and Bach10 mixes are harder than a jazz record (the sax is often an inner voice), so they are stress tests, not forecasts.
- Compared 2026-11-03 ([log E25](../evaluation/log.md), [ADR-0027](../decisions/0027-keep-htdemucs-6s.md)): htdemucs_ft and BS-RoFormer were 3–4× slower and scored lower (Parker records 52.2% and 52.7% vs 56.4%; Blues for Mary Jane 32.3% and 39.8% vs 51.0%). Two averaged shifts: 57.0% / 54.3% at +50% time, a candidate quality setting.
- Round 2, 2026-11-04 ([log E30](../evaluation/log.md), [ADR-0028](../decisions/0028-two-demucs-shifts-by-default.md)): ten alternatives tested (UVR woodwind model, AudioSep, pitch-guided filter, BS-RoFormer cascade, Demucs twice, Banquet). Only two averaged shifts helped on both sets with no loss (Parker 57.1% → 57.9%, Blues for Mary Jane 53.1% → 55.0%); it is the default since PR #61.
- Piano in the sax stem, 2026-11-04 ([log E46](../evaluation/log.md)): on Pennies From Heaven Oscar Peterson's piano lands in "vocals + other" with the sax (the piano stem is about 58 dB down), so Demucs can't separate them.
- Sax-specific separators surveyed 2026-11-05 ([survey](https://claude.ai/artifact/1mYvTsPk5ENMfbJbU1nDz5)). The BS-RoFormer rejected in E25/E30 was a general model, not a sax one. Queued for Mac tests: (1) the MVSep Mega 53-stem open model (ZFTurbo Music-Source-Separation-Training release v1.0.21, a BS-RoFormer with separate sax and piano stems, sax SDR 8.89, MIT licence); (2) PANNs Cnn14_DecisionLevelMax frame-by-frame sax and piano scores as a `not_sax` reason; tested 2026-11-05 and not adopted: it barely hears the piano on band records and hiding by its scores lost about half real notes ([log E50](../evaluation/log.md)). The MVSep Saxophone web model (SDR 9.77, no public weights) sends audio off the Mac; Austin approved testing it on 2026-11-05. SAM-Audio (needs CUDA, so Colab) not yet tested.
- Next: a sax-vs-rest fine-tune using JazzSAMBA's stems and mixes (Phase 2).

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | Copied from the game analyzer; default stem "other" | #1 |
| 2026-11-03 | Stem chosen by melody clarity, summed when split | #24 |
| 2026-11-03 | Licence and training data corrected from the upstream review; maintenance status and 4.1.0 noted | #51 |
