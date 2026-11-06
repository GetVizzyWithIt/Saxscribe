"""Riley and Dixon's sax models, trained on Filosax (opt-in).

Two models from Xavier Riley and Simon Dixon (Queen Mary University of London),
both MIT licensed and published on Hugging Face:

  separator    a Demucs v3 (hybrid) model trained to pull a sax out of a band:
               two stems, "Sax" and "BackingMono". Runs under our Demucs 4.
               --separator filosax
  transcriber  Kong's piano transcription model fine-tuned on Filosax
               (Riley and Dixon 2024, arXiv 2405.16687): sax notes straight
               from the stem, no pitch line needed. --notes-tool filosax

Measured 2026-11-05 on the Mac, note F1 against human keys:
  Weimar, 6 solos      Demucs + Basic Pitch 57.3, Filosax both 76.3
  4 tenor pop/fusion   32.5 -> 36.1 (Filosax separator + Basic Pitch 37.3)
  Pennies From Heaven  50.1 -> 57.7
  Blues for Mary Jane  56.2 -> 52.0 (the one record that gets worse)

Weights are downloaded once into ~/.cache/saxscribe/models (or the folder in
SAXSCRIBE_MODELS) and checked against a fixed sha256 before use; both load
with torch's safe loader, so a checkpoint can't run code.
"""
from __future__ import annotations

import codecs
import hashlib
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path

import numpy as np

from . import frontend

HF = "https://huggingface.co"
WEIGHTS = {
    "separator": dict(file="filosax_demucs_v3_14.22_SDR.th", repo="xavriley/demucs_v3_saxophone_separation",
                      sha256="4a801bc00f0e21d476edef1d9fa25dbcb088e3bae0a4092e590167ae26dbe360"),
    "transcriber": dict(file="filosax_25k.pth", repo="xavriley/midi-transcription-models",
                        sha256="448cf2c8ea6d4b77f7435f5b9a496211ea60300c5c17fa9c754da764f75f3a6a"),
}
SAX, BACKING = "saxophone", "backing"  # stem file names (the model calls them Sax and BackingMono)
THRESHOLDS = dict(onset_threshold=0.3, offset_threshold=0.3, frame_threshold=0.1)  # the package defaults, as measured


def models_dir() -> Path:
    return Path(os.environ.get("SAXSCRIBE_MODELS") or Path.home() / ".cache" / "saxscribe" / "models").expanduser()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def weights(name: str) -> Path:
    """The checkpoint's path, downloading it the first time. Refuses a file whose hash is wrong."""
    w = WEIGHTS[name]
    path = models_dir() / w["file"]
    if not path.exists():
        url = f"{HF}/{w['repo']}/resolve/main/{w['file']}"
        frontend.log(f"Downloading the Filosax {name} ({w['file']}, once) from {url}")
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".part")
        os.close(fd)
        try:
            with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            if sha256(Path(tmp)) != w["sha256"]:
                raise SystemExit(f"The downloaded {w['file']} is not the file that was tested (sha256 differs); not using it.")
            os.replace(tmp, path)
        finally:
            Path(tmp).unlink(missing_ok=True)
    elif sha256(path) != w["sha256"]:
        raise SystemExit(f"{path} is not the file that was tested (sha256 differs). Delete it to download it again.")
    return path


# ---------------------------------------------------------------- separator

def separate(wav: Path, out_dir: Path, device: str = "cpu") -> dict[str, Path]:
    """Writes saxophone.wav and backing.wav (44.1 kHz stereo). CPU is as fast as MPS here (~6 s per minute)."""
    import soundfile as sf
    import torch
    from demucs.apply import apply_model
    from demucs.hdemucs import HDemucs
    from demucs.states import load_model

    with torch.serialization.safe_globals([HDemucs]):
        model = load_model(torch.load(weights("separator"), map_location="cpu", weights_only=True))
    model.eval()
    frontend.log(f"Separating the sax with the Filosax model on {device}...")
    y, _ = _load(wav, model.samplerate)
    mix = torch.tensor(y, dtype=torch.float32)
    ref = mix.mean(0)
    mean, std = ref.mean(), ref.std() + 1e-8
    with torch.no_grad():
        src = apply_model(model, ((mix - mean) / std)[None], device=device, shifts=1, split=True,
                          overlap=0.25, progress=False)[0] * std + mean
    out_dir.mkdir(parents=True, exist_ok=True)
    stems = {}
    for source, x in zip(model.sources, src):
        name = SAX if source.lower() == "sax" else BACKING
        stems[name] = out_dir / f"{name}.wav"
        sf.write(stems[name], x.cpu().numpy().T, model.samplerate)
    return stems


def _load(wav: Path, rate: int) -> tuple[np.ndarray, int]:
    import librosa
    y, _ = librosa.load(str(wav), sr=rate, mono=False)
    y = np.atleast_2d(y)
    return (np.repeat(y, 2, 0) if y.shape[0] == 1 else y[:2]), rate


# ---------------------------------------------------------------- transcriber

def load_transcriber(path: Path | None = None, device: str = "cpu"):
    import numpy
    import torch
    from .vendor import kong

    try:
        from numpy._core.multiarray import _reconstruct  # numpy 2 renamed numpy.core
    except ImportError:
        from numpy.core.multiarray import _reconstruct
    # The weights file was saved under numpy 1 (numpy.core); files saved under
    # numpy 2 name the same function numpy._core. Allow both spellings.
    torch.serialization.add_safe_globals([
        (_reconstruct, "numpy.core.multiarray._reconstruct"),
        (_reconstruct, "numpy._core.multiarray._reconstruct"), numpy.ndarray, numpy.dtype,
        codecs.encode, type(numpy.dtype("float64")), type(numpy.dtype("int64"))])
    model = kong.Regress_onset_offset_frame_velocity_CRNN()
    state = torch.load(path or weights("transcriber"), map_location="cpu", weights_only=True)["model"]
    model.load_state_dict(state, strict=True)
    return model.to(device).eval()


def transcribe(stem: Path, model=None) -> list[dict]:
    """Notes [{onset, offset, pitch, amp}] from a sax stem, in seconds and concert MIDI numbers."""
    from .vendor import kong
    model = model or load_transcriber()
    frontend.log("Finding notes with the Filosax transcriber (CPU, ~9 s per minute)...")
    audio = frontend.load_mono(stem, sr=kong.SAMPLE_RATE)
    found = kong.decode(kong.run_model(model, audio), **THRESHOLDS)
    # A note whose sub-frame end lands before its start is kept, one frame long.
    return [{"onset": n["onset"], "offset": max(n["offset"], n["onset"] + 1 / kong.FRAMES_PER_SECOND),
             "pitch": n["pitch"], "amp": min(n["velocity"] / 127, 1.0)}
            for n in sorted(found, key=lambda n: (n["onset"], n["pitch"]))]
