"""Band records: notes a singer may be making, marked for review (rule V, log E82).

The notes come from the Filosax sax stem, which lets voices through on pop and
R&B records (Austin flagged most of Najee's "Is It The Way Back" as vocals).
For each note this compares MVSep Mega's vocal stem with the sax stem at the
note's pitch (+-1 semitone, CQT, over the note, at least 0.1 s):

  - the vocal stem is at least RIVAL_DB as loud as the sax stem there, and
  - the vocal stem holds that pitch at least HELD_DB over its own usual level.

A note that passes is tagged "maybe_not_sax" (shown as a review stretch in the
play-along) and "maybe_vocals" (why). Nothing is hidden or removed.

Settings fixed before the test (E82 round 3, 2026-11-13), then scored once: on
11 songs with answer keys (Austin's six tunes plus five jazz records with the
loudest Demucs vocal stems) it marked 0 of 3,206 notes that match the key and
112 extra notes on Bloody Well Right; in Austin's flagged takes it marked 241
of 603 notes inside his not-sax flags against 19 of 528 outside (Najee), and
4 of 4 against 2 of 201 (Just the Two of Us). Demucs' vocal stem in the same
rule marked 268 real sax notes, most on Pennies and Blues for Mary Jane, where
it carries the sax itself.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .notsax import CQT_HOP, CQT_RATE, LOW_MIDI, BINS, MAYBE_NOT_SAX, cqt_power

MAYBE_VOCALS = "maybe_vocals"
RIVAL_DB = 0.0     # the vocal stem is at least this loud as the sax stem at the note's pitch...
HELD_DB = 3.0      # ...and holds that pitch this far over its own median there
MIN_DUR = 0.1      # s: shorter notes are measured over this long
SKIP = ("not_sax",)  # notes already left off the score


def band(c: np.ndarray, note: dict):
    """Mean CQT power per bin (+-1 semitone around the note) over the note, and the bins used."""
    b = int(round(note["pitch"])) - LOW_MIDI
    if not 0 <= b < BINS:
        return None
    f0 = int(note["onset"] * CQT_RATE / CQT_HOP)
    f1 = max(int(max(note["offset"], note["onset"] + MIN_DUR) * CQT_RATE / CQT_HOP), f0 + 1)
    if f0 >= c.shape[1]:
        return None
    lo, hi = max(0, b - 1), b + 2
    return c[lo:hi, f0:f1].mean(axis=1), slice(lo, hi)


def features(sax: tuple, voc: tuple, note: dict) -> tuple[float, float]:
    """(vocal over sax in dB, vocal over its own median in dB) at the note; -99 when out of range."""
    s, v = band(sax[0], note), band(voc[0], note)
    if s is None or v is None:
        return -99.0, -99.0
    (es, _), (ev, bins) = s, v
    rival = 10 * np.log10((ev.sum() + 1e-12) / (es.sum() + 1e-12))
    held = float(np.max(10 * np.log10((ev + 1e-12) / voc[1][bins])))
    return float(rival), held


def mark(notes: list[dict], sax_stem: Path, vocal_stem: Path) -> dict:
    """Tags notes a singer may be making (in place); never removes or hides one."""
    from .. import frontend
    sax = cqt_power(frontend.load_mono(sax_stem, sr=CQT_RATE))
    voc = cqt_power(frontend.load_mono(vocal_stem, sr=CQT_RATE))
    return mark_with(notes, sax, voc)


def mark_with(notes: list[dict], sax: tuple, voc: tuple) -> dict:
    marked = 0
    for n in notes:
        tags = n.setdefault("tags", [])
        if any(t in tags for t in SKIP) or MAYBE_VOCALS in tags:
            continue
        rival, held = features(sax, voc, n)
        if rival >= RIVAL_DB and held >= HELD_DB:
            tags.append(MAYBE_VOCALS)
            if MAYBE_NOT_SAX not in tags:
                tags.append(MAYBE_NOT_SAX)
            marked += 1
    return {"marked": marked, "settings": {"rival_db": RIVAL_DB, "held_db": HELD_DB, "min_dur_s": MIN_DUR}}
