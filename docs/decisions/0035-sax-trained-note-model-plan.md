# ADR-0035: Plan for a sax-trained note model: retrain Riley and Dixon's sax model first

- **Date**: 2026-11-05
- **Status**: Proposed (plan; no training run yet)
- **Decided by**: Claude (note-model thread), plan for Austin's review
- **Plan**: https://claude.ai/artifact/9oPaB15bENmCzL49qAnb1Q
- **Relates to**: [ADR-0016](0016-notation-never-drops-notes.md), [ADR-0026](0026-adaptive-minimum-note-length.md)

## Context
Settings and rule changes have stopped paying off (onset tests E44, E45 and E47; separators E30 and E51). The tool reaches 76–97% note F1 on clean solo sax but the mid-50s to low 60s on band records. Off-the-shelf note models were not trained on sax in a band.

## Options, in order (updated 2026-11-05)
1. **Main line: retrain Riley and Dixon (2024)** ([arXiv 2405.16687](https://arxiv.org/abs/2405.16687)). They fine-tune Kong's high-resolution piano transcription model on Filosax: 80/10/10 split, ±5 semitone pitch shifts, 27.5k steps. Reported onset-only F-measure at 50 ms: 96.19 on the Filosax test set (CREPE Notes 82.67) and 75.43 on the Omnibook band records (CREPE Notes 70.41). The paper calls the weights "under preparation", but the research survey (2026-11-05) found a checkpoint, `filosax_25k.pth` in Hugging Face `xavriley/midi-transcription-models` (MIT); test it as is before retraining. The 75.4 ignores note ends, so it is not comparable with our Parker band-record note F1 of about 58. On the same onset-only measure our pipeline scores 78.5% on the Omnibook, but the splits may differ; stage 0 rescores ours onset-only on all 50 records.
2. **Comparison: fine-tune Basic Pitch** (Apache 2.0, under 20k weights). Training code ships in basic-pitch 0.4.0 (`basic_pitch/train.py`), and it trains on the Mac.
3. **Test YourMT3+ as it is**, in Colab (GPL-3, about 45M weights). It labels the instrument of each note.
4. **Fallback**: our own small model on top of CREPE and onset model v2.

Related: their sax separator is public (`xavriley/demucs_v3_saxophone_separation`, MIT, demucs 3.0.6, 14.22 dB SDR) and is the next separator test in the build thread, pending Austin's written OK. The 2026-11-05 separator survey missed it. Jazz sax data and model survey (2026-11-05): https://claude.ai/artifact/51xs3wjGscA9JLx9ZB4Wxu (markdown copy and source notes in the project files, `research/jazz-sax-survey/`). MERT and MuQ weights are CC BY-NC 4.0.

## Data
- About 4 hours of real, labelled sax on hand, mostly solo.
- **Filosax** (Zenodo 6335779, [datasheet](../data/datasheets/filosax.md)) moves to top priority: about 24 hours of jazz tenor, 5 players, restricted, non-commercial terms; the Aebersold backings are bought separately. Austin has to request it.
- Band training audio is built by mixing clean labelled sax over band audio with no sax.
- Weimar's 271 sax solos, rendered with MIDI-DDSP sax, and ChoraleWind (Zenodo 21217248, CC BY 4.0, 97 hours of rendered wind chorales including alto sax) are used only for warm-up. Same-player, same-tune leakage is removed.
- How many more hand transcriptions are needed (survey estimate): 4–9 more test keys, and 10–20 pop/soul training keys. No jazz training keys are needed if the Weimar records are bought.
- Austin's six answer keys (3,298 notes, about 11 minutes of sax, beat-level timing; pitch agreement with the mix 32–87%) stay test-only. A leave-one-out final tune may use them at the end.

## Validation
- Train, dev and locked test piles split by tune (Filosax: by player).
- Add a bar-level metric (bars written right) and an ear check of each key's noise floor.

## Stages and gates (about 5 weeks)
- Stages 0–4.
- Stage 1, solo: +2 points note F1.
- Stage 2, jazz band: +3 points note F1 and +5 points bars right.
- Stage 3, cloud GPU (roughly $50–150 per run, prices approximate): only if stage 2 stalls.
- Every stage also has to pass the never-drop rule (ADR-0016).

## Consequences
- Basic Pitch stays the default until a stage clears its gate.
- The Riley and Dixon model is a large piano-derived network, so Mac speed has to be checked before it can be the default.
- Filosax and GRFIA terms make any trained weights personal-use only.
- Austin's own recordings remain out of training, as he decided on 2026-11-04.

## First comparison (2026-11-05, log E58)
Riley and Dixon's public transcriber, without retraining, was compared with our note layer on the same separated audio.
- It wins on Parker's band records (67.2% against 62.6% note F1, both on the Filosax separator). That margin is overstated, because the Omnibook keys were refined with a transcription model.
- It is about even on the four tenor tunes (36.1% against 37.3%).
- It loses on Blues for Mary Jane and is about level on Pennies From Heaven.

On the six Weimar solos, whose human keys have no tie to the model, it beats our note layer on every solo. With their separator and no sax cuts it reaches 76.3% note F1, against 65.6% for our best pipeline (#102). Next is whether to adopt it as is for jazz band records, which is Austin's call, before any retraining.

## Plan revision (2026-11-05, plan doc rev 39)
After E58 the plan changes:
- **Base model**: Riley and Dixon's checkpoint, not Basic Pitch. The bar to beat is its own score as is, run with their separator: Weimar 76.3% note F1.
- **Stage 1**: fine-tune it on the Weimar training records plus band mixes with guitar, vocals and keys, aimed at the pop and fusion gap (four tunes 36.1%).
- **Basic Pitch**: the fine-tune becomes optional.
- **Separator**: theirs goes into the app first, behind a setting. It beats Demucs on 21 of 22 records at about 7 s per minute of audio.
- **Weimar test lock**: Impressions 1961, Impressions 1963 and Item 1 (D.I.T.) are held out by record, with about 1 in 5 new records held out going forward. They are never trained on.
- **Weimar alignment**: passed the go/no-go check, with a residual of 2–15 ms.

Plan doc: https://claude.ai/artifact/9oPaB15bENmCzL49qAnb1Q
