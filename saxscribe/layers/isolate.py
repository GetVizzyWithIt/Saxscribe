"""Layer 1: get the sax on its own.

A solo take is passed through: stem.wav is a copy of the source. A full mix
goes through Demucs; every stem is kept in stems/ so you can listen and pick
another with --stem, and accompaniment.wav is everything else added together.

Which stem holds the sax: Demucs (htdemucs_6s) has no sax stem, so the horn
lands in "other" on most records but in "guitar" on some, or is split
between the two (seen on Parker records: 7XTyc all in guitar, BRfYc about
half and half). By default (--stem auto) each melodic stem gets a lead score:
its loudness in frames that sound like one clear pitch, which favours a horn
line over chords. A stem with LEAD_ALONE of the total is used on its own;
otherwise every stem over LEAD_PART is added together. The scores and the
choice go in take.json.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from .. import frontend
from ..take import Take

DEFAULT_STEM = "other"  # where sax usually lands in Demucs' six stems
MELODIC = ("other", "guitar", "piano", "vocals")  # stems a horn can land in
LEAD_ALONE = 0.8   # a stem with this share of the lead score is used alone
LEAD_PART = 0.2    # otherwise stems with at least this share are added together
LEAD_RATE = 16000
LEAD_FRAME = 2048  # 128 ms: many periods of the lowest note
LEAD_HOP = 800     # 50 ms
LEAD_HZ = (95.0, 1600.0)  # tenor low B-flat (concert A-flat2, 104 Hz) up to altissimo


def run(take: Take, src: Path, mix: bool, stem: str | None) -> None:
    take.folder.mkdir(parents=True, exist_ok=True)
    frontend.log(f"Layer 1/4: isolate ({'full mix' if mix else 'solo take'})")
    frontend.decode(src, take.source)
    if not mix:
        shutil.copyfile(take.source, take.stem)
        take.accompaniment.unlink(missing_ok=True)
        take.record("isolate", tool="passthrough", source=str(src))
        return

    stems = {p.stem: p for p in take.stems.glob("*.wav")}
    if stems:
        frontend.log("Using the stems already separated (delete stems/ to separate again).")
    else:
        if not frontend.demucs_available():
            raise SystemExit("A full mix needs Demucs. Install it with: pip install -r requirements.txt")
        stems = frontend.separate_stems(take.source, take.stems)
    scores = {}
    if stem in (None, "auto"):
        scores = {n: lead_score(stems[n]) for n in MELODIC if n in stems}
        chosen = choose(scores) or [DEFAULT_STEM]
    else:
        chosen = [n.strip() for n in stem.split("+")]
    missing = [n for n in chosen if n not in stems]
    if missing:
        raise SystemExit(f"No stem called {missing[0]!r}. Stems: {', '.join(sorted(stems))}")
    if len(chosen) == 1:
        shutil.copyfile(stems[chosen[0]], take.stem)
    else:
        write_sum(take.stem, [stems[n] for n in chosen])
    write_accompaniment(take.accompaniment, [p for n, p in stems.items() if n not in chosen])
    name = "+".join(chosen)
    share = {n: round(v, 3) for n, v in shares(scores).items()}
    take.record("isolate", tool="demucs htdemucs_6s", stem=name, source=str(src), stems=sorted(stems),
                **({"lead_share": share} if share else {}))
    how = f" (lead share {', '.join(f'{n} {v:.0%}' for n, v in share.items())})" if share else ""
    frontend.log(f"Using the {name!r} stem{how}. Others are in {take.stems} to listen to.")


def lead_score(path: Path) -> float:
    """Loudness in frames that hold one clear pitch in the horn range.

    Per 128 ms frame: the autocorrelation peak in the horn range says how
    clearly one pitch sounds (about 0.95 for a horn line, under 0.6 for piano
    chords, near 0 for drums). Frames are weighted by how far that sits above
    0.5, squared, times the frame's energy, and summed."""
    y = frontend.load_mono(path, sr=LEAD_RATE)
    if len(y) < LEAD_FRAME:
        return 0.0
    frames = np.lib.stride_tricks.sliding_window_view(y, LEAD_FRAME)[::LEAD_HOP] * np.hanning(LEAD_FRAME)
    spec = np.abs(np.fft.rfft(frames, n=2 * LEAD_FRAME, axis=1)) ** 2
    ac = np.fft.irfft(spec, axis=1)[:, :LEAD_FRAME]
    energy = ac[:, 0]
    lo, hi = int(LEAD_RATE / LEAD_HZ[1]), int(LEAD_RATE / LEAD_HZ[0])
    peak = ac[:, lo:hi].max(axis=1) / np.maximum(energy, 1e-12)
    clarity = np.clip((peak - 0.5) / 0.5, 0, 1) ** 2
    return float(np.sum(energy * clarity))


def shares(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    return {n: v / total for n, v in scores.items()} if total > 0 else {}


def choose(scores: dict[str, float]) -> list[str]:
    """One stem when it clearly holds the lead, else every stem with a fair part of it."""
    s = shares(scores)
    if not s:
        return []
    ranked = sorted(s, key=s.get, reverse=True)
    if s[ranked[0]] >= LEAD_ALONE:
        return ranked[:1]
    return [n for n in ranked if s[n] >= LEAD_PART]


def write_sum(dst: Path, paths: list[Path]) -> None:
    write_accompaniment(dst, paths)  # the same thing: stems added together


def write_accompaniment(dst: Path, paths: list[Path]) -> None:
    import soundfile as sf
    total, rate = None, None
    for p in paths:
        y, rate = sf.read(str(p), always_2d=True)
        if total is None:
            total = y
        else:
            n = min(len(total), len(y))
            total = total[:n] + y[:n]
    if total is not None:
        sf.write(str(dst), np.clip(total, -1.0, 1.0), rate)
