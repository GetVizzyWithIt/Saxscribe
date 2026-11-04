"""Layer 2: the continuous pitch line, every 10 ms, never thrown away.

This is the layer that answers "what did he do on that bend". contour.csv has
one row per frame:

  time      seconds from the start of source.wav
  f0_hz     the pitch tracker's frequency (blank where pYIN heard nothing)
  midi      the same pitch as a MIDI number with decimals (60.5 = C4 + 50 cents)
  confidence  0 to 1, how sure the tracker is there is one clear pitch
  voiced    1 where the sax is sounding, 0 in silence or noise

CREPE (via torchcrepe) is used when installed; pYIN from librosa otherwise.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .. import frontend
from ..horns import CREPE_MAX_HZ, Horn
from ..take import Take

RATE = 16000
HOP = 160  # 10 ms
FRAME_SECONDS = HOP / RATE


def crepe_available() -> bool:
    import importlib.util
    return importlib.util.find_spec("torchcrepe") is not None


def track(y: np.ndarray, lo: float, hi: float, tool: str = "auto"):
    """(f0 Hz, confidence, voiced, tool name) for audio at 16 kHz, one value per 10 ms."""
    import librosa
    if tool in ("auto", "crepe") and crepe_available():
        import torch
        import torchcrepe
        device = frontend.best_torch_device()
        audio = torch.tensor(y, dtype=torch.float32)[None]
        try:
            f0, conf = torchcrepe.predict(audio, RATE, HOP, lo, min(hi, CREPE_MAX_HZ), "full", batch_size=512,
                                          device=device, return_periodicity=True)
        except Exception as exc:  # some GPU ops are missing on some machines
            frontend.log(f"CREPE failed on {device} ({exc}); retrying on the CPU.")
            f0, conf = torchcrepe.predict(audio, RATE, HOP, lo, min(hi, CREPE_MAX_HZ), "full", batch_size=512,
                                          device="cpu", return_periodicity=True)
        conf = torchcrepe.filter.median(conf, 3)[0].cpu().numpy()
        f0 = f0[0].cpu().numpy()
        rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0]
        rms = np.pad(rms, (0, max(0, len(f0) - len(rms))))[: len(f0)]
        voiced = (conf > 0.5) & (rms > 0.01 * (rms.max() or 1.0))
        return f0, conf, voiced, "torchcrepe full"
    if tool == "crepe":
        raise SystemExit("torchcrepe is not installed; use --contour-tool pyin or install it.")
    f0, voiced, prob = librosa.pyin(y, fmin=lo, fmax=hi, sr=RATE, frame_length=1024,
                                    hop_length=HOP)
    return f0, np.nan_to_num(prob), voiced, "pyin"


def run(take: Take, horn: Horn, tool: str = "auto") -> None:
    frontend.log("Layer 2/4: pitch contour")
    y = frontend.load_mono(take.stem, sr=RATE)
    f0, conf, voiced, name = track(y, horn.min_hz, horn.max_hz, tool)
    write(take.contour, f0, conf, voiced)
    take.record("contour", tool=name, frame_seconds=FRAME_SECONDS)
    frontend.log(f"  {name}: {int(np.sum(voiced))} of {len(f0)} frames voiced")


def write(path: Path, f0: np.ndarray, conf: np.ndarray, voiced: np.ndarray) -> None:
    with path.open("w", newline="") as fh:
        out = csv.writer(fh)
        out.writerow(["time", "f0_hz", "midi", "confidence", "voiced"])
        for k, (hz, c, v) in enumerate(zip(f0, conf, voiced)):
            ok = np.isfinite(hz) and hz > 0
            out.writerow([f"{k * FRAME_SECONDS:.3f}",
                          f"{hz:.2f}" if ok else "",
                          f"{69 + 12 * np.log2(hz / 440.0):.3f}" if ok else "",
                          f"{float(c):.3f}", int(bool(v))])


def read(path: Path) -> dict[str, np.ndarray]:
    """contour.csv as arrays: time, f0_hz, midi, confidence (NaN where blank), voiced (bool)."""
    cols: dict[str, list] = {"time": [], "f0_hz": [], "midi": [], "confidence": [], "voiced": []}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            for key in ("time", "f0_hz", "midi", "confidence"):
                cols[key].append(float(row[key]) if row[key] != "" else np.nan)
            cols["voiced"].append(row["voiced"] == "1")
    return {k: np.array(v, dtype=bool if k == "voiced" else float) for k, v in cols.items()}
