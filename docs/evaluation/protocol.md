# Evaluation protocol

How every number in the [evaluation log](log.md) is produced, so results are
comparable over time and with published work.

## Rule

A model or rule change is not done until it has a before-and-after scorecard
on the fixed sets, in the PR description and in the log (CLAUDE.md).

## How to run

```bash
python -m saxscribe score <set> [--split test] [--notes-tool X] [--contour-tool Y] [--limit N] [--runs DIR] [--note "..."] [--range-rules out|overtones|flag|off] [--tag altissimo]
```

Each run keeps its take folders under `~/saxscribe-runs/<set>/<settings>/`
(re-running a setting reuses lower layers) and writes `scorecard.md` and
`scorecard.json` with per-recording rows and means against the targets.
From PR #38 every run also appends one line (time, set, settings, means,
git commit, optional `--note` label such as a training session) to
`<runs>/results.jsonl`, by default `~/saxscribe-runs/results.jsonl`.
`--tag altissimo` (PR #69) scores only GRFIA takes carrying that technique tag; a run after a change to the pitch search range needs `--redo contour`.

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

**Guard metrics** (PR #106, on every scorecard). They sit beside note F1 and must not fall when note F1 rises, so a gain that comes from dropping or merging notes shows up (ADR-0016):

| Metric | What it measures | Tolerance | Code |
| --- | --- | --- | --- |
| Short notes found | Share of the key's notes under 0.12 s that we found (fast runs) | onset ±50 ms, pitch ±50 cents | `score/metrics.py: guard_scores` (PR #106) |
| Ghost notes found | Share of key notes marked `"ghost": true` that we found; only where the key marks them | as above | same |
| Notes in rests per minute | Our notes starting where the key has a rest (a gap of at least 0.25 s, no key note within 0.1 s), per minute of rest: bleed and ghosts | — | same |
| Onset F1 / note F1 at 100 ms | As above with a 100 ms onset window, note ends ignored. A big gap over the 50 ms figure means timing jitter, not missing notes | onset ±100 ms | `transcription` functions, `onset_tolerance=0.1` |

Notes on the definitions:
- Pitch accuracy gives every answer-key frame its note's fixed pitch, so deep
  vibrato and bends cost a little even when the pitch line is right. When
  sets with human-checked f0 (URMP, ChoraleBricks, Bach10) get f0 scoring,
  report both.
- F1 is the balance of precision (how many of ours are right) and recall (how
  many of theirs we found).
- Means are per-recording averages, not pooled over all notes.
- When an answer key covers only part of a recording (`Reference.partial`, e.g.
  Omnibook keys cover about one chorus), only notes and beats we found inside
  the key's span (first onset − 0.5 s to last offset + 0.5 s) are scored
  (PR #16, [ADR-0017](../decisions/0017-grade-within-answer-key-span.md)).

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

From E70 on, every entry's first line is `- **Headline**: ...`, one short
sentence with the outcome. `scripts/handbook.py` shows it in HANDBOOK.md's
"Latest experiments" table (falling back to the heading's parenthetical).

### Four records of the same runs, kept in step

| File | What it holds | Who writes it |
| --- | --- | --- |
| [log.md](log.md) | The readable record: one entry (E1, E2, ...) per run or finding, and the "Change by change" table | Docs thread |
| `results.jsonl` (in `docs/evaluation/`) | One JSON line per scorecard run, with an `id` and the log `entry` it belongs to. E2–E17 were backfilled by hand with approximate times (`"source": "log"`) | Copied from the Mac's `~/saxscribe-runs/results.jsonl` when a run is logged, same `id`, plus `"entry": "E18"` etc. |
| `changes.json` (in `docs/evaluation/`) | One object per model or pipeline change: `pr`, `merged` (UTC or null), `title`, `layer`, `sets` it was measured on, `measure`, `before`, `after`, `kept`, `entry`. A non-empty `sets` makes it a score-moving marker | Docs thread, mirroring the "Change by change" table row for row |
| `experiments.jsonl` (in `docs/evaluation/`) | One JSON line per (record, setup) for head-to-head tests: `setup` {separator, spans_from, note_finder}, `default`, `scope`, `key` {version, heard_ok}, `metrics`, guard counts and rates in a separate `guards` field (so `metrics` stays shares, PR #109), rhythm counts (`ref_bars`, `tempo_ratio`) in a separate `grid` field, and from `experiments.classify()` the error counts `key_notes` / `our_notes` and per-bar `bars`. E51–E59 backfilled from this log (`"source": "log"`); E64 and E66 rows from the Mac (2026-11-06). Set-level rows for E70–E74, E77 and E79 are in this file since PR #143, using the new setup names (`austin-6`, `parker-test`, `heldout-players`, `judge-test` and others); E80 rows come with PR #146. The earlier side files [e77-e79-rows.jsonl](e77-e79-rows.jsonl) and [e71-e74-summary.txt](e71-e74-summary.txt) are superseded and kept only as the raw originals. Rhythm metrics, all shares: `bars_right` (bars starting on the reference downbeat), `barline_precision` and `barline_f` (bar lines matched to the reference), `notes_in_place` (= the Weimar `position_read`) and `notes_exact` (= `position_exact`). Notation-only rows (`scope: "notation-only"`, e.g. the 444-solo `wjd` set) carry the standard `setup` keys, which don't apply to them. Set `tenor-tunes` in these rows is the same as `new-tunes` | Copied from the Mac's `~/saxscribe-runs/experiments.jsonl` (written with `saxscribe.score.experiments.row()` and `append()`) when a test is logged |

Two more files feed the dashboard (2026-11-13):

- `cards.json`: one card per experiment, in the shape the UAT review asked for: what changed, the problem, the hypothesis, the measure, the result, what we learned, the decision, and when to revisit. A new log entry adds its card in the same PR (test: `tests/test_cards_tags.py`).
- `benchmark_tags.json`: horn, style, era and (later) tempo for every benchmark song, so scores can be shown per cell. Drafted from the players and dates; `checked` turns true once Austin confirms a row. A song added to the benchmark gets its tags in the same PR.

The app's Results page (PR #38, `/results`) merges the repo's
`results.jsonl` with the Mac's, showing each run once, and draws
`changes.json` as markers ([ADR-0025](../decisions/0025-scorecard-history-files.md)).
A log entry without its `results.jsonl` line, or a table row without its
`changes.json` object, or a head-to-head entry without its `experiments.jsonl` rows, is incomplete ([ADR-0037](../decisions/0037-head-to-head-experiments-file.md)).

For band records, PR #90 (merged 2026-11-05) adds two plain-language measures to the Results page: **Sax found**, the share of the answer key's sax notes the tool wrote (note recall), and **Sax purity**, the share of the tool's notes that are sax in the key (note precision). They separate the two failures that separators trade against each other: losing real sax passages, and letting piano or bass in (log E51, E52).

The Results page's comparison views (setups compared, where the notes go, along the record) read `experiments.jsonl`. A setup that finds 3 or more points fewer of the key's notes than the default on a record is flagged there as losing sax, whatever its F1 (ADR-0016). `sax_found_heard` repeats sax found over only the key notes the recording confirms (`heard_ok`), to show how much of a gap is the key's.

## Stress scorecard

`python -m saxscribe stress <set> [--conditions ...]` (PR #106) scores the same set again under conditions that break transcription on real records, moving the answer key with the audio where needed:

| Condition | What it does |
| --- | --- |
| clean | The recording as is (baseline) |
| detune ±25 / ±50 | Off-speed transfer: pitch moves by that many cents and every time stretches by the same factor. Old jazz records run off speed (Weimar tuning ranges 428–453 Hz) |
| reverb | A 1.2 s synthetic hall, 35% wet |
| lofi | 80 Hz–5 kHz band limit plus hiss 20 dB below the music |

The reverb and hiss use their own seeds, so a model later trained with reverb or noise is not tested on the same sounds. Writes `stress.md` and `stress.json` under `<runs>/stress/<set>/`, adds one `results.jsonl` line per condition, and for GRFIA gives clean scores by technique tag.

## Rhythm scorecard (Weimar, no audio)

`python -m saxscribe rhythm` (PR #53) scores Layer 4 alone. It feeds the
Weimar Jazz Database's exact note timings and beats through the notation step
and compares the written rhythm with the Weimar transcription, so no audio
and no transcription errors are involved.

| Measure | Meaning |
| --- | --- |
| Exact position | Note written at the same position in the bar as the transcription |
| Right slot | Same grid slot (eighth, triplet, sixteenth) |
| Right beat | Same beat, slot may differ |
| Triplet / sixteenth / busy ratios | How often we write triplets, sixteenths or crowded beats compared with the transcription |
| Notes kept | Notes written ÷ notes given (must be 100%, [ADR-0016](../decisions/0016-notation-never-drops-notes.md)) |

Split: train/test by performer. Excluded: 12 Parker solos that are also in
the Omnibook (Weimar melids 52, 53, 55, 58–61, 63, 64, 66–68), so rhythm
tuning never sees an Omnibook solo.

## Known limitations

- No f0-based pitch scoring yet, even where human-checked f0 exists.
- Beat F1 not yet surfaced in summaries.
- Edits per 100 notes is not measured until the editor exists.
- Filosax (the v1 gate set) not yet available.
