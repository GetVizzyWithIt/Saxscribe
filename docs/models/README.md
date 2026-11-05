# Model cards

One card per model or rule-based component that changes what the tool
outputs. Format follows Mitchell et al., "Model Cards for Model Reporting"
(FAT* 2019), trimmed to what matters for a single-user tool.

| Card | Layer | Kind | Status |
| --- | --- | --- | --- |
| [Demucs (htdemucs_6s)](demucs.md) | 1 isolate | Pretrained, used as is | Default for `--mix` |
| [CREPE via torchcrepe](crepe.md) | 2 contour | Pretrained, used as is | Default |
| [Basic Pitch](basic-pitch.md) | 3 notes | Pretrained, used as is | Default |
| [Sax onset model (CRNN)](onset-crnn.md) | 3 notes | Trained by us on GRFIA + Omnibook (non-commercial weights) | Experimental, not in the app |
| [Note rules: one-line, split-note join, segmenter, contour cutter](note-rules.md) | 3 notes | Our own rules, no training | Join off by default since PR #22; others optional |
| [Beat This!](beat-this.md) | 3 beats | Pretrained, used as is | Default |
| [Filosax separator and transcriber (Riley & Dixon)](filosax.md) | 1 isolate, 3 notes | Pretrained on Filosax, used as is | Opt-in (`--separator filosax`, `--notes-tool filosax`, app "Filosax (test)") |

What the upstream authors document (training data, limits, licences, versions, alternatives), checked against our cards: [upstream model review](upstream-review.md), 2026-11-03.

Before/after numbers for every model and pipeline change, in one table: [evaluation log, change by change](../evaluation/log.md#change-by-change-what-each-model-or-pipeline-change-did).

No model has been trained or fine-tuned for Saxscribe yet. The first trained
model gets a card from [_template.md](_template.md) before its PR merges.

## Candidates under consideration (no card until adopted)

From the requirements doc's "alternatives to benchmark":

| Candidate | Would replace or add | Why |
| --- | --- | --- |
| BS-RoFormer, UVR community models | Demucs | Stronger separation; still no sax stem |
| Sax-vs-rest separation fine-tune | Demucs | Biggest potential win for full mixes |
| PESTO | CREPE | Tiny and fast; the one for a future real-time mode |
| MuScriptor | Basic Pitch on mixes | Instrument-conditioned transcription; check weight licence first |
| Onset/articulation head on MuQ or MERT embeddings (weights CC BY-NC 4.0) | Basic Pitch + rules | Articulation tags no off-the-shelf model gives |
| Essentia / madmom key detection | music21 key finder | Key from audio, not just notes |
