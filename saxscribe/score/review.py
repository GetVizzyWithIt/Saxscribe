"""Match check results for the Results page's Needs review tab.

The match check (run on the Mac) writes one line per chart/recording pair to
<runs>/keys/match_report.jsonl: id, performer, tune, instrument, source, audio, key_json,
verdict (pass / check / reject), reason, heard_agree, coverage, length_s, expected_length_s,
tempo_jumps, sax_judge, in_training, checked. Austin's own verdicts go to a separate file,
<runs>/keys/match_review.jsonl, so the check can be rerun without losing them.

The benchmark is every pair whose key passed (or that Austin marked good), that Austin has not
marked wrong, and that no model trained on.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

REPORT = "match_report.jsonl"
VERDICTS = "match_review.jsonl"
AUSTIN = ("good", "wrong", "unsure")
AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aif", ".aiff", ".ogg"}


def keys_dir(runs: str | Path | None = None) -> Path:
    return (Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs") / "keys"


def _lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line) if line.strip() else None
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("id"):
            out.append(rec)
    return out


def in_benchmark(e: dict) -> bool:
    mine = e.get("austin_verdict")
    if mine == "wrong" or e.get("in_training"):
        return False
    return e.get("verdict") == "pass" or mine == "good"


def load(runs: str | Path | None = None) -> dict:
    """The latest report line per pair, with Austin's latest verdict on it."""
    folder = keys_dir(runs)
    entries: dict[str, dict] = {}
    for rec in _lines(folder / REPORT):
        entries[rec["id"]] = rec
    for v in _lines(folder / VERDICTS):
        if v["id"] in entries:
            entries[v["id"]]["austin_verdict"] = v.get("verdict")
            entries[v["id"]]["austin_note"] = v.get("note") or ""
            entries[v["id"]]["austin_when"] = v.get("when")
    out = list(entries.values())
    for e in out:
        e["benchmark"] = in_benchmark(e)
    return {"report": str(folder / REPORT), "exists": (folder / REPORT).exists(), "entries": out}


def save(runs: str | Path | None, pair_id: str, verdict: str | None, note: str = "") -> dict:
    """Append Austin's verdict on one pair. verdict None clears it."""
    if verdict is not None and verdict not in AUSTIN:
        raise ValueError(f"verdict must be one of {', '.join(AUSTIN)}")
    if not any(e["id"] == pair_id for e in load(runs)["entries"]):
        raise KeyError(pair_id)
    rec = {"id": pair_id, "verdict": verdict, "note": str(note)[:2000],
           "when": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    path = keys_dir(runs) / VERDICTS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def entry(runs: str | Path | None, pair_id: str) -> dict:
    for e in load(runs)["entries"]:
        if e["id"] == pair_id:
            return e
    raise KeyError(pair_id)


def resolve(runs: str | Path | None, value: str | None) -> Path | None:
    """A path from the report: absolute, ~, or relative to the runs folder (or its keys folder)."""
    if not value:
        return None
    p = Path(str(value)).expanduser()
    if p.is_absolute():
        return p if p.exists() else None
    base = keys_dir(runs).parent
    for cand in (base / p, base / "keys" / p):
        if cand.exists():
            return cand
    return None


def audio_path(runs: str | Path | None, pair_id: str) -> Path | None:
    """Only the audio file the report names for this pair, and only if it is audio."""
    p = resolve(runs, entry(runs, pair_id).get("audio"))
    return p if p is not None and p.suffix.lower() in AUDIO and p.is_file() else None


def key_notes(runs: str | Path | None, pair_id: str) -> list[dict]:
    """The key's notes as [{onset, offset, pitch}] in seconds and concert MIDI, for playing it along."""
    p = resolve(runs, entry(runs, pair_id).get("key_json"))
    if p is None or p.suffix.lower() != ".json":
        return []
    data = json.loads(p.read_text())
    notes = data.get("notes", []) if isinstance(data, dict) else data
    out = []
    for n in notes if isinstance(notes, list) else []:
        if not isinstance(n, dict):
            continue
        t0 = n.get("onset", n.get("start", n.get("time")))
        t1 = n.get("offset", n.get("end"))
        if t1 is None and t0 is not None and n.get("duration") is not None:
            t1 = float(t0) + float(n["duration"])
        pitch = n.get("pitch", n.get("midi"))
        if t0 is None or t1 is None or pitch is None:
            continue
        out.append({"onset": round(float(t0), 3), "offset": round(float(t1), 3), "pitch": float(pitch)})
    return sorted(out, key=lambda n: n["onset"])
