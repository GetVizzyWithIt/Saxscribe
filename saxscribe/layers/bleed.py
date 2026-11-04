"""Band records only: notes the sax's own pitch line does not back up.

On a band record the sax stem still carries some piano, bass and guitar. The
pitch line (layer 2) follows the strongest single voice, which is the sax
whenever it plays. Two checks use it, and both only tag: a tagged note is kept
in notes.json with "not_sax" (left off the score and the scorecard) plus a tag
that says why.

  no_pitch_line  the line is unvoiced for GAP seconds or more in a row, so the
                 sax is laying out (a piano solo the sax-span cut missed). On
                 Pennies From Heaven: 3:42-4:21, 65 notes, every one piano.
  off_line       the line is clearly voiced through the note but never on its
                 pitch (or an octave from it), and mostly a semitone or more
                 away: the sax is holding another note and this one is bleed.

Measured 2026-11-04 (offline_exp.py, existing runs, against the keys): note
F1 Pennies 49.2 -> 49.8, Parker band records 57.6 -> 57.8, BFMJ 56.0 -> 56.2;
0 or 1 real key note hidden per set. Solo sets are not touched.
"""
from __future__ import annotations

import numpy as np

NOT_SAX = "not_sax"
GAP = 8.0          # s of unvoiced pitch line: the sax is out
VOICED = 0.8       # share of a note's frames the line must be voiced for off_line
AWAY = 0.6         # share of those frames more than a semitone off the note
EDGE = 0.02        # s skipped at each end of a note


def silent_spans(line: dict, gap: float = GAP) -> list[tuple[float, float]]:
    """Stretches where the pitch line is unvoiced for at least gap seconds."""
    v = line["voiced"] & np.isfinite(line["midi"])
    t = line["time"]
    spans, start = [], None
    for i, on in enumerate(v):
        if not on and start is None:
            start = float(t[i])
        elif on and start is not None:
            if t[i] - start >= gap:
                spans.append((start, float(t[i])))
            start = None
    if start is not None and len(t) and t[-1] - start >= gap:
        spans.append((start, float(t[-1]) + 1.0))
    return spans


def off_line(note: dict, line: dict) -> bool:
    t = line["time"]
    m = (t >= note["onset"] + EDGE) & (t < max(note["offset"] - EDGE, note["onset"] + 0.05))
    if m.sum() < 3:
        return False
    v = line["voiced"][m] & np.isfinite(line["midi"][m])
    if v.mean() < VOICED:
        return False
    d = line["midi"][m][v] - note["pitch"]
    on = (np.abs(d) <= 0.5) | (np.abs(np.abs(d) - 12) <= 0.5)
    return not on.any() and (np.abs(d) > 1.0).mean() >= AWAY


def tag(notes: list[dict], line: dict) -> dict:
    """Tag bleed in place (notes not already not_sax). Returns counts."""
    spans = silent_spans(line)
    counts = {"no_pitch_line": 0, "off_line": 0, "silent_spans": [[round(a, 2), round(b, 2)] for a, b in spans]}
    for n in notes:
        tags = n.setdefault("tags", [])
        if NOT_SAX in tags:
            continue
        why = ("no_pitch_line" if any(a <= n["onset"] < b for a, b in spans)
               else "off_line" if off_line(n, line) else None)
        if why:
            tags += [why, NOT_SAX]
            counts[why] += 1
    return counts
