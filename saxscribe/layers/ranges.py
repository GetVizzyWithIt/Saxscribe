"""Range rules: check every note against what the horn can play.

The note detectors know nothing about saxophones. They can hand back a note
no sax can sound (below the low Bb key, or far above any altissimo), and
they can lock onto an overtone: a low note whose second partial is louder
than its fundamental (common in the sax's bottom octave) comes out an octave
too high. These rules use the horn's range (horns.py) and the stem's own
spectrum to catch both. No note is ever removed: a note is either moved and
tagged, or kept as heard and tagged.

Tags added to a note in notes.json (with "detected_pitch" = the detector's
pitch whenever the pitch was moved):
  octave_up      below the horn's lowest note and not a bend: moved up into range
  octave_down    above the horn's highest altissimo note: moved down into range
                 (by an octave, or an octave and a fifth when the stem shows it
                 was the third partial)
  below_range    up to two semitones below the lowest note: kept as heard
                 (a lipped-down low note, or a horn tuned flat). On a band
                 record (mix=True) such a note is also tagged not_sax: kept in
                 notes.json but left off the score, since there it is nearly
                 always the piano or bass coming through the sax stem (Pennies
                 From Heaven, 2026-11-04: 14 of 14 were, none was Getz).
  altissimo      above the keyed range: kept. Real altissimo is never moved
                 for being high.
  overtone       the stem shows the partials of a note an octave (or an octave
                 and a fifth) lower: the detector may have heard an overtone.
                 Only with --range-rules overtones (moved) or flag (kept).
                 Not in the default: on 2026-11-04, of 678 notes it flagged on
                 Omnibook and GRFIA, the answer key agreed with the lower note
                 6 times and with the note as heard 129 times.
  out_of_range   outside the range, and not moved because too many notes are
                 (most likely the take was made with the wrong horn)

Modes (--range-rules):
  out        (default) move notes no sax can play; tag altissimo and near-misses
  overtones  also move notes tagged overtone down to the fundamental
  flag       tag only (overtones too), move nothing
  off        no range rules
"""
from __future__ import annotations

import numpy as np

from ..horns import BEND_ROOM, HORNS, Horn, hz

MODES = ("out", "overtones", "flag", "off")
SKIP = "not_sax"
WRONG_HORN_SHARE = 0.1   # this share of a take's notes out of range: suspect the wrong horn, move nothing
WRONG_HORN_LEAST = 5
OVERTONE_RATIO = 0.3     # the lower note's own partials, against the heard note's partials
EDGE = 0.02              # s skipped at each end of a note (scoops, releases)
N_FFT = 8192             # 0.19 s at 44.1 kHz: 5 Hz bins, enough for a low Bb's partials
RATE = 44100
# Where a heard note may really be a partial: (semitones down to the fundamental, partial number).
PARTIALS = ((12, 2), (19, 3))


def apply(notes: list[dict], horn: Horn, y: np.ndarray | None = None, sr: int = RATE,
          mode: str = "out", mix: bool = False) -> dict:
    """Check notes (concert MIDI, with "tags" lists) in place. y is the stem, for
    the overtone check; without it only the range is used. mix: the take is a
    band record, so a note just below the horn is another instrument. Returns counts."""
    if mode not in MODES:
        raise ValueError(f"range rules: unknown mode {mode!r}")
    counts = {"mode": mode}
    if mode == "off":
        return counts
    played = [n for n in notes if SKIP not in (n.get("tags") or [])]
    spec = Spectrum(y, sr) if y is not None and len(y) else None
    far = [n for n in played if n["pitch"] < horn.low - BEND_ROOM or n["pitch"] > horn.altissimo]
    wrong_horn = len(far) >= WRONG_HORN_LEAST and len(far) > WRONG_HORN_SHARE * len(played)
    if wrong_horn:
        counts["better_horn"] = best_horn([n["pitch"] for n in played], horn)
    move = mode in ("out", "overtones") and not wrong_horn
    check_overtones = mode in ("overtones", "flag")

    for n in played:
        tags = n.setdefault("tags", [])
        p = n["pitch"]
        where = horn.register(p)
        far_out = where in ("below", "above") and not (where == "below" and p >= horn.low - BEND_ROOM)
        # The overtone check runs on notes above the altissimo (which partial was it?),
        # and on every note only when asked: as a tag it was wrong far more often than right.
        sub = (spec.lower_partial(n) if spec is not None and (far_out or check_overtones) else None)
        if where == "below" and p >= horn.low - BEND_ROOM:
            tags.append("below_range")
            if mix:
                tags.append(SKIP)
        elif where in ("below", "above"):
            if not move:
                tags.append("out_of_range")
            elif where == "below":
                new = p + 12 * -(-(horn.low - p) // 12)
                put(n, new if horn.playable(new) else p, "octave_up" if horn.playable(new) else "out_of_range")
            else:
                down = sub[0] if sub and horn.playable(p - sub[0]) else 12
                new = p - down
                while new > horn.altissimo:
                    new -= 12
                put(n, new if horn.playable(new) else p, "octave_down" if horn.playable(new) else "out_of_range")
            continue
        elif where == "altissimo":
            tags.append("altissimo")
        if sub and horn.playable(p - sub[0]):
            tags.append("overtone")
            if mode == "overtones" and not wrong_horn:
                put(n, p - sub[0], None)
    for tag in ("octave_up", "octave_down", "below_range", "altissimo", "overtone", "out_of_range"):
        counts[tag] = sum(tag in n.get("tags", []) for n in played)
    counts["moved"] = sum("detected_pitch" in n for n in played)
    if mix:
        counts["below_range_not_sax"] = sum(SKIP in n.get("tags", []) and "below_range" in n["tags"] for n in played)
    return counts


def put(n: dict, pitch: int, tag: str | None) -> None:
    if pitch != n["pitch"]:
        n.setdefault("detected_pitch", n["pitch"])
        n["pitch"] = int(pitch)
    if tag:
        n["tags"].append(tag)


def best_horn(pitches: list[int], now: Horn) -> str:
    """The horn whose range holds the most of these notes (the current one on a tie)."""
    score = {name: sum(h.playable(p) for p in pitches) for name, h in HORNS.items() if h.family == now.family}
    top = max(score.values())
    return now.name if score.get(now.name) == top else max(score, key=score.get)


class Spectrum:
    """The stem's magnitude spectrum, averaged over a note, to ask which partials sound."""

    def __init__(self, y: np.ndarray, sr: int):
        self.y, self.sr = np.asarray(y, dtype=float), sr

    def mean(self, onset: float, offset: float) -> np.ndarray | None:
        a, b = int((onset + EDGE) * self.sr), int((offset - EDGE) * self.sr)
        if b - a < 1024:
            a, b = int(onset * self.sr), int(offset * self.sr)
        seg = self.y[max(0, a):max(0, b)]
        if len(seg) < 1024:
            return None
        n_fft = N_FFT if len(seg) >= N_FFT else 1 << int(np.log2(len(seg)))
        hop = n_fft // 2
        frames = [seg[i:i + n_fft] for i in range(0, max(1, len(seg) - n_fft + 1), hop)]
        win = np.hanning(n_fft)
        return np.mean([np.abs(np.fft.rfft(f * win)) for f in frames], axis=0)

    def level(self, mag: np.ndarray, f: float) -> float:
        """The strongest bin within 40 cents of f."""
        res = self.sr / (2 * (len(mag) - 1))
        lo, hi = int(f * 2 ** (-40 / 1200) / res), int(np.ceil(f * 2 ** (40 / 1200) / res))
        if lo >= len(mag):
            return 0.0
        return float(mag[max(lo, 1):min(hi, len(mag) - 1) + 1].max())

    def lower_partial(self, n: dict) -> tuple[int, float] | None:
        """(semitones down, ratio) when the heard note looks like partial 2 or 3 of a
        lower note: that lower note's own partials (the ones the heard note does not
        share) are at least OVERTONE_RATIO as loud as the shared ones. Else None."""
        mag = self.mean(n["onset"], n["offset"])
        if mag is None:
            return None
        f = hz(n["pitch"] + (n.get("cents") or 0) / 100)
        best = None
        for down, k in PARTIALS:
            g = f / k
            shared = [self.level(mag, g * m) for m in range(k, 4 * k + 1, k)]          # g*k, 2gk...: the heard note's partials
            own = [self.level(mag, g * m) for m in range(1, 4 * k) if m % k]            # the rest: only the lower note has them
            ref = float(np.mean(shared)) or 1e-12
            ratio = float(np.mean(sorted(own, reverse=True)[:k])) / ref
            if ratio >= OVERTONE_RATIO and (best is None or ratio > best[1]):
                best = (down, ratio)
        return best


UNPLAYABLE_COLOR = "#c00000"


def mark_unplayable(score, horn: Horn, shift: int) -> int:
    """Colour red every note in a music21 score that the horn cannot play (shift =
    semitones from concert to the score's pitch: 0 for concert, written_shift for
    the horn's part). The note stays as heard; the colour says "check this".
    Returns how many were marked."""
    marked = 0
    for el in score.recurse().notes:
        for p in getattr(el, "pitches", ()):
            if not horn.playable(int(round(p.ps)) - shift):
                el.style.color = UNPLAYABLE_COLOR
                marked += 1
                break
    return marked
