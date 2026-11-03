"""Rhythm scorecard: how well the notation layer writes rhythm, with no audio.

The Weimar Jazz Database (WJD) holds 456 jazz solos transcribed by hand: each
note's onset and length in seconds, the beat grid of the recording, and the
note's written place (bar, beat, and which of `division` slots in the beat,
`tatum`, counting from 1). That is exactly what the notation layer gets from
the layers below (note times and beats) and what it should write. So the
played times go into notation.quantize() with the WJD beats, and what comes
out is compared with the written places. No audio, no pitch tracker: only
the rhythm writing is tested.

Measures (per solo, then averaged over solos):
  position_exact  share of notes written on exactly the key's beat and slot
  slot_right      share on the right slot inside the beat (a beat slip still counts)
  beat_right      share in the right beat (any slot)
  triplet_ratio   our triplet starts / the key's (1.0 = as many; above = busier)
  sixteenth_ratio our sixteenth-or-finer starts / the key's
  busy_ratio      (triplets + sixteenths) ours / the key's
  notes_kept      notes written / notes in (must be 1.0: notation never drops a note)

The key's notes are grouped by rhythmfeel, style and tempoclass. Train and test
are split by performer, never by solo, so a player's habits are never on both
sides. Parker solos that are also in the Charlie Parker Omnibook are left out
(the same recorded solo; matched by shared pitch-interval 8-grams on the Mac,
2026-11-03), so a set scored alongside the Omnibook never sees one twice.

Run: python -m saxscribe rhythm [--split test] [--saxes] [--limit N]
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from .. import frontend
from ..layers import notation

SAXES = ("as", "ts", "ss", "bs")
OMNIBOOK_OVERLAP = {52, 53, 55, 58, 59, 60, 61, 63, 64, 66, 67, 68}   # WJD melids also in the Omnibook
GROUPS = ("rhythmfeel", "style", "tempoclass", "instrument")
MEASURES = ("position_exact", "slot_right", "beat_right", "triplet_ratio", "sixteenth_ratio",
            "busy_ratio", "notes_kept")


def wjd_path(override: str | None = None) -> Path:
    from .refs import config
    if override:
        return Path(override).expanduser()
    configured = config().get("data", {}).get("wjd")
    base = Path(configured).expanduser() if configured else Path.home() / "mir_datasets" / "WeimarJazzDatabase"
    return base / "wjazzd.db" if base.is_dir() else base


def performer_split(performer: str) -> str:
    """test for about one performer in five, train otherwise."""
    h = int(hashlib.md5(performer.encode()).hexdigest(), 16)
    return "test" if h % 5 == 0 else "train"


def load(db: Path, split: str = "all", saxes: bool = False) -> list[dict]:
    """Solos as {melid, info, notes: [{onset, offset, pitch, place}], beats, downbeats}.

    place is the written position in beats from the solo's first beat (a Fraction)."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    solos = []
    for info in con.execute("SELECT * FROM solo_info ORDER BY melid"):
        info = dict(info)
        if info["melid"] in OMNIBOOK_OVERLAP:
            continue
        if saxes and info["instrument"] not in SAXES:
            continue
        if split != "all" and performer_split(info["performer"] or "") != split:
            continue
        beat_rows = con.execute("SELECT onset, bar, beat FROM beats WHERE melid = ? ORDER BY onset",
                                (info["melid"],)).fetchall()
        where = {(r["bar"], r["beat"]): i for i, r in enumerate(beat_rows)}
        notes = []
        for r in con.execute("SELECT onset, duration, pitch, bar, beat, tatum, division FROM melody "
                             "WHERE melid = ? ORDER BY onset", (info["melid"],)):
            i = where.get((r["bar"], r["beat"]))
            if i is None or not r["division"]:
                continue   # a note outside the beat grid has no written place to check
            place = i + Fraction(int(r["tatum"]) - 1, int(r["division"]))
            notes.append({"onset": float(r["onset"]), "offset": float(r["onset"] + r["duration"]),
                          "pitch": int(round(r["pitch"])), "place": place})
        if len(notes) < 8 or len(beat_rows) < 4:
            continue
        solos.append({"melid": info["melid"], "info": info, "notes": notes,
                      "beats": [float(r["onset"]) for r in beat_rows],
                      "downbeats": [float(r["onset"]) for r in beat_rows if r["beat"] == 1]})
    con.close()
    return solos


def kind(x: Fraction) -> str:
    """What a start inside the beat needs: 'beat', 'eighth', 'triplet' or 'sixteenth' (or finer)."""
    d = (x % 1).denominator
    if d == 1:
        return "beat"
    if d == 2:
        return "eighth"
    if d % 3 == 0:
        return "triplet"
    return "sixteenth"


def ratio(ours: int, key: int) -> float:
    if key == 0:
        return 1.0 if ours == 0 else float(ours)
    return ours / key


def score_solo(solo: dict, swing: str = "auto") -> dict:
    """Quantize one solo's played notes on its own beats and compare with its written places."""
    notes, beats = solo["notes"], solo["beats"]
    tempo = solo["info"].get("avgtempo")
    result = notation.quantize(notes, beats, solo["downbeats"], tempo, swing)
    # quantize() counts beats along its own grid, which may have added beats
    # before the first WJD beat; find where WJD beat 0 sits on it.
    grid, _ = notation.repair_grid(beats, notes, tempo)
    first = int(np.argmin(np.abs(np.asarray(grid) - beats[0])))
    ours = {p["index"]: p["start"] - result["shift"] - first for p in result["notes"]}
    keys = [n["place"] for n in notes]
    got = [ours.get(i) for i in range(len(notes))]
    pairs = [(g, k) for g, k in zip(got, keys) if g is not None]
    kinds_ours = [kind(g) for g, _ in pairs]
    kinds_key = [kind(k) for k in keys]
    count = lambda ks, name: sum(k == name for k in ks)
    tri_o, tri_k = count(kinds_ours, "triplet"), count(kinds_key, "triplet")
    six_o, six_k = count(kinds_ours, "sixteenth"), count(kinds_key, "sixteenth")
    n = len(notes)
    return {
        "position_exact": sum(g == k for g, k in pairs) / n,
        "slot_right": sum((g % 1) == (k % 1) for g, k in pairs) / n,
        "beat_right": sum((g // 1) == (k // 1) for g, k in pairs) / n,
        "triplet_ratio": ratio(tri_o, tri_k),
        "sixteenth_ratio": ratio(six_o, six_k),
        "busy_ratio": ratio(tri_o + six_o, tri_k + six_k),
        "notes_kept": len(result["notes"]) / n,
        "notes": n, "swing": round(result["swing"], 3), "swing_source": result["swing_source"],
        "triplets": [tri_o, tri_k], "sixteenths": [six_o, six_k],
    }


def mean(rows: list[dict]) -> dict:
    return {m: round(float(np.mean([r[m] for r in rows])), 4) for m in MEASURES} if rows else {}


def card(solos: list[dict], swing: str = "auto") -> dict:
    rows = []
    for solo in solos:
        try:
            r = score_solo(solo, swing)
        except Exception as exc:   # one odd solo must not stop the card
            frontend.log(f"[saxscribe] could not score WJD melid {solo['melid']}: {exc}")
            continue
        r.update(melid=solo["melid"], performer=solo["info"]["performer"], title=solo["info"]["title"],
                 **{g: solo["info"].get(g) or "?" for g in GROUPS})
        rows.append(r)
    by = {g: {v: mean([r for r in rows if r[g] == v]) | {"n": sum(r[g] == v for r in rows)}
              for v in sorted({r[g] for r in rows})} for g in GROUPS}
    return {"items": len(rows), "mean": mean(rows), "by": by, "rows": rows}


def table(c: dict) -> str:
    pct = lambda x: f"{100 * x:5.1f}%"
    lines = [f"Rhythm scorecard, Weimar Jazz Database: {c['items']} solos",
             "", "measure           mean", "-" * 26]
    for m in MEASURES:
        v = c["mean"].get(m, 0.0)
        lines.append(f"{m:<17} {pct(v) if 'ratio' not in m else f'{v:6.2f}x'}")
    for g in GROUPS:
        lines += ["", f"by {g}:", f"{'':<14}{'n':>4} {'exact':>7} {'slot':>7} {'busy':>7}"]
        for v, m in c["by"][g].items():
            lines.append(f"{v[:14]:<14}{m['n']:>4} {pct(m['position_exact'])} {pct(m['slot_right'])} "
                         f"{m['busy_ratio']:6.2f}x")
    return "\n".join(lines)


def run(db: str | None = None, split: str = "all", saxes: bool = False, limit: int | None = None,
        runs: str | None = None, note: str | None = None, swing: str = "auto") -> dict:
    from . import history
    path = wjd_path(db)
    if not path.exists():
        raise SystemExit(f"No Weimar Jazz Database at {path} (set [data] wjd in config.local.toml or pass --data)")
    solos = load(path, split, saxes)[:limit] if limit else load(path, split, saxes)
    frontend.log(f"[saxscribe] Rhythm scorecard on {len(solos)} WJD solos ({split}{', saxes only' if saxes else ''})")
    c = card(solos, swing)
    name = "wjd-rhythm" + ("-sax" if saxes else "")
    c.update(set=name, split=split, settings="default" if swing == "auto" else f"swing={swing}")
    out_dir = (Path(runs).expanduser() if runs else history.default_runs()) / "rhythm"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if note:
        c["note"] = note
    (out_dir / f"{name}-{split}-{stamp}.json").write_text(json.dumps(c, indent=1, default=str) + "\n")
    print(table(c))
    frontend.log(f"[saxscribe] Wrote {out_dir / f'{name}-{split}-{stamp}.json'}")
    return c
