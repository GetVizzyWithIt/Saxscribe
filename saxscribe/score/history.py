"""The results history behind the dashboard: one line per scorecard run.

Two files, same format (JSON Lines, one run per line):

  docs/evaluation/results.jsonl   in the repo: runs written up in the evaluation
                                  log, backfilled from it and kept with it
  <runs>/results.jsonl            on the machine that runs scorecards
                                  (default ~/saxscribe-runs): every
                                  `python -m saxscribe score` appends here by
                                  itself, so a run shows on the dashboard at once

docs/evaluation/changes.json lists the model and pipeline changes (one per PR)
that the dashboard draws as markers. It mirrors the "Change by change" table at
the top of docs/evaluation/log.md.

A run line:
  {"id": "2026-11-03T05:12:40Z omnibook default", "when": "2026-11-03T05:12:40Z",
   "set": "omnibook", "split": "all", "settings": "default", "default": true,
   "items": 45, "metrics": {"note_f1": 0.642, ...}, "commit": "5e92192",
   "source": "scorecard", "note": "..."}

"default" says whether the run used the pipeline's default tools at the time,
which is what the dashboard joins into a trend line. Metrics are shares (0-1)
except seconds_per_minute. Extra metrics a set needs (key_accuracy) sit
alongside the scorecard's.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPO_RESULTS = REPO / "docs" / "evaluation" / "results.jsonl"
CHANGES = REPO / "docs" / "evaluation" / "changes.json"
FILE_NAME = "results.jsonl"


def default_runs() -> Path:
    return Path.home() / "saxscribe-runs"


def git_commit() -> tuple[str | None, bool]:
    """The short commit this code is at, and whether there are uncommitted changes."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                             text=True, timeout=5).stdout.strip() or None
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO,
                                    capture_output=True, text=True, timeout=5).stdout.strip())
        return sha, dirty
    except (OSError, subprocess.SubprocessError):
        return None, False


def record(card: dict, note: str | None = None) -> dict:
    """A results line for one scorecard (as card.run makes it)."""
    when = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sha, dirty = git_commit()
    rec = {"id": f"{when} {card['set']} {card['settings']}", "when": when, "set": card["set"],
           "split": card.get("split", "all"), "settings": card["settings"],
           "default": card["settings"] == "default", "items": card["items"],
           "metrics": card["mean"], "commit": sha, "source": "scorecard"}
    if dirty:
        rec["dirty"] = True
    if note:
        rec["note"] = note
    return rec


def append(rec: dict, runs: str | Path | None = None) -> Path:
    path = Path(runs).expanduser() / FILE_NAME if runs else default_runs() / FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return path


def read(path: Path) -> list[dict]:
    """Every run in one file; a broken line is skipped, not fatal."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("set") and rec.get("when") and isinstance(rec.get("metrics"), dict):
            out.append(rec)
    return out


def load(runs: str | Path | None = None) -> list[dict]:
    """The repo's history plus this machine's, oldest first, each run once."""
    local = (Path(runs).expanduser() if runs else default_runs()) / FILE_NAME
    seen, out = set(), []
    for rec in read(REPO_RESULTS) + read(local):
        rid = rec.get("id") or f"{rec['when']} {rec['set']} {rec.get('settings')}"
        if rid in seen:
            continue
        seen.add(rid)
        rec.setdefault("id", rid)
        out.append(rec)
    return sorted(out, key=lambda r: r["when"])


def changes() -> list[dict]:
    if not CHANGES.exists():
        return []
    return json.loads(CHANGES.read_text()).get("changes", [])


def dashboard_data(runs: str | Path | None = None) -> dict:
    from .card import MIX_SETS, TARGETS
    return {"runs": load(runs), "changes": changes(),
            "targets": {k: {"solo": v[0], "mix": v[1]} for k, v in TARGETS.items()},
            "mix_sets": sorted(MIX_SETS)}
