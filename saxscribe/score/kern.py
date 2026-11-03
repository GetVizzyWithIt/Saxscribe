"""A small reader for Humdrum **kern scores with one melody spine (GRFIA-RealSax).

Reads notes as [{start, end, pitch}] in quarter notes from the first note,
with ties joined, plus the time signature, tempo and transposition tag.
Pitch is the kern pitch as written in the file (c = middle C = MIDI 60);
the caller decides what that means (in GRFIA-RealSax it is concert + 12).

Covers what the dataset uses: durations with dots and tuplet numbers (12 =
triplet eighth), accidentals, rests, ties ([ _ ]), chords (top note kept),
barlines, grace notes (skipped), and beam or editorial marks (ignored).
"""
from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

TOKEN = re.compile(r"(?P<dur>\d+)(?P<dots>\.*)")
PITCH = re.compile(r"(?P<name>([a-gA-G])\2*)(?P<acc>#+|-+|n)?")
STEP = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def duration(token: str) -> Fraction | None:
    m = TOKEN.search(token)
    if not m:
        return None
    n = int(m.group("dur"))
    base = Fraction(8) if n == 0 else Fraction(4, n)  # 0 is a breve
    dots = len(m.group("dots"))
    return base * (2 - Fraction(1, 2 ** dots))


def midi(token: str) -> int | None:
    m = PITCH.search(token)
    if not m:
        return None
    name = m.group("name")
    letter = name[0].lower()
    if name[0].islower():
        octave = 4 + len(name) - 1
    else:
        octave = 3 - (len(name) - 1)
    acc = m.group("acc") or ""
    shift = acc.count("#") - acc.count("-")
    return 12 * (octave + 1) + STEP[letter] + shift


def parse(text: str) -> dict:
    """{notes: [{start, end, pitch}], meter, tempo, transposition} from kern text."""
    notes: list[dict] = []
    t = Fraction(0)
    meter, tempo, trans = None, None, None
    open_tie: dict | None = None
    for raw in text.splitlines():
        line = raw.split("\t")[0].strip()  # first spine only
        if not line or line.startswith("!"):
            omd = re.search(r"\[quarter\]\s*=\s*(\d+(?:\.\d+)?)", raw)
            if omd and tempo is None:
                tempo = float(omd.group(1))
            continue
        if line.startswith("*"):
            if re.fullmatch(r"\*M\d+/\d+", line):
                meter = line[2:]
            elif line.startswith("*MM") and line[3:].replace(".", "").isdigit():
                tempo = float(line[3:])
            elif line.startswith("*Tr"):
                trans = line[1:]
            continue
        if line.startswith("="):
            continue
        token = line.split(" ")  # a chord: notes split by spaces
        if any(("q" in x or "Q" in x) for x in token):
            continue  # grace note: no time of its own
        length = duration(token[0])
        if length is None:
            continue
        if "r" in token[0]:
            t += length
            open_tie = None
            continue
        pitches = [p for p in (midi(x) for x in token) if p is not None]
        if not pitches:
            t += length
            continue
        pitch = max(pitches)
        tie_end = any("]" in x or "_" in x for x in token)
        if tie_end and open_tie is not None and open_tie["pitch"] == pitch:
            open_tie["end"] = t + length
            if not any("_" in x for x in token):
                open_tie = None
        else:
            note = {"start": t, "end": t + length, "pitch": pitch}
            notes.append(note)
            open_tie = note if any("[" in x for x in token) else None
        t += length
    return {"notes": notes, "meter": meter, "tempo": tempo, "transposition": trans, "length": t}


def read(path: Path) -> dict:
    return parse(Path(path).read_text(encoding="utf-8", errors="replace"))
