"""Head-to-head results: one line per (record, setup), for the Results page's comparison views.

The scorecard history (history.py) follows one pipeline over time. This file
holds the other axis: several setups (separator x where the sax-rest cuts come
from x note finder) run on the same records against the same answer keys.

  docs/evaluation/experiments.jsonl   in the repo: rows written up in the
                                      evaluation log (backfilled from it)
  <runs>/experiments.jsonl            on the Mac: every experiment script
                                      appends here with experiments.append()

A row:
  {"id": "...", "when": "2026-11-05T05:40:00Z", "entry": "E55", "commit": "abc1234",
   "set": "parker-band", "record": "6Cbwc",          # record null = whole-set row
   "setup": {"separator": "mega", "spans_from": "same", "note_finder": "ours"},
   "default": false,                                  # the app's current default setup?
   "scope": "key-span",                               # or "whole", "solo"
   "key": {"version": "stem-aligned", "heard_ok": 0.81},
   "n_key": 863, "n_est": 1105,
   "metrics": {"note_f1": 0.283, "note_f1_no_offset": ..., "onset_f1": ...,
               "onset_recall": ..., "onset_precision": ..., "pitch_accuracy": ...,
               "sax_found": ..., "sax_purity": ..., "octave_errors": ...},
   "cuts": {"seconds": 69.0, "key_notes_inside": 162},
   "seconds_per_minute": 210, "checkpoints": {"separator": "sha256:..."},   # optional
   "key_notes": {"right": .., "timing": .., "wrong_pitch": .., "merged": .., "hidden": .., "missed": ..},
   "our_notes": {"right": .., "timing": .., "wrong_pitch": .., "split": .., "in_rest": .., "extra": ..},
   "hidden_notes": {"in_key": .., "not_in_key": ..},
   "guards": {"extras_in_rests_per_min": .., "rest_seconds": .., "short_notes": .., ...},   # optional
   "bars": [{"bar": 17, "t0": 20.9, "key": 4, "right": 3, "hidden": 0, "ours": 5, "extra": 1, "cut": 0.0}, ...],
   "note": "..."}

Metrics are shares (0-1); the guard counts and rates (score/metrics.py)
go in guards, beside the shares they explain (short_found, ghost_found). Whole-set rows are note-count-weighted averages of
their records. key_notes, our_notes and bars come from classify(); a row
without them still shows in the comparison grid.

Where each answer-key note went (key_notes, each note counted once):
  right        found: onset within 50 ms, pitch within 50 cents (ends ignored)
  timing       our note has the pitch but starts 50-150 ms off
  wrong_pitch  our note starts within 50 ms on another pitch (octaves included,
               also counted alone as octave)
  merged       swallowed by our previous note on the same pitch (a re-tongued
               repeat we joined)
  (sax_found_heard: found among the key notes whose pitch the recording
  confirms (heard_ok), so the gap to sax_found is the key's share)
  hidden       we found it but tagged it not_sax (or it sits inside a sax-rest
               cut): the note is in notes.json but off the sheet
  missed       nothing of ours near it
Where each of our notes on the sheet came from (our_notes):
  right, timing, wrong_pitch   the partners of the key notes above
  split        an extra piece of a key note we already have (same pitch)
  in_rest      no key note is sounding: bleed or a ghost in a rest
  extra        any other extra note while the sax plays
"""
from __future__ import annotations

import bisect
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
REPO_EXPERIMENTS = REPO / "docs" / "evaluation" / "experiments.jsonl"
FILE_NAME = "experiments.jsonl"

KEY_KINDS = ("right", "timing", "wrong_pitch", "merged", "hidden", "missed")
OUR_KINDS = ("right", "timing", "wrong_pitch", "split", "in_rest", "extra")
ONSET = 0.05
LATE = 0.15
NOT_SAX = "not_sax"


def _hidden(n: dict) -> bool:
    return NOT_SAX in (n.get("tags") or [])


def _arrays(notes):
    if not notes:
        return np.zeros((0, 2)), np.zeros(0)
    iv = np.array([[n["onset"], max(n["offset"], n["onset"] + 0.01)] for n in notes])
    return iv, 440.0 * 2 ** ((np.array([n["pitch"] for n in notes], float) - 69) / 12)


def classify(key: list[dict], notes: list[dict], span: tuple[float, float] | None = None,
             cuts: list[tuple[float, float]] | None = None) -> dict:
    """Sort every answer-key note and every one of our notes into one kind each.

    key: [{onset, offset, pitch, bar?, heard_ok?}] (grace notes already left out).
    notes: notes.json's notes, hidden ones included (tags carry not_sax).
    span: only our notes starting inside it count (default: the key's span +- 0.5 s).
    cuts: the take's sax-rest cuts [(start, end)], for key notes lost with no note at all.
    """
    import mir_eval
    key = sorted(key, key=lambda n: n["onset"])
    if not key:
        return {}
    lo, hi = span or (key[0]["onset"] - 0.5, max(n["offset"] for n in key) + 0.5)
    ours = sorted((n for n in notes if lo <= n["onset"] < hi), key=lambda n: n["onset"])
    cuts = cuts or []
    ri, rp = _arrays(key)
    ei, ep = _arrays(ours)
    pairs = dict(mir_eval.transcription.match_notes(ri, rp, ei, ep, onset_tolerance=ONSET,
                                                    pitch_tolerance=50.0, offset_ratio=None)) if ours else {}
    used = set(pairs.values())
    kind_key: list[str] = [""] * len(key)
    kind_ours: dict[int, str] = {}
    octave = 0
    for i, j in pairs.items():
        if _hidden(ours[j]):
            kind_key[i] = "hidden"
        else:
            kind_key[i] = kind_ours[j] = "right"
    for i, k in enumerate(key):
        if kind_key[i]:
            continue
        on, p = k["onset"], k["pitch"]
        near = [j for j, n in enumerate(ours) if j not in used and abs(n["onset"] - on) <= ONSET]
        late = [j for j, n in enumerate(ours) if j not in used and abs(n["pitch"] - p) < 0.5
                and ONSET < abs(n["onset"] - on) <= LATE]
        if near:
            j = min(near, key=lambda x: (abs(ours[x]["pitch"] - p), abs(ours[x]["onset"] - on)))
            used.add(j)
            if _hidden(ours[j]):
                kind_key[i] = "hidden"
                continue
            kind_key[i] = kind_ours[j] = "wrong_pitch"
            octave += round(ours[j]["pitch"] - p) % 12 == 0
        elif late:
            j = min(late, key=lambda x: abs(ours[x]["onset"] - on))
            used.add(j)
            if _hidden(ours[j]):
                kind_key[i] = "hidden"
                continue
            kind_key[i] = kind_ours[j] = "timing"
        elif any(not _hidden(n) and abs(n["pitch"] - p) < 0.5 and n["onset"] < on - ONSET and n["offset"] > on
                 for n in ours):
            kind_key[i] = "merged"
        elif any(a <= on < b for a, b in cuts):
            kind_key[i] = "hidden"
        else:
            kind_key[i] = "missed"
    hidden_in_key = sum(1 for j, n in enumerate(ours) if _hidden(n) and j in used)
    for j, n in enumerate(ours):
        if j in kind_ours or _hidden(n):
            continue
        t = n["onset"]
        sounding = [k for k in key if k["onset"] - ONSET <= t < k["offset"]]
        if any(abs(k["pitch"] - n["pitch"]) < 0.5 for k in sounding):
            kind_ours[j] = "split"
        elif not sounding:
            kind_ours[j] = "in_rest"
        else:
            kind_ours[j] = "extra"
    out = {"n_key": len(key), "n_est": sum(not _hidden(n) for n in ours),
           "key_notes": {k: kind_key.count(k) for k in KEY_KINDS},
           "our_notes": {k: list(kind_ours.values()).count(k) for k in OUR_KINDS},
           "octave": octave,
           "hidden_notes": {"in_key": hidden_in_key,
                            "not_in_key": sum(_hidden(n) for n in ours) - hidden_in_key}}
    oks = [k["heard_ok"] for k in key if "heard_ok" in k]
    if oks:
        out["key_heard_ok"] = round(sum(map(bool, oks)) / len(oks), 4)
        heard = [kind for k, kind in zip(key, kind_key) if k.get("heard_ok")]
        if heard:  # found, counting only key notes the recording confirms: how much of a gap is the key
            out["found_heard"] = round(heard.count("right") / len(heard), 4)
    if all("bar" in k for k in key):
        out["bars"] = _bars(key, kind_key, ours, kind_ours, cuts)
    return out


def _bars(key, kind_key, ours, kind_ours, cuts) -> list[dict]:
    """Per-bar counts, bars without key notes (rests) included, their start times interpolated."""
    start: dict[int, float] = {}
    for k in key:
        start[k["bar"]] = min(start.get(k["bar"], k["onset"]), k["onset"])
    first, last = min(start), max(start)
    known = sorted(start)
    t0 = {}
    for b in range(first, last + 1):
        if b in start:
            t0[b] = start[b]
            continue
        lo = max(x for x in known if x < b)
        hi = min(x for x in known if x > b)
        t0[b] = start[lo] + (start[hi] - start[lo]) * (b - lo) / (hi - lo)
    bars = list(range(first, last + 1))
    times = [t0[b] for b in bars]
    rows = {b: {"bar": b, "t0": round(t0[b], 3), "key": 0, "right": 0, "hidden": 0, "ours": 0, "extra": 0,
                "cut": 0.0} for b in bars}
    for k, kind in zip(key, kind_key):
        r = rows[k["bar"]]
        r["key"] += 1
        r["right"] += kind == "right"
        r["hidden"] += kind == "hidden"
    for j, kind in kind_ours.items():
        b = bars[max(0, bisect.bisect_right(times, ours[j]["onset"]) - 1)]
        rows[b]["ours"] += 1
        rows[b]["extra"] += kind in ("split", "in_rest", "extra")
    end = max(k["offset"] for k in key)
    for n, b in enumerate(bars):
        a, z = times[n], times[n + 1] if n + 1 < len(times) else end
        if z > a and cuts:
            inside = sum(max(0.0, min(z, cb) - max(a, ca)) for ca, cb in cuts)
            rows[b]["cut"] = round(min(1.0, inside / (z - a)), 3)
    return [rows[b] for b in bars]


def row(set_name: str, record: str | None, setup: dict, metrics: dict, *, default: bool = False,
        breakdown: dict | None = None, scope: str = "key-span", key: dict | None = None,
        cuts: dict | None = None, entry: str | None = None, note: str | None = None) -> dict:
    """One results line. metrics as metrics.note_scores/pitch_scores give them (shares)."""
    from .history import git_commit
    when = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sha, _ = git_commit()
    label = "+".join(str(setup.get(k, "")) for k in ("separator", "spans_from", "note_finder"))
    rec = {"id": f"{when} {set_name} {record or 'all'} {label}", "when": when, "commit": sha,
           "set": set_name, "record": record, "setup": setup, "default": default, "scope": scope,
           "metrics": {k: round(float(v), 4) for k, v in metrics.items() if v is not None}}
    if breakdown:
        rec.update({k: breakdown[k] for k in ("n_key", "n_est", "key_notes", "our_notes", "hidden_notes", "bars")
                    if k in breakdown})
        if "found_heard" in breakdown:
            rec["metrics"].setdefault("sax_found_heard", breakdown["found_heard"])
        if "key_heard_ok" in breakdown:
            rec.setdefault("key", {})["heard_ok"] = breakdown["key_heard_ok"]
    if key:
        rec["key"] = {**rec.get("key", {}), **key}
    for k, v in (("cuts", cuts), ("entry", entry), ("note", note)):
        if v:
            rec[k] = v
    return rec


def append(rec: dict, runs: str | Path | None = None) -> Path:
    path = (Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs") / FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return path


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line) if line.strip() else None
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("set") and isinstance(rec.get("setup"), dict) \
                and isinstance(rec.get("metrics"), dict):
            out.append(rec)
    return out


def load(runs: str | Path | None = None) -> list[dict]:
    """The repo's rows plus this machine's, oldest first, each id once."""
    local = (Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs") / FILE_NAME
    seen, out = set(), []
    for rec in read(REPO_EXPERIMENTS) + read(local):
        rid = rec.get("id") or json.dumps([rec.get("when"), rec["set"], rec.get("record"), rec["setup"]])
        if rid in seen:
            continue
        seen.add(rid)
        rec["id"] = rid
        out.append(rec)
    return sorted(out, key=lambda r: r.get("when") or "")
