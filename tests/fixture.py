"""A 10-second synthetic alto phrase with known notes, made fresh for each test run.

No audio lives in the repo, so the tests build their own: a reedy harmonic
tone at 120 BPM in concert pitch, with the things a sax line does that make
note cutting hard:
  - slurred steps (the pitch moves, no new attack, no gap)
  - tongued repeats (same pitch, a short dip in level)
  - a long note with vibrato
  - rests
It is a smoke test for the pipeline's wiring, not a stand-in for a real horn.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

RATE = 44100
BPM = 120.0
BEAT = 60.0 / BPM

# (start beat, length in beats, concert MIDI pitch, "slur" | "tongue" | "vibrato")
PHRASE = [
    (1.0, 0.5, 65, "tongue"), (1.5, 0.5, 67, "slur"), (2.0, 0.5, 69, "slur"), (2.5, 0.5, 70, "slur"),
    (3.0, 1.0, 72, "tongue"), (4.0, 0.5, 72, "tongue"), (4.5, 0.5, 72, "tongue"),
    (5.0, 3.0, 70, "vibrato"),
    (9.0, 0.5, 62, "tongue"), (9.5, 0.5, 65, "slur"), (10.0, 0.5, 69, "slur"), (10.5, 0.5, 72, "slur"),
    (11.0, 0.5, 74, "tongue"), (11.5, 0.5, 72, "tongue"), (12.0, 1.0, 69, "tongue"),
    (13.0, 0.5, 67, "tongue"), (13.5, 0.5, 65, "slur"), (14.0, 2.0, 63, "vibrato"),
    (17.0, 1.0, 58, "tongue"), (18.0, 1.0, 61, "tongue"),
]
SECONDS = 10.0


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def truth() -> list[dict]:
    """The phrase in seconds: [{onset, offset, pitch}]."""
    return [{"onset": b * BEAT, "offset": (b + n) * BEAT, "pitch": p} for b, n, p, _ in PHRASE]


def make(path: Path | None = None) -> np.ndarray:
    n = int(SECONDS * RATE)
    freq = np.zeros(n)
    amp = np.zeros(n)
    rng = np.random.default_rng(7)
    for i, (b, length, pitch, kind) in enumerate(PHRASE):
        a, z = int(b * BEAT * RATE), int((b + length) * BEAT * RATE)
        t = np.arange(z - a) / RATE
        f = np.full(z - a, hz(pitch))
        if kind == "vibrato":
            f *= 2 ** (0.25 * np.sin(2 * np.pi * 5.5 * t) / 12)  # +-25 cents at 5.5 Hz
        freq[a:z] = f
        env = np.ones(z - a)
        joined = kind == "slur" and i > 0
        if not joined:
            atk = int(0.02 * RATE)
            env[:atk] = np.linspace(0, 1, atk)
        nxt = PHRASE[i + 1] if i + 1 < len(PHRASE) else None
        if not (nxt and nxt[3] == "slur" and abs(nxt[0] - (b + length)) < 1e-9):
            rel = int(0.04 * RATE)  # a tongue stop or a breath before the next note
            env[-rel:] = np.linspace(1, 0, rel)
        amp[a:z] = env
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    # A reedy spectrum: strong low partials, slowly falling.
    y = sum((0.9 ** k) / k ** 0.5 * np.sin(k * phase) for k in range(1, 9))
    y = y * amp
    y += rng.normal(0, 0.002, n)  # a little room noise
    y = 0.5 * y / np.max(np.abs(y))
    if path is not None:
        import soundfile as sf
        sf.write(str(path), y.astype(np.float32), RATE)
    return y
