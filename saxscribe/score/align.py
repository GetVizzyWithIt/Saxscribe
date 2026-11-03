"""An answer key for your own take of a written piece: line the score up with the audio.

  python -m saxscribe answer-key take.wav etude.musicxml

Writes take.mid next to the audio (the score's notes at the times you played
them), so the folder can be scored as a "pairs" set. Works from day one,
before the model is any good, because it uses the score, not the transcription.

How: the score becomes a chroma sequence (which of the 12 pitch classes sound
when) at a steady tempo; so does the recording. Dynamic time warping finds the
best way to stretch one onto the other. Each note's start is then nudged to the
nearest attack heard in the audio, within 80 ms.

Scores for alto are usually written in E-flat; --score-pitch written (the
default) moves them to concert pitch first.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .. import frontend
from ..horns import HORNS

SR = 22050
HOP = 512
SNAP = 0.08


def score_notes(path: Path, horn: str, written: bool) -> list[dict]:
    """[{start, end, pitch}] in quarter notes, concert pitch, ties joined, top note of chords."""
    from music21 import converter, interval
    s = converter.parse(str(path))
    if written:
        s = s.transpose(interval.Interval(HORNS[horn].written_interval).reverse())
    part = s.parts[0] if s.parts else s
    out = []
    for n in part.stripTies().flatten().notes:
        p = max(n.pitches, key=lambda x: x.midi)
        start = float(n.getOffsetInHierarchy(part))
        out.append({"start": start, "end": start + float(n.quarterLength), "pitch": p.midi})
    return sorted(out, key=lambda n: n["start"])


def score_chroma(notes: list[dict], frames_per_beat: float) -> np.ndarray:
    total = int(np.ceil(max(n["end"] for n in notes) * frames_per_beat)) + 1
    c = np.zeros((12, total))
    for n in notes:
        a, b = int(n["start"] * frames_per_beat), max(int(n["end"] * frames_per_beat), int(n["start"] * frames_per_beat) + 1)
        c[n["pitch"] % 12, a:b] = 1.0
        c[(n["pitch"] + 7) % 12, a:b] += 0.2  # a little of the third harmonic, as a horn has
    c[:, c.sum(axis=0) == 0] = 0.01  # rests: a faint, even floor
    return c / np.linalg.norm(c, axis=0, keepdims=True)


def align(audio: Path, score: Path, horn: str = "alto", written: bool = True) -> list[dict]:
    notes = score_notes(score, horn, written)
    if not notes:
        raise SystemExit(f"No notes in {score}")
    return align_notes(audio, notes)


def align_notes(audio: Path, notes: list[dict]) -> list[dict]:
    """Score notes [{start, end, pitch}] in quarters, concert pitch, lined up with
    the recording: [{onset, offset, pitch, beat}] in seconds (beat is the
    note's place in the score, in quarters, kept for rhythm scoring)."""
    import librosa
    y = frontend.load_mono(audio, SR)
    chroma = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0][: chroma.shape[1]]
    chroma[:, rms < 0.02 * rms.max()] = 0.01  # silence looks like the score's rests
    chroma = chroma / np.linalg.norm(chroma, axis=0, keepdims=True)
    seconds_per_frame = HOP / SR
    # Start the score at the recording's average tempo, so warping has less to do.
    beats_total = max(n["end"] for n in notes)
    sounding = np.flatnonzero(rms >= 0.02 * rms.max())
    span = (sounding[-1] - sounding[0] + 1) if len(sounding) else chroma.shape[1]
    frames_per_beat = span / beats_total
    ref = score_chroma(notes, frames_per_beat)
    _, path = librosa.sequence.dtw(X=ref, Y=chroma, metric="cosine")
    path = path[::-1]
    score_frames, audio_frames = path[:, 0].astype(float), path[:, 1].astype(float)
    # For each score frame, the middle of the audio frames it was matched to.
    uniq = np.unique(score_frames)
    mapped = np.array([audio_frames[score_frames == f].mean() for f in uniq])

    def to_seconds(beat: float) -> float:
        return float(np.interp(beat * frames_per_beat, uniq, mapped)) * seconds_per_frame

    onsets = np.array([o["t"] for o in frontend.detect_onsets(frontend.load_mono(audio))])
    out = []
    for n in notes:
        t0, t1 = to_seconds(n["start"]), to_seconds(n["end"])
        if len(onsets):
            k = int(np.argmin(np.abs(onsets - t0)))
            if abs(onsets[k] - t0) <= SNAP:
                t0 = float(onsets[k])
        out.append({"onset": t0, "offset": max(t1, t0 + 0.03), "pitch": n["pitch"], "beat": float(n["start"])})
    for a, b in zip(out, out[1:]):
        a["offset"] = min(a["offset"], b["onset"])
    return out


def run(audio: Path, score: Path, out: Path | None, horn: str, written: bool) -> Path:
    from .refs import write_midi_notes
    notes = align(audio, score, horn, written)
    dst = out or audio.with_suffix(".mid")
    write_midi_notes(dst, notes)
    frontend.log(f"Answer key: {len(notes)} notes lined up with {audio.name}; wrote {dst}")
    return dst
