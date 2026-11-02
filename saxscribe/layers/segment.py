"""Cutting the pitch line into notes, after the CREPE Notes method.

Riley and Dixon, "CREPE Notes: A new method for segmenting pitch contours into
discrete notes", SMC 2023 (CC BY 3.0). On Filosax they report note F-measure
82.3% against 75.5% for Basic Pitch. This is our own implementation from the
paper, working on our saved contour layer; no code from their package.

Steps:
  1. Note changes show up as a dip in the pitch tracker's confidence and a
     jump in the pitch line. Neither alone is clean, but their product
     (1 - confidence) x |pitch slope| has sharp peaks at note boundaries.
  2. Cut at every peak above a low threshold, then join neighbours whose
     median pitch rounds to the same note (vibrato and scoops are not new notes).
  3. Drop near-silent pieces, trim each note's ends where the sound has not
     started or has died away, and end a note at any quiet gap of 30 ms or more.
  4. Repeated notes on one pitch have no pitch jump, so split notes where the
     stem has a strong attack and the sound swells again, or where the level
     dips sharply and recovers (the tongue), and drop anything under 30 ms.
Pitch is the note's median, after allowing for the whole take's tuning (a
horn tuned 15 cents sharp still gets the right note names).
"""
from __future__ import annotations

import numpy as np

PEAK_HEIGHT = 0.002   # boundary strength threshold (the paper's default)
ATTACK = 0.7          # onset strength, as a share of the take's strong attacks, that splits a repeat
MIN_LEVEL = 0.06      # pieces quieter than this share of the take's loud level are dropped
TRIM_LEVEL = 0.04     # note ends quieter than this are trimmed
MIN_SECONDS = 0.03
EDGE = 0.05           # no repeat splits this close to a note's ends
DIP = 0.35            # a level dip this deep (share of the loud level) inside a note is a re-attack


def tuning_offset(midi: np.ndarray) -> float:
    """The take's tuning, in semitones from A=440 (between -0.5 and 0.5)."""
    frac = midi[np.isfinite(midi)] - np.round(midi[np.isfinite(midi)])
    if len(frac) == 0:
        return 0.0
    angle = np.angle(np.mean(np.exp(2j * np.pi * frac)))  # a circular mean: 0.49 and -0.49 are close
    return float(angle / (2 * np.pi))


def boundary_strength(midi: np.ndarray, confidence: np.ndarray) -> np.ndarray:
    filled = np.copy(midi)
    bad = ~np.isfinite(filled)
    if bad.all():
        return np.zeros_like(filled)
    filled[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), filled[~bad])
    slope = np.abs(np.gradient(filled))
    slope = slope / (slope.max() or 1.0)
    return (1 - np.nan_to_num(confidence)) * slope


def segment(line: dict, level: np.ndarray, attacks: np.ndarray) -> list[dict]:
    """Notes from a contour (see contour.read), a loudness envelope on the same
    10 ms frames (0 to about 1), and attack strengths on the same frames."""
    import scipy.signal
    times, midi, conf = line["time"], line["midi"], line["confidence"]
    n = len(times)
    if n < 3:
        return []
    step = float(times[1] - times[0])
    level = np.pad(level, (0, max(0, n - len(level))))[:n]
    attacks = np.pad(attacks, (0, max(0, n - len(attacks))))[:n]
    tune = tuning_offset(np.where(line["voiced"], midi, np.nan))

    # 1-2: cut at boundary peaks, then join pieces on the same note.
    peaks, _ = scipy.signal.find_peaks(boundary_strength(midi, conf), height=PEAK_HEIGHT)
    edges = [0, *peaks.tolist(), n]
    pieces = [(a, b) for a, b in zip(edges, edges[1:]) if b > a]

    def note_of(a, b):
        vals = midi[a:b][np.isfinite(midi[a:b])]
        return int(np.round(np.median(vals) - tune)) if len(vals) else None

    merged: list[list[int]] = []
    for a, b in pieces:
        p = note_of(a, b)
        if merged and p is not None and note_of(*merged[-1]) == p and merged[-1][1] == a:
            merged[-1][1] = b
        else:
            merged.append([a, b])

    loud = float(np.percentile(level, 95)) or 1.0
    rel = level / loud
    strong = ATTACK * (np.percentile(attacks[attacks > 0], 95) if (attacks > 0).any() else 1.0)
    edge = int(round(EDGE / step))
    gap = int(round(MIN_SECONDS / step))
    notes = []
    for a, b in merged:
        if rel[a:b].max() < MIN_LEVEL:
            continue
        # 3: trim to where it sounds; a quiet gap of 30 ms or more (a tongue stop, a breath) ends a note.
        sounding = a + np.flatnonzero(rel[a:b] >= TRIM_LEVEL)
        if len(sounding) == 0:
            continue
        runs = np.split(sounding, np.flatnonzero(np.diff(sounding) > gap) + 1)
        for run in runs:
            x, y = int(run[0]), int(run[-1]) + 1
            # 4: split repeats at strong attacks where the sound swells again (not a release).
            hits, _ = scipy.signal.find_peaks(attacks[x:y], height=strong, distance=edge)
            cuts = [x + h for h in hits if edge <= h <= (y - x) - edge
                    and rel[x + h:x + h + 4].mean() > 1.1 * rel[x + h - 4:x + h].mean()]
            # ...or where the level dips sharply and comes back (a tongue too quick to fall silent).
            dips, _ = scipy.signal.find_peaks(-rel[x:y], prominence=DIP, wlen=2 * edge + 1)
            cuts += [x + h for h in dips if edge <= h <= (y - x) - edge
                     and min(abs(x + h - c) for c in cuts or [-10 ** 9]) > edge // 2]
            cuts.sort()
            bounds = [x, *cuts, y]
            for u, v in zip(bounds, bounds[1:]):
                if (v - u) * step < MIN_SECONDS or rel[u:v].max() < MIN_LEVEL:
                    continue
                p = note_of(u, v)
                if p is None:
                    continue
                notes.append({"onset": float(times[u]), "offset": float(times[u]) + (v - u) * step,
                              "pitch": p, "amp": float(np.clip(rel[u:v].max(), 0.0, 1.0))})
    return notes


def envelopes(y: np.ndarray, sr: int, frames: int) -> tuple[np.ndarray, np.ndarray]:
    """Loudness and attack strength every 10 ms, for audio y at rate sr."""
    import librosa
    hop = int(round(sr * 0.01))
    level = librosa.feature.rms(y=y, frame_length=4 * hop, hop_length=hop, center=True)[0]
    attacks = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    pad = lambda v: np.pad(v, (0, max(0, frames - len(v))))[:frames]
    return pad(level), pad(attacks)
