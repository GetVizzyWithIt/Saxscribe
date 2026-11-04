"""Audio front end: decode, separate, beats, onsets, Basic Pitch notes.

Copied from the Songs in the Key of Life analyzer (analyzer/analyze.py at
commit 18a6548) and kept as a private copy on purpose. The game reduces a part
into something playable; this tool must stay faithful to it. Nothing here is
imported from the game, and nothing from its chart model came over, so the two
can drift apart without either one pulling the other along.

What changed from the game's copy:
  - Profiles (lanes, difficulties) are gone; callers pass a pitch range.
  - Basic Pitch keeps short notes (50 ms, not 80 ms): fast runs are the point.
  - Beat detection takes a file only; the librosa fallback loads it itself.
"""
from __future__ import annotations

import contextlib
import io
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 22050
HOP = 256  # about 11.6 ms per analysis frame


def log(msg: str) -> None:
    print(f"[saxscribe] {msg}", flush=True)


# ---------------------------------------------------------------- decoding

def decode(src: Path, dst_wav: Path, rate: int = 44100) -> None:
    """Any audio file to a 44.1 kHz stereo WAV, with ffmpeg."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn",
                    "-ac", "2", "-ar", str(rate), str(dst_wav)], check=True)


def load_mono(path: Path, sr: int = SR) -> np.ndarray:
    import librosa
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    return y


# ---------------------------------------------------------------- stems

def demucs_available() -> bool:
    try:
        import demucs  # noqa: F401
        return True
    except ImportError:
        return False


def best_torch_device() -> str:
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon GPU
        if torch.cuda.is_available():
            return "cuda"
    except Exception as exc:
        log(f"PyTorch problem ({exc}); using the CPU.")
    return "cpu"


DEMUCS_SHIFTS = 2   # average two shifted passes: more notes found on band records for ~50% more time (log E30)


def separate_stems(wav: Path, out_dir: Path) -> dict[str, Path]:
    """Runs Demucs' 6-stem model. Returns {stem name: wav path}.

    No Demucs model has a sax stem; sax usually lands in "other".
    """
    work = Path(tempfile.mkdtemp(prefix="demucs-"))
    device = best_torch_device()
    log(f"Separating stems with Demucs on {device} (the slow step; a few minutes)...")
    cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs_6s", "-d", device,
           "--shifts", str(DEMUCS_SHIFTS), "-o", str(work), "--filename", "{stem}.{ext}", str(wav)]
    result = subprocess.run(cmd)
    if result.returncode != 0 and device != "cpu":
        log("Demucs failed on the GPU, retrying on the CPU...")
        cmd[cmd.index("-d") + 1] = "cpu"
        subprocess.run(cmd, check=True)
    elif result.returncode != 0:
        raise RuntimeError("Demucs failed")
    produced = {p.stem: p for p in (work / "htdemucs_6s").glob("*.wav")}
    out_dir.mkdir(parents=True, exist_ok=True)
    stems = {}
    for name, path in produced.items():
        dst = out_dir / f"{name}.wav"
        shutil.move(str(path), dst)
        stems[name] = dst
    shutil.rmtree(work, ignore_errors=True)
    return stems


# ---------------------------------------------------------------- beats

def detect_beats(wav: Path) -> tuple[list[float], list[float], str]:
    """Returns (beat times, downbeat times, tool name)."""
    try:
        from beat_this.inference import File2Beats
        device = best_torch_device()
        try:
            f2b = File2Beats(checkpoint_path="final0", device=device, dbn=False)
            beats, downbeats = f2b(str(wav))
        except Exception:  # some GPU ops are missing on some machines
            f2b = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
            beats, downbeats = f2b(str(wav))
        if len(beats) >= 8:
            return [float(b) for b in beats], [float(d) for d in downbeats], "beat_this"
        log("Beat This! found too few beats; falling back to librosa.")
    except ImportError:
        pass
    except Exception as exc:  # e.g. model download blocked
        log(f"Beat This! unavailable ({exc}); falling back to librosa.")
    import librosa
    y = load_mono(wav)
    _, frames = librosa.beat.beat_track(y=y, sr=SR, hop_length=HOP, units="frames")
    beats = librosa.frames_to_time(frames, sr=SR, hop_length=HOP).tolist()
    return beats, guess_downbeats(y, beats), "librosa"


def guess_downbeats(y: np.ndarray, beats: list[float]) -> list[float]:
    """Without a downbeat model: assume 4/4 and pick the phase with the most low-end energy."""
    import librosa
    if len(beats) < 8:
        return beats[::4]
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
    low = S[freqs < 200].sum(axis=0)
    frames = librosa.time_to_frames(beats, sr=SR, hop_length=HOP)
    frames = np.clip(frames, 0, len(low) - 1)
    energy = low[frames]
    phase = int(np.argmax([energy[p::4].mean() for p in range(4)]))
    return beats[phase::4]


# ---------------------------------------------------------------- onsets

def detect_onsets(y: np.ndarray) -> list[dict]:
    """Note attacks with a strength from 0 to about 1."""
    import librosa
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    frames = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP,
                                        backtrack=False, units="frames")
    if len(frames) == 0:
        return []
    scale = float(np.percentile(env[frames], 95)) or 1.0
    times = librosa.frames_to_time(frames, sr=SR, hop_length=HOP)
    return [{"t": round(float(t), 4), "s": round(min(1.5, float(env[f]) / scale), 3)}
            for t, f in zip(times, frames)]


# ---------------------------------------------------------------- notes

def basic_pitch_available() -> bool:
    import importlib.util
    return importlib.util.find_spec("basic_pitch") is not None


BP_SHORTEST = (50.0, 127.7)   # ms: range for Basic Pitch's shortest note
BP_SPACING_SHARE = 0.4        # shortest note = this share of the take's typical gap between notes


def note_spacing(onsets: list[float]) -> float:
    """The take's typical gap between note starts in seconds (median; starts
    closer than 10 ms count as one), or 0 when there are too few notes."""
    starts = np.unique(np.round(np.asarray(sorted(onsets)), 2))
    gaps = np.diff(starts)
    return float(np.median(gaps)) if len(gaps) >= 4 else 0.0


def basic_pitch_notes(wav: Path, min_hz: float, max_hz: float, by_spacing: bool = True,
                      info: dict | None = None) -> list[dict]:
    """Basic Pitch note events: [{onset, offset, pitch (MIDI), amp}].

    Basic Pitch is built for any instrument and may return overlapping notes;
    the notes layer makes them one line for a single horn.

    by_spacing (the default): the network runs once and its output is read
    twice. The first read (shortest note 50 ms, Basic Pitch's melodia step on)
    measures how far apart this take's notes usually start; the second keeps
    notes of at least 0.4 of that gap (50-128 ms) with the melodia step off.
    Ghost and split notes are short next to the line around them, so a slow
    melody sheds them while fast bebop keeps its short notes. Measured on
    2026-11-03 (note F1): GRFIA alto +9.0, tenor +10.5, Blues for Mary Jane
    +2.0, Omnibook -0.2. On fast lines (notes under 200 ms apart) a short
    note the second read drops comes back when the recording confirms it
    (restore_short), so fast real notes are kept.
    by_spacing=False is the old fixed 50 ms read.
    info, when given, gets the gap and the shortest note used.
    """
    logging.getLogger().setLevel(logging.ERROR)  # Basic Pitch warns about optional backends
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.constants import AUDIO_SAMPLE_RATE, FFT_HOP
    from basic_pitch.inference import run_inference
    from basic_pitch.note_creation import model_output_to_notes

    def infer():
        # Basic Pitch's Core ML backend prints debug lines for every chunk; hide them.
        with contextlib.redirect_stdout(io.StringIO()):
            return run_inference(str(wav), ICASSP_2022_MODEL_PATH)
    try:
        output = infer()
    except Exception as exc:
        # Seen on Macs: the very first call fails while the model loads,
        # and the next one works. Try once more before giving up.
        log(f"Basic Pitch failed once ({exc}); trying again...")
        output = infer()

    def read(shortest_ms: float, melodia: bool) -> list[dict]:
        frames = int(np.round(shortest_ms / 1000 * (AUDIO_SAMPLE_RATE / FFT_HOP)))
        with contextlib.redirect_stdout(io.StringIO()):
            _, events = model_output_to_notes(output, onset_thresh=0.5, frame_thresh=0.3,
                                              min_note_len=frames, min_freq=min_hz, max_freq=max_hz,
                                              melodia_trick=melodia)
        notes = [{"onset": float(s), "offset": float(e), "pitch": int(p), "amp": float(a)}
                 for s, e, p, a, *_ in events]
        notes.sort(key=lambda n: (n["onset"], n["pitch"]))
        return notes

    notes = read(BP_SHORTEST[0], True)
    if not by_spacing:
        return notes
    gap = note_spacing([n["onset"] for n in notes])
    if not gap:
        return notes
    shortest = float(np.clip(BP_SPACING_SHARE * gap * 1000, *BP_SHORTEST))
    kept = read(shortest, False)
    back = []
    if gap < RESTORE_FAST:
        attacks = [o for o in detect_onsets(load_mono(wav)) if o["s"] >= RESTORE_STRENGTH]
        back = restore_short(notes, kept, [o["t"] for o in attacks])
    retongued = restore_dipped(notes, kept + back, level_db(load_mono(wav, sr=DIP_RATE)))
    if info is not None:
        info.update(spacing_ms=round(gap * 1000, 1), shortest_ms=round(shortest, 1), restored=len(back),
                    restored_after_dip=len(retongued))
    return sorted(kept + back + retongued, key=lambda n: (n["onset"], n["pitch"]))


RESTORE_NEAR = 0.04       # s: a short note the long read already has (a note starting this close)
RESTORE_ATTACK = 0.03     # s: an attack this close confirms a short note
RESTORE_STRENGTH = 0.3    # onset strength (0-1) that counts as an attack
RESTORE_FAST = 0.2        # s: only lines whose notes start closer than this (fast playing) get notes back.
                          # Omnibook (151 ms): 137 of 490 lost real notes back, F1 -0.23 -> -0.01; on
                          # slow GRFIA takes (~350 ms) restored notes were nearly all extras (tenor 1 of 33).


DIP_RATE = 44100
DIP_DB = 10.0             # dB: a short note comes back when the level dips this far just before it
DIP_BEFORE = 6            # 10 ms frames looked at before the note (60 ms), plus its first frame


def level_db(y: np.ndarray) -> np.ndarray:
    """Loudness in dB per 10 ms frame (frame k centred at k x 10 ms), at DIP_RATE."""
    import librosa
    hop = DIP_RATE // 100
    r = librosa.feature.rms(y=y, frame_length=2 * hop, hop_length=hop)[0]
    return 20 * np.log10(np.maximum(r, 1e-6))


def restore_dipped(short_read: list[dict], kept: list[dict], db: np.ndarray) -> list[dict]:
    """Short notes the second read dropped that start after a clear dip in level
    (at least 10 dB below the note's own median, within 60 ms before it): a
    re-tongued note, often the same pitch again, which a slow classical line
    is full of. URMP lost 221 real notes to the longer shortest note, 78% of
    them repeats; this brings back about half (119 of 150 restored were real,
    onset recall loss -15.5 -> -8.1 points) at a cost under 1.5 points of
    note F1 elsewhere (2026-11-03). Any pitch, any speed."""
    starts = np.array(sorted(n["onset"] for n in kept)) if kept else np.array([])
    back = []
    for n in short_read:
        if len(starts) and np.min(np.abs(starts - n["onset"])) <= RESTORE_NEAR:
            continue
        i0, i1 = int(n["onset"] * 100), int(n["offset"] * 100) + 1
        if i0 >= len(db):
            continue
        own = float(np.median(db[i0:i1])) if i1 > i0 else float(db[i0])
        before = db[max(0, i0 - DIP_BEFORE):i0 + 1]
        if len(before) and own - float(before.min()) >= DIP_DB:
            back.append(dict(n))
    return back


def restore_short(short_read: list[dict], kept: list[dict], attacks: list[float]) -> list[dict]:
    """Short notes the second read dropped that the recording confirms: a clear
    attack at their start and a pitch different from the notes on both sides
    (a split note or a ghost repeats its neighbour's pitch; a fast bebop note
    moves). Returned to be added back, so a real fast note is never lost to
    the longer shortest-note setting."""
    starts = np.array(sorted(n["onset"] for n in kept)) if kept else np.array([])
    hits = np.array(sorted(attacks)) if attacks else np.array([])
    line = sorted(kept, key=lambda n: n["onset"])
    on = [n["onset"] for n in line]
    back = []
    for n in short_read:
        if len(starts) and np.min(np.abs(starts - n["onset"])) <= RESTORE_NEAR:
            continue
        if not len(hits) or np.min(np.abs(hits - n["onset"])) > RESTORE_ATTACK:
            continue
        i = int(np.searchsorted(on, n["onset"]))
        sides = [line[j]["pitch"] for j in (i - 1, i) if 0 <= j < len(line)]
        if any(p == n["pitch"] for p in sides):
            continue
        back.append(dict(n))
    return back
