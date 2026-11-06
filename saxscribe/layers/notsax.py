"""Band records only: notes that may be another instrument, marked for review.

A separator sometimes lets a whole piano solo through as "sax". On Pennies
From Heaven the Filosax separator kept the piano at 3:42-4:21 near sax level,
and its transcriber wrote 64 piano notes. This check finds such stretches
with Demucs' six stems:

  - Demucs' sax stem (the stem the sax lands in) is nearly silent: at least
    SILENT dB under the mix,
  - a rival stem (piano, guitar or bass) is loud: within RIVAL dB of the mix,
  - both for at least RUN seconds in a row,
  - and the rival stem holds the note's own pitch (within a semitone).

A note that passes is tagged "maybe_not_sax". It stays on the score: this is
a review mark only, shown in the play-along for Austin to confirm by ear.

Why not hide them: real sax can sink just as low in Demucs' sax stem. Over
the key spans of Resolution and Impressions 1963 it reaches -66 and -77 dB,
lower than the Pennies piano solo's -56. Measured 2026-11-06 (log E67, E68;
tuned on the Parker and Weimar train records, Austin's tunes held out):
on the Filosax path it marks all 70 Pennies piano-solo notes, and about 1.6%
of real sax (on Impressions and Item 1) for review. Hiding waits until
Austin's answers on these marks give a fair test set.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

MAYBE_NOT_SAX = "maybe_not_sax"
RIVALS = ("piano", "guitar", "bass")   # Demucs stems that can carry a melody the sax doesn't play
FRAME = 0.5         # s per level frame
SILENT = -20.0      # dB under the mix: Demucs' sax stem is nearly silent
RIVAL = {"filosax": 6.0, "demucs": 10.0}   # dB: a rival stem this close to the mix is playing
RUN = 4.0           # s: both hold this long in a row
AROUND = 0.5        # s either side of a note when reading its levels
RATE = 22050


def levels(y: np.ndarray, rate: int = RATE) -> np.ndarray:
    """dB per FRAME (RMS)."""
    n = int(FRAME * rate)
    k = len(y) // n
    if k == 0:
        return np.zeros(0)
    r = np.sqrt(np.mean(y[:k * n].reshape(k, n) ** 2, axis=1))
    return 20 * np.log10(np.maximum(r, 1e-7))


def runs(mask: np.ndarray, least: int) -> list[tuple[int, int]]:
    """Index ranges [a, b) where mask is true for at least `least` frames."""
    out, a = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and a is None:
            a = i
        elif not m and a is not None:
            if i - a >= least:
                out.append((a, i))
            a = None
    return out


def pitch_held(cqt_db: np.ndarray, median: np.ndarray, pitch: int, a: float, b: float,
               hop_s: float, low_midi: int) -> bool:
    """Does the stem hold this pitch (+-1 semitone) over [a, b) more than it usually does?"""
    i0, i1 = int(a / hop_s), max(int(a / hop_s) + 1, int(b / hop_s))
    bins = [p - low_midi for p in (pitch - 1, pitch, pitch + 1) if 0 <= p - low_midi < cqt_db.shape[0]]
    if not bins or i0 >= cqt_db.shape[1]:
        return False
    seg = cqt_db[bins, i0:min(i1, cqt_db.shape[1])]
    return bool(np.max(np.mean(seg, axis=1) - median[bins]) > 0)


def mark(notes: list[dict], mix: Path, sax: Path, rivals: dict[str, Path], path: str = "demucs",
         skip: str = "not_sax") -> dict:
    """Tags questionable notes MAYBE_NOT_SAX (in place). Returns counts for take.json."""
    import librosa
    from .. import frontend
    rival_db = RIVAL[path]
    y_mix = frontend.load_mono(mix, sr=RATE)
    mix_db = levels(y_mix)
    sax_db = levels(frontend.load_mono(sax, sr=RATE))
    k = min(len(sax_db), len(mix_db))
    sax_rel = sax_db[:k] - mix_db[:k]
    rel, ys = {}, {}
    for name, p in rivals.items():
        ys[name] = frontend.load_mono(p, sr=RATE)
        lv = levels(ys[name])
        k = min(len(lv), len(mix_db))
        rel[name] = lv[:k] - mix_db[:k]
    if not rel:
        return {"marked": 0, "why": "no rival stems"}
    k = min([len(sax_rel)] + [len(v) for v in rel.values()])
    loud = np.max(np.stack([v[:k] for v in rel.values()]), axis=0) >= -rival_db
    quiet = sax_rel[:k] <= SILENT
    spans = [(a * FRAME, b * FRAME) for a, b in runs(quiet & loud, int(round(RUN / FRAME)))]
    if not spans:
        return {"marked": 0, "spans": []}
    hop = 512
    low = 24  # C1
    cqts = {}
    for name, y in ys.items():
        c = np.abs(librosa.cqt(y, sr=RATE, hop_length=hop, fmin=librosa.midi_to_hz(low),
                               n_bins=84, bins_per_octave=12))
        c = librosa.amplitude_to_db(c, ref=np.max)
        cqts[name] = (c, np.median(c, axis=1))
    marked = 0
    for n in notes:
        if skip in n["tags"] or not any(a <= n["onset"] < b for a, b in spans):
            continue
        f0, f1 = int(max(0.0, n["onset"] - AROUND) / FRAME), int((n["offset"] + AROUND) / FRAME) + 1
        if not (f1 > f0 and np.mean(sax_rel[f0:f1]) <= SILENT):
            continue
        playing = [name for name in rel if np.mean(rel[name][f0:min(f1, len(rel[name]))]) >= -rival_db]
        if any(pitch_held(*cqts[name], int(n["pitch"]), n["onset"], n["offset"], hop / RATE, low)
               for name in playing):
            n["tags"].append(MAYBE_NOT_SAX)
            marked += 1
    return {"marked": marked, "spans": [[round(a, 1), round(b, 1)] for a, b in spans],
            "settings": {"silent_db": SILENT, "rival_db": rival_db, "run_s": RUN}}
