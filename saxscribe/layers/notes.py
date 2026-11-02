"""Layer 3: note events, plus the beat grid.

notes.json holds:
  notes      [{onset, offset, pitch, cents, amp, tags}] in seconds and concert
             MIDI numbers. cents is how far the pitch line sat from that note
             (median over the note, +30 = 30 cents sharp). tags is for
             articulations (slur, scoop, fall, ...) and is empty until Phase 1.
  beats, downbeats, tempo_bpm   from the full source, so a band's groove counts
  key        not filled in yet (step 2)

Note tools (--notes-tool):
  basic_pitch  Spotify's Basic Pitch on the stem (the default when installed)
  segment      the pitch line cut into notes after the CREPE Notes method (segment.py)
  contour      a simpler cutter on the pitch line: a new note wherever the pitch
               settles somewhere new or the stem has a clear new attack
"""
from __future__ import annotations

import json

import numpy as np

from .. import LAYOUT_VERSION, frontend
from ..horns import Horn
from ..take import Take
from . import contour as contour_layer

SAME_START = 0.03  # two notes starting closer than this are one attack


def run(take: Take, horn: Horn, tool: str = "auto") -> None:
    frontend.log("Layer 3/4: note events and beats")
    line = contour_layer.read(take.contour)
    if tool in ("auto", "basic_pitch") and frontend.basic_pitch_available():
        notes, name = one_line(frontend.basic_pitch_notes(take.stem, horn.min_hz, horn.max_hz)), "basic_pitch"
    elif tool == "basic_pitch":
        raise SystemExit("Basic Pitch is not installed; use --notes-tool segment or install it.")
    elif tool == "segment":
        from . import segment
        y = frontend.load_mono(take.stem, sr=contour_layer.RATE)
        level, attacks = segment.envelopes(y, contour_layer.RATE, len(line["time"]))
        notes, name = segment.segment(line, level, attacks), "segment"
    else:
        onsets = frontend.detect_onsets(frontend.load_mono(take.stem))
        notes, name = from_contour(line, onsets), "contour"
    for n in notes:
        n["cents"] = cents_off(line, n)
        n["tags"] = []
    beats, downbeats, beat_tool = frontend.detect_beats(take.source)
    data = {
        "layout_version": LAYOUT_VERSION,
        "horn": horn.name,
        "pitch": "concert",
        "tools": {"notes": name, "beats": beat_tool},
        "tempo_bpm": tempo(beats),
        "key": None,
        "beats": [round(b, 4) for b in beats],
        "downbeats": [round(d, 4) for d in downbeats],
        "notes": [{"onset": round(n["onset"], 4), "offset": round(n["offset"], 4),
                   "pitch": int(n["pitch"]), "cents": n["cents"],
                   "amp": round(float(n.get("amp", 0.5)), 3), "tags": n["tags"]} for n in notes],
    }
    take.notes.write_text(json.dumps(data, indent=1) + "\n")
    take.record("notes", tool=name, beats=beat_tool)
    frontend.log(f"  {name}: {len(notes)} notes; {beat_tool}: {len(beats)} beats")


def one_line(notes: list[dict]) -> list[dict]:
    """A sax plays one note at a time: drop doubled attacks and cut overlaps.

    When two notes start at the same moment, keep the louder one (the other is
    usually an octave or a harmonic). A note that is still ringing when the
    next one starts ends there. Nothing else is removed.
    """
    out: list[dict] = []
    for n in sorted(notes, key=lambda n: n["onset"]):
        if out and n["onset"] - out[-1]["onset"] < SAME_START:
            if n.get("amp", 0) > out[-1].get("amp", 0):
                out[-1] = dict(n)
            continue
        out.append(dict(n))
    for a, b in zip(out, out[1:]):
        a["offset"] = min(a["offset"], b["onset"])
    return [n for n in out if n["offset"] > n["onset"]]


def from_contour(line: dict, onsets: list[dict]) -> list[dict]:
    """Notes cut from the pitch line (adapted from the game's vocal transcriber).

    A new note starts where the line settles on a pitch more than 0.8 semitone
    away, or where the stem has a clear attack (a tongued repeat on one pitch).
    """
    import scipy.signal
    times, midi = line["time"], np.where(line["voiced"], line["midi"], np.nan)
    filled = np.where(np.isnan(midi), 0.0, midi)
    smooth = np.where(np.isnan(midi), np.nan, scipy.signal.medfilt(filled, 5))  # 50 ms: smooths vibrato
    attacks = np.array([o["t"] for o in onsets if o["s"] >= 0.3])
    step = float(times[1] - times[0]) if len(times) > 1 else 0.01
    notes: list[dict] = []
    start, values = None, []

    def close(k_end):
        if start is None or len(values) < 4:  # under 40 ms: a slide, not a note
            return
        notes.append({"onset": float(times[start]), "offset": float(times[k_end]) + step,
                      "pitch": int(round(float(np.median(values)))),
                      "amp": float(np.clip(np.nanmean(line["confidence"][start:k_end + 1]), 0.2, 1.0))})

    for k in range(len(times)):
        m = smooth[k]
        if np.isnan(m):
            close(k - 1)
            start, values = None, []
            continue
        if start is None:
            start, values = k, [m]
            continue
        ref = float(np.median(values[-6:]))
        attack = len(attacks) and len(values) >= 6 and np.min(np.abs(attacks - times[k])) < step / 2
        if abs(m - ref) > 0.8 or attack:
            close(k - 1)
            start, values = k, [m]
        else:
            values.append(m)
    close(len(times) - 1)
    return notes


def cents_off(line: dict, note: dict) -> float | None:
    """Median distance of the pitch line from the note's pitch, in cents.

    Skips the first and last 20 ms, where scoops and releases live.
    """
    t = line["time"]
    mask = (t >= note["onset"] + 0.02) & (t < note["offset"] - 0.02) & line["voiced"]
    vals = line["midi"][mask]
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return None
    return round(float(np.median(vals - note["pitch"])) * 100, 1)


def tempo(beats: list[float]) -> float | None:
    if len(beats) < 2:
        return None
    return round(60.0 / float(np.median(np.diff(beats))), 2)


def read(take: Take) -> dict:
    return json.loads(take.notes.read_text())
