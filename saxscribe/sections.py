"""Sax sections: the stretches of a band recording where the sax plays, given by hand.

Austin types them when he adds a song ("3:45-4:21, 5:10-5:40"). Notes found
outside every section (plus PAD seconds either side) are tagged "not_sax" and
"outside_sections": kept in notes.json, left off the score, so the chart
shows rests there. Beats and bar lines still come from the whole recording.
"""
from __future__ import annotations

import re

PAD = 2.0  # s kept either side of a section, so a pickup or a late release is not cut
OUTSIDE = "outside_sections"


def seconds(text: str) -> float:
    """'3:45', '1:02:03', '225' or '225.5' -> seconds."""
    t = text.strip()
    if not re.fullmatch(r"\d+(:\d{1,2}(\.\d+)?){0,2}|\d+\.\d+", t):
        raise ValueError(f"'{text}' is not a time (use m:ss, e.g. 3:45)")
    parts = [float(p) for p in t.split(":")]
    if any(p >= 60 for p in parts[1:]):
        raise ValueError(f"'{text}': seconds and minutes go up to 59")
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def parse(text: str | None) -> list[list[float]]:
    """'3:45-4:21, 5:10-5:40' -> [[225.0, 261.0], [310.0, 340.0]], sorted, overlaps merged.
    Empty or None -> []."""
    if not text or not text.strip():
        return []
    out = []
    for chunk in re.split(r"[,;\n]+", text):
        if not chunk.strip():
            continue
        m = re.fullmatch(r"\s*([\d:.]+)\s*(?:-|–|—|to)\s*([\d:.]+)\s*", chunk)
        if not m:
            raise ValueError(f"'{chunk.strip()}' is not a section (use from-to, e.g. 3:45-4:21)")
        a, b = seconds(m.group(1)), seconds(m.group(2))
        if b <= a:
            raise ValueError(f"'{chunk.strip()}': the end comes before the start")
        out.append([a, b])
    out.sort()
    merged = []
    for a, b in out:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def text(sections: list[list[float]]) -> str:
    """[[225, 261]] -> '3:45-4:21' (the form parse() reads)."""
    def clock(s: float) -> str:
        m, sec = divmod(round(s), 60)
        return f"{m}:{sec:02d}"
    return ", ".join(f"{clock(a)}-{clock(b)}" for a, b in sections)


def inside(t: float, sections: list[list[float]], pad: float = PAD) -> bool:
    return any(a - pad <= t < b + pad for a, b in sections)


def tag(notes: list[dict], sections: list[list[float]], not_sax: str = "not_sax") -> int:
    """Tag the notes that start outside every section. Returns how many."""
    n = 0
    for note in notes:
        if not inside(note["onset"], sections):
            tags = note.setdefault("tags", [])
            for t in (not_sax, OUTSIDE):
                if t not in tags:
                    tags.append(t)
            n += 1
    return n
