# ADR-0037: Head-to-head tests kept in their own data file

- **Date**: 2026-11-05
- **Status**: Accepted (PR #100 merged 2026-11-05)
- **Decided by**: Claude (dashboard and docs threads), for Austin's request (06:48 UTC) that the dashboard show the different approaches clearly
- **PR**: #100
- **Relates to**: [ADR-0025](0025-scorecard-history-files.md), [ADR-0016](0016-notation-never-drops-notes.md)

## Context
`results.jsonl` (ADR-0025) holds one line per scorecard run of a set, tracked over time. Tonight's tests compared several separators and note finders on the same records: Demucs, Mega, MVSep website, the hybrid, and Riley and Dixon's Filosax models (log E51–E59). Each setup was scored per record. A time series can't show that well, and stuffing it into `results.jsonl` would mix experiments into the history of the default pipeline.

## Decision
Head-to-head tests go in `docs/evaluation/experiments.jsonl`:
- One line per (record or set, setup).
- `setup` has three fields: `separator`, `spans_from` and `note_finder`.
- Each line also carries `default`, `scope`, `key` and `metrics`, plus the log `entry` it belongs to.
- Lines are copied from the Mac's `~/saxscribe-runs/experiments.jsonl` when the test is logged, or written from the log with `"source": "log"`.

This file is the fourth record kept in step with the log, after log.md, `results.jsonl` and `changes.json`. A logged head-to-head without its experiments rows is incomplete. Entry numbers come from the docs thread, so the log and the data files never disagree.

The Results page's comparison views read this file. A setup that finds 3 or more points fewer of the key's notes than the default is flagged as losing sax, whatever its F1, because dropping real playing breaks ADR-0016.

## Consequences
- The time panels stay about the default pipeline; experiments live beside them.
- Every head-to-head needs its rows written, in the same docs PR as its log entry.
- Rows backfilled from the log (`"source": "log"`) carry only the numbers in the log and approximate times.
