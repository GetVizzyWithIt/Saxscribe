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
STEADY_SNAP = 0.04      # metronome keys: attacks this close to the beat grid are taken
STEADY_SLOPES = np.linspace(0.97, 1.03, 13)   # how far the player's tempo may sit off the marking
STEADY_GOOD = 0.6       # share of key notes that must land on a heard attack for the fit to stand
STEADY_CLOSE = 0.85     # fits landing this share of the best fit's notes are compared by pitch
DTW_BETTER = 0.05       # DTW key wins only when its pitches agree this much better than the steady key's


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
        out.append({"onset": t0, "offset": max(t1, t0 + MIN_NOTE), "pitch": n["pitch"], "beat": float(n["start"])})
    return tidy(out)


MIN_NOTE = 0.03  # seconds: the shortest note an answer key may hold


def tidy(notes: list[dict]) -> list[dict]:
    """Every key note keeps a length of at least MIN_NOTE and starts after the one before.

    Warping can put a very short note (a thirty-second) on the same instant as
    its neighbour, which left it with no length at all and stopped the scoring
    (mir_eval needs every note to last). Such a note moves just after the one
    before it rather than being dropped."""
    out = sorted((dict(n) for n in notes), key=lambda n: n["onset"])
    for n in out:
        n["onset"] = max(0.0, n["onset"])
        n["offset"] = max(0.0, n["offset"])
    for a, b in zip(out, out[1:]):
        if b["onset"] < a["onset"] + MIN_NOTE:
            b["onset"] = a["onset"] + MIN_NOTE
    for a, b in zip(out, out[1:]):
        a["offset"] = min(max(a["offset"], a["onset"] + MIN_NOTE), b["onset"])
    if out:
        out[-1]["offset"] = max(out[-1]["offset"], out[-1]["onset"] + MIN_NOTE)
    return out


def run(audio: Path, score: Path, out: Path | None, horn: str, written: bool) -> Path:
    from .refs import write_midi_notes
    notes = align(audio, score, horn, written)
    dst = out or audio.with_suffix(".mid")
    write_midi_notes(dst, notes)
    frontend.log(f"Answer key: {len(notes)} notes lined up with {audio.name}; wrote {dst}")
    return dst


def attacks(y: np.ndarray, sr: int = frontend.SR, before: float = 0.05, after: float = 0.08) -> np.ndarray:
    """Onset times that are not just a note stopping. The onset detector also
    fires on releases (the sound stopping is a change too); a metronome fit
    that locks onto releases puts every key note one note-length late. An
    onset stays when the sound within 80 ms after it gets back to at least
    0.7 of its level just before (a release followed straight away by the
    next attack still counts)."""
    times = np.array([o["t"] for o in frontend.detect_onsets(y)])
    hop = int(0.01 * sr)
    if len(y) < hop:
        return np.array([])
    frames = np.sqrt(np.mean(y[: len(y) // hop * hop].reshape(-1, hop) ** 2, axis=1))
    keep = []
    for t in times:
        i = int(t / 0.01)
        was = float(frames[max(0, i - int(before / 0.01)):i].mean()) if i > 0 else 0.0
        now = float(frames[i:i + int(after / 0.01)].max()) if i < len(frames) else 0.0
        if now >= 0.7 * was:
            keep.append(t)
    return np.array(keep)


def pitch_profile(audio: Path):
    """What pitch classes sound when: (chroma per frame, silent frames zeroed)."""
    import librosa
    y = frontend.load_mono(audio, SR)
    chroma = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0][: chroma.shape[1]]
    chroma = chroma[:, : len(rms)]
    chroma[:, rms < 0.02 * rms.max()] = 0.0
    return chroma


def pitch_agreement(chroma: np.ndarray, notes: list[dict]) -> float:
    """How well a key's pitches match what is heard under them, 0 to 1: for each
    note, the strength of its pitch class over its span (1 = the loudest class
    in every frame, 0 = silence or another note), averaged over notes."""
    if not notes or chroma.shape[1] == 0:
        return 0.0
    sums = np.concatenate([np.zeros((12, 1)), np.cumsum(chroma, axis=1)], axis=1)
    last = chroma.shape[1]
    got = []
    for n in notes:
        a = int(np.clip(n["onset"] * SR / HOP, 0, last - 1))
        b = int(np.clip(n["offset"] * SR / HOP, a + 1, last))
        got.append((sums[int(n["pitch"]) % 12, b] - sums[int(n["pitch"]) % 12, a]) / (b - a))
    return float(np.mean(got))


def align_steady(audio: Path, notes: list[dict], tempo: float,
                 chroma: np.ndarray | None = None) -> tuple[list[dict], float]:
    """Score notes lined up with a take played to a metronome: (key notes, fit).

    GRFIA-RealSax takes are played at the marked tempo, so each note sits at
    t0 + beat x 60 / tempo, give or take a few percent. Chroma DTW can't line
    up a one-pitch drill (nothing changes to lock onto) and drifted 150-270 ms
    there. This tries every start and tempo (within 3% of the marking) that
    puts a score note on a heard attack and counts how many notes land on
    one. Attacks alone can't tell the steps of a scale apart (every beat has
    one), so among the fits that land nearly as many notes as the best, the
    one whose pitches agree best with what is heard wins. Each note then
    takes an attack within 40 ms. fit is the share of notes that landed on
    one; the caller falls back to DTW when it is low."""
    onsets = attacks(frontend.load_mono(audio))
    first = min(n["start"] for n in notes)
    q = np.array([(n["start"] - first) * 60.0 / tempo for n in notes])
    if len(onsets) == 0:
        return [], 0.0
    if chroma is None:
        chroma = pitch_profile(audio)
    fits = {}
    for slope in STEADY_SLOPES:
        for j in range(min(len(onsets), 12)):
            for k in range(min(len(q), 3)):
                t0 = onsets[j] - q[k] * slope
                if t0 < -STEADY_SNAP:
                    continue          # the first note can't start before the recording
                pred = t0 + q * slope
                d = np.abs(onsets[None, :] - pred[:, None]).min(axis=1)
                hits = int((d <= STEADY_SNAP).sum())
                err = float(np.mean(np.minimum(d, 0.2)))
                fits[(round(t0, 2), round(float(slope), 3))] = (hits, err, t0, slope)
    if not fits:
        return [], 0.0

    def place(t0, slope):
        out = []
        for n, qi in zip(notes, q):
            t = max(0.0, t0 + qi * slope)
            k = int(np.argmin(np.abs(onsets - t)))
            if abs(onsets[k] - t) <= STEADY_SNAP:
                t = float(onsets[k])
            length = (n["end"] - n["start"]) * 60.0 / tempo * slope
            out.append({"onset": t, "offset": t + length, "pitch": n["pitch"], "beat": float(n["start"])})
        return tidy(out)

    most = max(f[0] for f in fits.values())
    close = [f for f in fits.values() if f[0] >= STEADY_CLOSE * most]
    best, best_rank = None, None
    for hits, err, t0, slope in close:
        key = place(t0, slope)
        rank = (round(pitch_agreement(chroma, key), 2), hits, -err)
        if best_rank is None or rank > best_rank:
            best, best_rank = (key, hits), rank
    key, hits = best
    return key, hits / len(notes)
