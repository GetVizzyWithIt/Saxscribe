"""MVSep's Mega separator, used here only for its vocal stem (rule V, log E82).

Mega is a BS-RoFormer trained by MVSep (ZFTurbo) to split a mix into 53
instruments, voice and saxophone among them. Because voice and sax compete for
the same sound inside one model, Mega keeps a sax out of its "vocal" stem;
Demucs puts the sax there on some instrumentals (Pennies From Heaven, Blues for
Mary Jane), which is why the vocal check uses Mega (E82 round 3).

Weights: mvsep_mega_model_bs_roformer_53_stems_v1.ckpt and its .yaml, from the
v1.0.21 release of github.com/ZFTurbo/Music-Source-Separation-Training (an MIT
repo; the release states no separate terms for the weights). They are not
downloaded automatically (1.4 GB): copy or link both files into the models
folder (~/.cache/saxscribe/models, or SAXSCRIBE_MODELS). Each file is checked
against a fixed sha256, the checkpoint loads with torch's safe loader, and the
yaml with a safe loader that also allows tuples.

Speed on the M3 Pro's GPU, vocal stem only: about 1.3 times the length of the
audio (76 s per minute over 41 minutes, model load included). Only the stems
asked for are computed (one mask head instead of 53); the GPU is about 1.6
times faster than the CPU, with the same output.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path

import numpy as np

from . import frontend
from .filosax import models_dir, sha256

WEIGHTS = {
    "checkpoint": dict(file="mvsep_mega_model_bs_roformer_53_stems_v1.ckpt",
                       sha256="c62820893bbf86d4e734f966bd142d9157cfc8bb8e79e9d8f9ea553f3ff3519f"),
    "config": dict(file="mvsep_mega_model_bs_roformer_53_stems.yaml",
                   sha256="7e198062a251587088adb91215a4f44ab59e67bd62fcc805cf54d6e7dfc51103"),
}
RATE = 44100
VOCAL = "vocal"   # Mega's all-vocals stem (it also has lead-vocal and back-vocal)


def installed() -> bool:
    return all((models_dir() / w["file"]).exists() for w in WEIGHTS.values())


@functools.lru_cache(maxsize=None)
def checked(name: str) -> Path:
    """The file's path once its fingerprint matches (checked once per run)."""
    w = WEIGHTS[name]
    path = models_dir() / w["file"]
    if not path.exists():
        raise FileNotFoundError(f"{path} is not installed: copy Mega's {w['file']} into {models_dir()}")
    got = sha256(path)
    if got != w["sha256"]:
        raise ValueError(f"{path} has the wrong fingerprint ({got[:12]}..., expected {w['sha256'][:12]}...)")
    return path


def load_config(path: Path) -> dict:
    """The model's yaml. It tags tuples as !!python/tuple, which yaml's safe loader refuses;
    this loader accepts that one tag and nothing else that could build Python objects."""
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_constructor("tag:yaml.org,2002:python/tuple", lambda loader, node: tuple(loader.construct_sequence(node)))
    return yaml.load(path.read_text(), Loader=Loader)


def load_model(device: str = "cpu"):
    import torch
    from .vendor.bs_roformer import BSRoformer

    config = load_config(checked("config"))
    model = BSRoformer(**dict(config["model"]))
    state = torch.load(checked("checkpoint"), map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    return model.to(device).eval(), config


def device() -> str:
    """Apple's GPU when there is one (about 1.6x faster than the CPU on the M3 Pro, same output);
    SAXSCRIBE_MEGA_DEVICE=cpu forces the CPU."""
    if os.environ.get("SAXSCRIBE_MEGA_DEVICE"):
        return os.environ["SAXSCRIBE_MEGA_DEVICE"]
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


def separate(wav: Path, out_dir: Path, stems: tuple[str, ...] = (VOCAL,)) -> dict[str, Path]:
    """Writes <out_dir>/mega_<stem>.wav (mono, 44.1 kHz, 16 bit) for each stem asked for."""
    import soundfile as sf

    dev = device()
    model, config = load_model(dev)
    names = list(config["training"]["instruments"])
    ids = [names.index(s) for s in stems]
    frontend.log(f"Separating {', '.join(stems)} with MVSep's Mega model on {dev} ...")
    y = _load(wav)
    out = demix(model, y, ids, int(config["inference"]["chunk_size"]), int(config["inference"]["num_overlap"]), dev)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for s, x in zip(stems, out):
        paths[s] = out_dir / f"mega_{s}.wav"
        tmp = paths[s].with_suffix(".tmp.wav")
        sf.write(tmp, np.clip(x.mean(axis=0), -1, 1), RATE, subtype="PCM_16")
        tmp.replace(paths[s])
    return paths


def _load(wav: Path) -> np.ndarray:
    import librosa
    y, _ = librosa.load(str(wav), sr=RATE, mono=False)
    y = np.atleast_2d(y)
    return np.repeat(y, 2, 0) if y.shape[0] == 1 else y[:2]


def window(size: int, fade: int):
    import torch
    w = torch.ones(size)
    w[-fade:] = torch.linspace(1, 0, fade)
    w[:fade] = torch.linspace(0, 1, fade)
    return w


def demix(model, mix: np.ndarray, ids: list[int], chunk: int, overlap: int, dev: str = "cpu") -> np.ndarray:
    """MSST's demix (utils/model_utils.py @ea7eb9c, generic mode, batch 1) for the stems in ids:
    overlapping chunks with linear fades, reflect padding at both ends. Returns (stems, channels, time)."""
    import torch
    from torch import nn

    x = torch.tensor(mix, dtype=torch.float32)
    fade, step = chunk // 10, chunk // overlap
    border = chunk - step
    length = x.shape[-1]
    padded = length > 2 * border and border > 0
    if padded:
        x = nn.functional.pad(x, (border, border), mode="reflect")
    base = window(chunk, fade)
    result = torch.zeros((len(ids),) + tuple(x.shape))
    counter = torch.zeros_like(result)
    total, i, shown = x.shape[1], 0, 0
    with torch.inference_mode():
        while i < total:
            part = x[:, i:i + chunk]
            n = part.shape[-1]
            part = nn.functional.pad(part, (0, chunk - n), mode="reflect" if n > chunk // 2 else "constant", value=0)
            out = model(part[None].to(dev), active_stem_ids=ids)[0].cpu()
            w = base.clone()
            if i == 0:
                w[:fade] = 1
            elif i + step >= total:
                w[-fade:] = 1
            result[..., i:i + n] += out[..., :n] * w[:n]
            counter[..., i:i + n] += w[:n]
            i += step
            if 10 * i // total > shown:
                shown = 10 * i // total
                frontend.log(f"  Mega: {min(100, 10 * shown)}%")
    est = (result / counter).numpy()
    np.nan_to_num(est, copy=False, nan=0.0)
    return est[..., border:-border] if padded else est
