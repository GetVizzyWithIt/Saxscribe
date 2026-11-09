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

Since the play-along feedback redesign (2026-11-09) a flag covers a range of
bars (bar .. to), may be saved with no reason yet (a quick flag made while
the music plays, "to sort"), and carries the run it was made on:

  run, run_name  which run of the song the flag was made on. A re-run of the
               song (Run again) keeps every flag; flags from earlier runs show
               in the tracker with whether this run's notes there changed.
  looks_right  per run, the bars played through with no flag.

The file also goes to the Desktop folder with the sheet music (export.py),
and text() makes the short summary the page's "Copy for Claude" button copies.
"""
from __future__ import annotations

import functools
import json
import os
import threading
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
    # the big reasons, when no detail is picked
    "wrong_notes": "Wrong notes",
    "rhythm_feel": "Rhythm",
}
# The four big reasons on the flag screen; the categories above are optional detail under them.
GROUPS = {
    "wrong_notes": {"label": "Wrong notes", "hint": "missing, extra, pitch, octave…",
              "keys": ["missing", "extra", "pitch", "octave", "split", "merged"]},
    "rhythm_feel": {"label": "Rhythm", "hint": "timing, bar lines, swing…",
               "keys": ["timing", "rhythm", "barline", "feel"]},
    "not_sax": {"label": "Not sax", "hint": "piano, voice, guitar…", "keys": ["not_sax"]},
    "other": {"label": "Other", "hint": "say it in words", "keys": ["other"]},
}
ENGINES = {"standard": "Standard", "filosax": "Filosax test"}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def pitch_name(midi: float) -> str:
    m = int(round(midi))
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def path(folder: Path) -> Path:
    return folder / "flags.json"


def load(folder: Path) -> dict:
    p = path(folder)
    if not p.exists():
        return {"flags": []}
    data = json.loads(p.read_text())
    # Flags saved before runs were tracked belong to the run the file was last saved on.
    first = ((data.get("made_by") or {}).get("notes") or {}).get("made") or "earlier"
    for f in data.get("flags", []):
        f.setdefault("to", f["bar"])
        f.setdefault("run", first)
        f.setdefault("run_name", "Earlier run")
    return data


# The server answers requests on several threads, and the page can save a flag and the bars
# heard at the same moment: every read-change-write of flags.json holds this lock.
_LOCK = threading.RLock()


def _locked(fn):
    @functools.wraps(fn)
    def run(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    return run


def _write(folder: Path, data: dict) -> None:
    p = path(folder)
    tmp = p.with_name(f"flags.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(p)


def _clock_of(take: Take):
    """bar position (quarter notes from bar 1) -> seconds, from the play-along's timing map."""
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
    return at


def bar_context(take: Take, bar: int, picked: list[float], to: int | None = None) -> dict:
    """Where bars `bar`..`to` are in the recording, and the notes written in them.
    picked = quarter-note positions (from bar 1) of the notes tapped."""
    to = max(bar, to or bar)
    at = _clock_of(take)
    played = json.loads(take.notes.read_text())["notes"]
    nota = json.loads(take.notation.read_text())
    notes = []
    for n in nota["notes"]:
        if not bar <= n["bar"] <= to:
            continue
        q = (n["bar"] - 1) * BEATS_PER_BAR + float(Fraction(n["beat"])) - 1
        p = played[n["index"]]
        notes.append({"index": n["index"], "bar": n["bar"], "pitch": n["pitch"], "name": pitch_name(n["pitch"]),
                      "beat": n["beat"], "length_beats": n["length_beats"],
                      "onset": round(float(p["onset"]), 3), "offset": round(float(p["offset"]), 3),
                      "picked": any(abs(q - x) < 1e-3 for x in picked)})
    return {"start": round(at((bar - 1) * BEATS_PER_BAR), 3), "end": round(at(to * BEATS_PER_BAR), 3),
            "notes": notes}


def made_by(take: Take) -> dict:
    try:
        layers = json.loads(take.manifest.read_text()).get("layers", {})
    except (OSError, ValueError):
        return {}
    return layers


def run_info(take: Take, job: dict) -> dict:
    """This run of the song: an id that changes each time it is run again, and a label.
    The id is when the notes layer was made (take.json), else when the job finished."""
    layers = made_by(take)
    made = (layers.get("notes") or {}).get("made") or job.get("finished") or ""
    engine = job.get("engine", "standard")
    name = ENGINES.get(engine, engine.capitalize())
    tool = (layers.get("notes") or {}).get("tool")
    date = ""
    try:
        t = time.strptime(made[:19], "%Y-%m-%dT%H:%M:%S")
        date = f"{t.tm_mday} {time.strftime('%b', t)} {time.strftime('%H:%M', t)}"
    except ValueError:
        pass
    return {"id": made or "run", "name": name, "tool": tool or "", "date": date,
            "label": f"{name} · {date}" if date else name}


def clean(body: dict) -> dict:
    """The fields the page may set, checked. No categories and no text = a quick flag, to sort."""
    bar = int(body.get("bar", 0))
    if bar < 1:
        raise ValueError("bar must be 1 or more")
    to = int(body.get("to") or bar)
    if to < bar:
        raise ValueError("to must be the same bar or later")
    if to - bar > 400:
        raise ValueError("that range is too long")
    cats = [c for c in body.get("categories", []) if c in CATEGORIES]
    if body.get("categories") and not cats:
        raise ValueError("unknown category")
    scope = body.get("scope", "bar")
    if scope not in ("bar", "notes"):
        raise ValueError("scope must be bar or notes")
    picked = [float(q) for q in body.get("picked", [])] if scope == "notes" else []
    if scope == "notes" and not picked:
        scope = "bar"
    return {"bar": bar, "to": to, "categories": cats, "scope": scope, "picked": sorted(picked),
            "text": str(body.get("text", ""))[:2000], "view": str(body.get("view", ""))[:20]}


def _header(data: dict, take: Take, job: dict, folder: Path) -> dict:
    run = run_info(take, job)
    data.update({"title": job.get("title", ""), "artist": job.get("artist", ""),
                 "horn": job.get("horn", ""), "engine": job.get("engine", "standard"),
                 "take": folder.name, "made_by": made_by(take), "run": run})
    data.setdefault("flags", [])
    return run


@_locked
def save(folder: Path, take: Take, job: dict, body: dict, flag_id: str | None = None) -> dict:
    """Add a flag, or change flag_id (fields not sent stay as they were).
    With body["merge"] (a quick flag from the Flag button), a new flag that overlaps a flag
    of this run grows that flag instead. Returns the stored flag, with "undo": what to send
    to take it back ({"delete": id} or {"put": id, "body": the old range})."""
    data = load(folder)
    run = _header(data, take, job, folder)
    old = next((f for f in data["flags"] if f["id"] == flag_id), None) if flag_id else None
    if flag_id and old is None:
        raise KeyError(flag_id)
    if old:
        body = {**{k: old.get(k) for k in ("bar", "to", "categories", "scope", "picked", "text", "view")}, **body}
    fields = clean(body)
    undo: dict = {}
    if not old and body.get("merge"):
        hit = next((f for f in data["flags"] if f.get("run") == run["id"]
                    and not (fields["to"] < f["bar"] or fields["bar"] > f.get("to", f["bar"]))), None)
        if hit:
            old = hit
            undo = {"put": hit["id"], "body": {"bar": hit["bar"], "to": hit.get("to", hit["bar"])}}
            fields = {**{k: hit.get(k) for k in ("categories", "scope", "picked", "text", "view")},
                      "bar": min(hit["bar"], fields["bar"]), "to": max(hit.get("to", hit["bar"]), fields["to"])}
            fields["to"] = max(fields["to"], fields["bar"])
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    fid = old["id"] if old else uuid.uuid4().hex[:8]
    flag = {"id": fid, **fields,
            **bar_context(take, fields["bar"], fields["picked"], fields["to"]),
            "run": old.get("run", run["id"]) if old else run["id"],
            "run_name": old.get("run_name", run["label"]) if old else run["label"],
            "created": old["created"] if old else now, "updated": now}
    if old:
        data["flags"][data["flags"].index(old)] = flag
    else:
        data["flags"].append(flag)
        undo = {"delete": fid}
    data["flags"].sort(key=lambda f: (f["bar"], f["created"]))
    _write(folder, data)
    return {**flag, "undo": undo}


@_locked
def remove(folder: Path, flag_id: str) -> None:
    data = load(folder)
    keep = [f for f in data["flags"] if f["id"] != flag_id]
    if len(keep) == len(data["flags"]):
        raise KeyError(flag_id)
    data["flags"] = keep
    _write(folder, data)


@_locked
def heard(folder: Path, take: Take, job: dict, bars: list[int]) -> list[int]:
    """Bars played through on this run: stored per run under looks_right. The page sends
    every bar heard; bars with a flag are left out when it is read (looks_right())."""
    data = load(folder)
    run = _header(data, take, job, folder)
    got = {int(b) for b in bars if int(b) >= 1}
    lr = data.setdefault("looks_right", {})
    lr[run["id"]] = sorted(set(lr.get(run["id"], [])) | got)
    _write(folder, data)
    return lr[run["id"]]


def looks_right(data: dict, run_id: str) -> list[int]:
    flagged = {b for f in data.get("flags", []) if f.get("run", run_id) == run_id
               for b in range(f["bar"], f.get("to", f["bar"]) + 1)}
    return [b for b in data.get("looks_right", {}).get(run_id, []) if b not in flagged]


def sorted_flag(f: dict) -> bool:
    return bool(f.get("categories") or f.get("text"))


def compare(take: Take, f: dict) -> str:
    """A flag from an earlier run, against this run's written notes in the same stretch of the
    recording: "changed" (a note it had is gone, or a new one is written inside the stretch:
    listen to check it's fixed) or "same" (the same notes, so it is still wrong). A not-sax
    flag counts as changed when its notes are gone or now marked maybe-not-sax."""
    try:
        played = json.loads(take.notes.read_text())["notes"]
        nota = json.loads(take.notation.read_text())["notes"]
    except (OSError, ValueError, KeyError):
        return "same"
    from ..layers.notsax import MAYBE_NOT_SAX
    now = [(int(round(float(n["pitch"]))), float(played[n["index"]]["onset"]),
            MAYBE_NOT_SAX in (played[n["index"]].get("tags") or [])) for n in nota]

    def found(pitch: int, onset: float) -> list:
        return [x for x in now if x[0] == pitch and abs(x[1] - onset) <= 0.05]
    before = [(int(round(float(n["pitch"]))), float(n["onset"])) for n in f.get("notes", [])]
    if "not_sax" in f.get("categories", []):
        still = [b for b in before if any(not x[2] for x in found(*b))]
        return "changed" if before and not still else "same"
    if any(not found(*b) for b in before):
        return "changed"
    t0, t1 = f.get("start", 0.0) + 0.05, f.get("end", 0.0) - 0.05
    new = [x for x in now if t0 <= x[1] < t1 and not any(x[0] == b[0] and abs(x[1] - b[1]) <= 0.05 for b in before)]
    return "changed" if new else "same"


# ---- suggested stretches: notes the notes layer marked "maybe_not_sax" (layers/notsax.py)

ANSWERS = ("not_sax", "sax")


def suggestions(take: Take, data: dict) -> list[dict]:
    """Runs of bars holding notes marked maybe_not_sax, with Austin's answer if he gave one.
    The notes stay on the score; the answers become the test set for a rule that hides them."""
    try:
        played = json.loads(take.notes.read_text())["notes"]
        nota = json.loads(take.notation.read_text())["notes"]
    except (OSError, ValueError, KeyError):
        return []
    from ..layers.notsax import MAYBE_NOT_SAX
    count: dict[int, int] = {}
    for n in nota:
        if MAYBE_NOT_SAX in (played[n["index"]].get("tags") or []):
            count[n["bar"]] = count.get(n["bar"], 0) + 1
    out: list[dict] = []
    for bar in sorted(count):
        if out and bar - out[-1]["bars"][1] <= 2:  # one empty bar between still reads as one stretch
            out[-1]["bars"][1] = bar
            out[-1]["notes"] += count[bar]
        else:
            out.append({"bars": [bar, bar], "notes": count[bar]})
    answers = {tuple(r["bars"]): r["answer"] for r in data.get("reviewed", [])}
    for s in out:
        s["answer"] = answers.get(tuple(s["bars"]))
    return out


@_locked
def review(folder: Path, take: Take, job: dict, bars: list[int], answer: str) -> dict:
    """Store Austin's answer for a suggested stretch: "not_sax" (he hears another instrument)
    or "sax". Replaces an earlier answer for the same bars."""
    if answer not in ANSWERS:
        raise ValueError("answer must be not_sax or sax")
    a, b = int(bars[0]), int(bars[1])
    if a < 1 or b < a:
        raise ValueError("bars must be [first, last]")
    data = load(folder)
    _header(data, take, job, folder)
    first, last = bar_context(take, a, []), bar_context(take, b, [])
    entry = {"bars": [a, b], "answer": answer, "start": first["start"], "end": last["end"],
             "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    data["reviewed"] = [r for r in data.get("reviewed", []) if r["bars"] != [a, b]] + [entry]
    _write(folder, data)
    return entry


def clock(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


def bars_name(f: dict) -> str:
    to = f.get("to", f["bar"])
    return f"Bar {f['bar']}" if to == f["bar"] else f"Bars {f['bar']}-{to}"


def text(data: dict, run_id: str | None = None, status: dict | None = None) -> str:
    """A short summary to paste into a thread: this run's flags, then earlier runs' flags
    with whether this run changed the notes there (status: flag id -> changed|same)."""
    head = data.get("title", "") + (f" - {data['artist']}" if data.get("artist") else "")
    run = data.get("run") or {}
    run_id = run_id or run.get("id")
    cur = [f for f in data["flags"] if run_id is None or f.get("run", run_id) == run_id]
    past = [f for f in data["flags"] if f not in cur]
    todo = sum(not sorted_flag(f) for f in cur)
    lines = [f"Saxscribe flags: {head} ({data.get('horn', '')}, {data.get('engine', 'standard')} notes, "
             f"take {data.get('take', '')}, run {run.get('label', '?')}), {len(cur)} flagged"
             + (f", {todo} not sorted yet" if todo else "")]

    def one(f: dict) -> None:
        cats = ", ".join(CATEGORIES.get(c, c) for c in f["categories"]) or "not sorted yet"
        picked = [n["name"] for n in f["notes"] if n["picked"]]
        where = f"just notes {' '.join(picked)} (concert)" if picked else (
            "whole bar" if f.get("to", f["bar"]) == f["bar"] else "whole bars")
        line = f"- {bars_name(f)} ({clock(f['start'])}-{clock(f['end'])}): {cats}; {where}"
        if f.get("text"):
            line += f'. "{f["text"]}"'
        if status and f["id"] in status:
            line += "; this run: " + ("notes changed there" if status[f["id"]] == "changed" else "unchanged")
        written = " ".join(n["name"] for n in f["notes"]) or "(rest)"
        lines.append(line)
        lines.append(f"  written (concert): {written}")
    for f in cur:
        one(f)
    for r in data.get("reviewed", []):
        said = "not sax" if r["answer"] == "not_sax" else "sax"
        lines.append(f"- Bars {r['bars'][0]}-{r['bars'][1]} ({clock(r['start'])}-{clock(r['end'])}): "
                     f"suggested 'possibly not sax'; Austin says {said}")
    ok = looks_right(data, run_id) if run_id else []
    if ok:
        lines.append(f"- Looks right (played through, no flag): {len(ok)} bars")
    if past:
        lines.append("Earlier runs:")
        for f in past:
            lines.append(f"  (run {f.get('run_name', '?')})")
            one(f)
    return "\n".join(lines) + "\n"


def page(folder: Path, take: Take, job: dict) -> dict:
    """Everything the play-along's feedback parts show."""
    data = load(folder)
    run = run_info(take, job)
    data.setdefault("run", run)
    data["run"] = run
    cur = [f for f in data["flags"] if f.get("run") == run["id"]]
    past = [f for f in data["flags"] if f.get("run") != run["id"]]
    status = {f["id"]: compare(take, f) for f in past}
    past_out = [{**f, "status": status[f["id"]]} for f in past]
    for f in cur:
        f["sorted"] = sorted_flag(f)
    return {"flags": cur, "past": past_out, "run": run, "categories": CATEGORIES, "groups": GROUPS,
            "suggested": suggestions(take, data), "looks_right": looks_right(data, run["id"]),
            "heard": data.get("looks_right", {}).get(run["id"], []),
            "text": text({**data, "title": job.get("title", ""), "artist": job.get("artist", ""),
                          "horn": job.get("horn", ""), "engine": job.get("engine", "standard"),
                          "take": folder.name}, run["id"], status)}
