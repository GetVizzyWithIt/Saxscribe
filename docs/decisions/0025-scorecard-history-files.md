# ADR-0025: Scorecard history kept as data files beside the log

- **Date**: 2026-11-03
- **Status**: Accepted (PR #38 merged)
- **Decided by**: Claude (dashboard thread), for Austin's request to see model performance over time
- **PR**: #38

## Context
Austin wants to see how scores move from change to change. The evaluation
log is written for people; a chart needs the same numbers as data. Scorecard
runs on the Mac were recorded only in each run's `scorecard.json` and by hand
in the log.

## Decision
- Every `python -m saxscribe score` run appends one line to
  `<runs>/results.jsonl` (time, set, settings, means, git commit, optional
  `--note` label for training sessions).
- The repo keeps `docs/evaluation/results.jsonl` (runs that have a log entry,
  each tagged with its E-number) and `docs/evaluation/changes.json` (the
  change-by-change table as data).
- The app's Results page merges the repo file with the Mac's, each run once
  by `id`, and plots per-set history with a marker per change.
- [log.md](../evaluation/log.md) stays the readable record. The three are
  kept in step as described in the [protocol](../evaluation/protocol.md#three-records-of-the-same-runs-kept-in-step).

## Consequences
- Every run is recorded automatically, including ones nobody logged, with the
  commit that produced it ([ADR-0004](0004-mir-eval-scorecard.md) gets a
  machine-checked trail).
- E2–E17 were backfilled by hand; their times are approximate and marked
  `"source": "log"`.
- Two places to update per logged run and per change; a missing line shows up
  as a gap on the Results page.
- Training runs can be labelled with `--note`, so fine-tunes appear on the
  same charts as rule changes.
