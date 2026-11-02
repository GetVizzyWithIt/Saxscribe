# Evaluation protocol

How every number in the [evaluation log](log.md) is produced, so results are
comparable over time and with published work.

## Rule

A model or rule change is not done until it has a before-and-after scorecard
on the fixed sets, in the PR description and in the log (CLAUDE.md).

## How to run

```bash
python -m saxscribe score <set> [--split test] [--notes-tool X] [--contour-tool Y] [--limit N] [--runs DIR]
```

Each run keeps its take folders under `~/saxscribe-runs/<set>/<settings>/`
(re-running a setting reuses lower layers) and writes `scorecard.md` and
`scorecard.json` with per-recording rows and means against the targets.

## Metrics (`saxscribe/score/metrics.py`, all mir_eval)

| Metric | What it measures | Tolerance | mir_eval function |
| --- | --- | --- | --- |
| Pitch accuracy | Share of the answer key's sounding frames where our pitch line is within 50 cents | ±50 cents, 10 ms frames | `melody.evaluate` → Raw Pitch Accuracy |
| Voicing recall / false alarm | Did we hear sound where there was sound, and not where there wasn't | — | `melody.evaluate` |
| Onset F1 | Note starts found, pitch ignored | ±50 ms | `transcription.onset_precision_recall_f1` |
| Note F1 | Notes right on start, pitch and end | onset ±50 ms, pitch ±50 cents, offset within 20% of the note's length or 50 ms, whichever is larger | `transcription.precision_recall_f1_overlap` |
| Note F1, no offsets | As above without the end rule | onset ±50 ms, pitch ±50 cents | same, `offset_ratio=None` |
| Beat F1 | Beats found | ±70 ms | `beat.f_measure` (only where the key has beats) |
| Seconds per minute | Compute time per minute of audio | — | wall clock |
| Note-count ratio | Our notes ÷ answer key's notes; >1 means splitting or extra notes | — | — |
| Edits per 100 notes | Hand edits to reach an accepted score | — | hand count, 10 fixed tunes (not automated yet) |

Notes on the definitions:
- Pitch accuracy gives every answer-key frame its note's fixed pitch, so deep
  vibrato and bends cost a little even when the pitch line is right. When
  sets with human-checked f0 (URMP, ChoraleBricks, Bach10) get f0 scoring,
  report both.
- F1 is the balance of precision (how many of ours are right) and recall (how
  many of theirs we found).
- Means are per-recording averages, not pooled over all notes.

## Targets

From the requirements doc; encoded in `score/card.py: TARGETS`.

| Metric | Solo | Full mix |
| --- | --- | --- |
| Pitch accuracy | 97% | 90% |
| Onset F1 | 90% | 75% |
| Note F1 | 80% | 60% |
| Beat F1 | 95% | 95% |
| Seconds per minute | 15 | 60 |
| Edits per 100 notes | 5 | 15 |

Which targets a set is held to: `omnibook` (stems already separated from
records), `omnibook-mix`, `urmp-mix`, `bach10-mix` use full-mix targets;
everything else uses solo targets.

## Test sets

| Set | Recordings | Horns | Kind | Targets |
| --- | --- | --- | --- | --- |
| `omnibook` | 46 | alto | separated jazz stems | mix |
| `omnibook-mix` | 46 | alto | jazz records through Demucs | mix |
| `urmp` / `urmp-mix` | 11 | alto/tenor *(per piece)* | classical parts / ensemble | solo / mix |
| `bach10` / `bach10-mix` | 10 | tenor-voice sax | chorale parts / quartet | solo / mix |
| `choralebricks` | 38 | alto, baritone | chorale parts | solo |
| `filosax` | ~48 tunes | tenor | jazz over backing tracks | solo (v1 gate) |
| `pairs` | any | any | Austin's takes with aligned MIDI | solo (v1 gate: 20 frozen takes) |

Splits: by tune via a hash (≈1 in 5 tunes to `test`), never by take.
Thresholds are tuned on train only. See [data/README.md](../data/README.md#splits-and-leakage).

## Reporting

Each log entry records: date, commit, machine, set, split, settings
(`--contour-tool`, `--notes-tool`), recordings scored, the metric means,
note-count ratio when known, and what it shows in one or two sentences.
Comparisons are on the same recordings with only one setting changed.

## Known limitations

- No f0-based pitch scoring yet, even where human-checked f0 exists.
- Beat F1 not yet surfaced in summaries.
- Edits per 100 notes is not measured until the editor exists.
- Filosax (the v1 gate set) not yet available.
