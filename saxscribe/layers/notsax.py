"""Band records only: notes that may be another instrument, marked for review.

A separator sometimes lets a whole piano solo through as "sax". On Pennies
From Heaven the Filosax separator kept the piano at 3:42-4:21 near sax level,
and its transcriber wrote 64 piano notes. This check finds such stretches
with Demucs' six stems (rule E, log E67):

  - the Demucs stems the sax lands in are nearly silent: under SAX_DB of the
    mix, in 2 s windows (1 s apart),
  - the loudest rival stem (piano, guitar or bass) is within RIVAL_DB of it,
  - both for a run of at least RUN seconds, holding the whole note (+-0.5 s),
  - and a rival stem holds the note's own pitch (within a semitone) at least
    PITCH_DB over its usual level at that pitch.

A note that passes is tagged "maybe_not_sax". It stays on the score: this is
a review mark only, shown in the play-along for Austin to confirm by ear.

Why not hide them: real sax can sink just as low in Demucs' stems. Over the
key spans of Resolution and Impressions 1963 it reaches -66 and -77 dB, lower
than the Pennies piano solo's -56. Measured 2026-11-06 (tuned on the Parker
and Weimar train records, Austin's tunes held out): on the Filosax path it
marks all 70 Pennies piano-solo notes, and about 1.6% of real sax (mostly
on Impressions and Item 1). Hiding waits for a second opinion that agrees,
tested against Austin's answers on these marks.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

MAYBE_NOT_SAX = "maybe_not_sax"
RIVALS = ("piano", "guitar", "bass")   # Demucs stems that can carry a solo the sax doesn't play
LEVEL_RATE = 16000
WINDOW, STEP = 2, 1   # s: level windows and their spacing (window i covers [i, i + 2) s)
SAX_DB = -20.0        # the sax stems' share of the mix is under this...
RIVAL_DB = {"filosax": 6.0, "demucs": 10.0}   # ...while a rival's share is within this of the mix
RUN = 4               # s: a run of k windows covers k + 1 s
AROUND = 0.5          # s: the whole note plus this much either side lies inside one run
CQT_RATE, CQT_HOP, LOW_MIDI, BINS = 22050, 512, 24, 84
PITCH_DB = 6.0        # a rival holds the note's pitch this far over its median there


def load_sum(paths: list[Path], rate: int) -> np.ndarray:
    from .. import frontend
    ys = [frontend.load_mono(p, sr=rate) for p in paths]
    n = min(len(y) for y in ys)
    return np.sum([y[:n] for y in ys], axis=0)


def shares(y: np.ndarray, mix: np.ndarray) -> np.ndarray:
    """The stem's share of the mix in dB, per window."""
    n = min(len(y), len(mix))
    win, hop = WINDOW * LEVEL_RATE, STEP * LEVEL_RATE
    return np.array([10 * np.log10((np.mean(y[i:i + win] ** 2) + 1e-10) / (np.mean(mix[i:i + win] ** 2) + 1e-10))
                     for i in range(0, n - win + 1, hop)])


def runs(mask: np.ndarray, least: float) -> list[tuple[float, float]]:
    """[start, end) in seconds of each run of windows lasting at least `least` seconds."""
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if (i - start) * STEP + (WINDOW - STEP) >= least:
                out.append((float(start * STEP), float(i * STEP + WINDOW - STEP)))
            start = None
    return out


def cqt_power(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    import librosa
    c = np.abs(librosa.cqt(y, sr=CQT_RATE, hop_length=CQT_HOP, fmin=librosa.midi_to_hz(LOW_MIDI),
                           n_bins=BINS, bins_per_octave=12)) ** 2
    return c, np.median(c, axis=1) + 1e-12


def pitch_held(cqts: dict, note: dict) -> bool:
    """Does some rival stem hold the note's pitch (+-1 semitone) clearly over its usual level?"""
    b = int(round(note["pitch"])) - LOW_MIDI
    if not 0 <= b < BINS:
        return False
    f0 = int(note["onset"] * CQT_RATE / CQT_HOP)
    f1 = max(int(note["offset"] * CQT_RATE / CQT_HOP), f0 + 1)
    lo, hi = max(0, b - 1), b + 2
    for c, med in cqts.values():
        if f0 >= c.shape[1]:
            continue
        e = c[lo:hi, f0:f1].mean(axis=1)
        if np.max(10 * np.log10((e + 1e-12) / med[lo:hi])) >= PITCH_DB:
            return True
    return False


def mark(notes: list[dict], mix: Path, sax: list[Path], rivals: dict[str, Path], path: str = "demucs") -> dict:
    """Tags questionable notes MAYBE_NOT_SAX (in place); never removes or hides one.
    sax: the Demucs stems the sax lands in (added together). path: "filosax" or "demucs",
    the note finder's path, which sets how close to the mix a rival must be."""
    from .. import frontend
    m = frontend.load_mono(mix, sr=LEVEL_RATE)
    sax_share = shares(load_sum(sax, LEVEL_RATE), m)
    rival_share = {n: shares(frontend.load_mono(p, sr=LEVEL_RATE), m) for n, p in rivals.items()}
    if not rival_share:
        return {"marked": 0, "why": "no rival stems"}
    k = min([len(sax_share)] + [len(v) for v in rival_share.values()])
    loudest = np.max([v[:k] for v in rival_share.values()], axis=0)
    spans = runs((sax_share[:k] < SAX_DB) & (loudest >= -RIVAL_DB[path]), RUN)
    settings = {"sax_db": SAX_DB, "rival_db": RIVAL_DB[path], "run_s": RUN, "pitch_db": PITCH_DB}
    if not spans:
        return {"marked": 0, "spans": [], "settings": settings}
    cqts = {n: cqt_power(frontend.load_mono(p, sr=CQT_RATE)) for n, p in rivals.items()}
    marked = 0
    for n in notes:
        a, b = n["onset"] - AROUND, n["offset"] + AROUND
        if MAYBE_NOT_SAX not in n["tags"] and any(x <= a and b <= y for x, y in spans) and pitch_held(cqts, n):
            n["tags"].append(MAYBE_NOT_SAX)
            marked += 1
    return {"marked": marked, "spans": [[a, b] for a, b in spans], "settings": settings}
