"""Bars Austin flags for review in the play-along, saved next to the take.

One file per upload, <library>/<id>/flags.json, written each time a flag is
saved. Flags are notes for review only: they never change the transcription.

Each flag is stored with what the page sent (bar, categories, which notes,
free text) plus what the tool had there, filled in on the server so a later
review doesn't need the app running:

  start, end   the bar's place in the recording, in seconds (from the same
               timing map the play-along uses). Review lines flags up with an
               answer key by time, because our bar numbers can differ from
               the key's.
  notes        every written note in the bar: its index in notes.json, concert
               pitch (MIDI), beat, length in beats, onset and offset in seconds,
               and whether it was one of the notes tapped.
  made_by      the tools that made the take (from take.json), so a flag on an
               old take reads against the code that made it.

The file also goes to the Desktop folder with the sheet music (export.py),
and text() makes the short summary the page's "Copy for Claude" button copies.
"""
from __future__ import annotations

import json
import time
import uuid
from fractions import Fraction
from pathlib import Path

from ..layers.notation import BEATS_PER_BAR
from ..take import Take

# key -> words on the page. The order is the order of the buttons.
CATEGORIES = {
    "missing": "Missing note",
    "extra": "Extra note",
    "pitch": "Wrong pitch",
    "octave": "Wrong octave",
    "split": "Held note split in two",
    "merged": "Notes merged into one",
    "timing": "Timing off",
    "rhythm": "Rhythm written wrong",
    "barline": "Bar line off / half time",
    "feel": "Swing or feel wrong",
    "not_sax": "Not sax (piano, band)",
    "other": "Other",
}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def pitch_name(midi: float) -> str:
    m = int(round(midi))
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def path(folder: Path) -> Path:
    return folder / "flags.json"


def load(folder: Path) -> dict:
    p = path(folder)
    if p.exists():
        return json.loads(p.read_text())
    return {"flags": []}


def _write(folder: Path, data: dict) -> None:
    p = path(folder)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(p)


def bar_context(take: Take, bar: int, picked: list[float]) -> dict:
    """Where bar `bar` is in the recording, and the notes written in it.
    picked = quarter-note positions (from bar 1) of the notes tapped."""
    from .score_view import sync
    pairs = sync(take)
    qs = [q for q, _ in pairs]
    ts = [t for _, t in pairs]

    def at(q: float) -> float:
        if len(qs) < 2:
            return ts[0] if ts else 0.0
        i = max(1, min(len(qs) - 1, next((k for k, x in enumerate(qs) if x > q), len(qs) - 1)))
        lo, hi = i - 1, i
        return ts[lo] + (q - qs[lo]) * (ts[hi] - ts[lo]) / (qs[hi] - qs[lo])

    q0 = (bar - 1) * BEATS_PER_BAR
    played = json.loads(take.notes.read_text())["notes"]
    nota = json.loads(take.notation.read_text())
    notes = []
    for n in nota["notes"]:
        if n["bar"] != bar:
            continue
        q = q0 + float(Fraction(n["beat"])) - 1
        p = played[n["index"]]
        notes.append({"index": n["index"], "pitch": n["pitch"], "name": pitch_name(n["pitch"]),
                      "beat": n["beat"], "length_beats": n["length_beats"],
                      "onset": round(float(p["onset"]), 3), "offset": round(float(p["offset"]), 3),
                      "picked": any(abs(q - x) < 1e-3 for x in picked)})
    return {"start": round(at(q0), 3), "end": round(at(q0 + BEATS_PER_BAR), 3), "notes": notes}


def made_by(take: Take) -> dict:
    try:
        layers = json.loads(take.manifest.read_text()).get("layers", {})
    except (OSError, ValueError):
        return {}
    return layers


def clean(body: dict) -> dict:
    """The fields the page may set, checked."""
    bar = int(body.get("bar", 0))
    if bar < 1:
        raise ValueError("bar must be 1 or more")
    cats = [c for c in body.get("categories", []) if c in CATEGORIES]
    if not cats:
        raise ValueError("pick at least one category")
    scope = body.get("scope", "bar")
    if scope not in ("bar", "notes"):
        raise ValueError("scope must be bar or notes")
    picked = [float(q) for q in body.get("picked", [])] if scope == "notes" else []
    if scope == "notes" and not picked:
        scope = "bar"
    return {"bar": bar, "categories": cats, "scope": scope, "picked": sorted(picked),
            "text": str(body.get("text", ""))[:2000], "view": str(body.get("view", ""))[:20]}


def save(folder: Path, take: Take, job: dict, body: dict, flag_id: str | None = None) -> dict:
    """Add a flag, or replace flag_id. Returns the stored flag."""
    fields = clean(body)
    data = load(folder)
    data.update({"title": job.get("title", ""), "artist": job.get("artist", ""),
                 "horn": job.get("horn", ""), "engine": job.get("engine", "standard"),
                 "take": folder.name, "made_by": made_by(take)})
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    old = next((f for f in data["flags"] if f["id"] == flag_id), None) if flag_id else None
    if flag_id and old is None:
        raise KeyError(flag_id)
    flag = {"id": flag_id or uuid.uuid4().hex[:8], **fields,
            **bar_context(take, fields["bar"], fields["picked"]),
            "created": old["created"] if old else now, "updated": now}
    if old:
        data["flags"][data["flags"].index(old)] = flag
    else:
        data["flags"].append(flag)
    data["flags"].sort(key=lambda f: (f["bar"], f["created"]))
    _write(folder, data)
    return flag


def remove(folder: Path, flag_id: str) -> None:
    data = load(folder)
    keep = [f for f in data["flags"] if f["id"] != flag_id]
    if len(keep) == len(data["flags"]):
        raise KeyError(flag_id)
    data["flags"] = keep
    _write(folder, data)


def clock(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


def text(data: dict) -> str:
    """A short summary to paste into a thread."""
    head = data.get("title", "") + (f" - {data['artist']}" if data.get("artist") else "")
    lines = [f"Saxscribe flags: {head} ({data.get('horn', '')}, {data.get('engine', 'standard')} notes, "
             f"take {data.get('take', '')}), {len(data['flags'])} flagged"]
    for f in data["flags"]:
        cats = ", ".join(CATEGORIES[c] for c in f["categories"])
        picked = [n["name"] for n in f["notes"] if n["picked"]]
        where = f"just notes {' '.join(picked)} (concert)" if picked else "whole bar"
        line = f"- Bar {f['bar']} ({clock(f['start'])}-{clock(f['end'])}): {cats}; {where}"
        if f.get("text"):
            line += f'. "{f["text"]}"'
        written = " ".join(n["name"] for n in f["notes"]) or "(rest)"
        lines.append(line)
        lines.append(f"  written (concert): {written}")
    return "\n".join(lines) + "\n"
