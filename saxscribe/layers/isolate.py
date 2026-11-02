"""Layer 1: get the sax on its own.

A solo take is passed through: stem.wav is a copy of the source. A full mix
goes through Demucs; every stem is kept in stems/ so you can listen and pick
another with --stem, and accompaniment.wav is everything else added together.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from .. import frontend
from ..take import Take

DEFAULT_STEM = "other"  # where sax usually lands in Demucs' six stems


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
    name = stem or DEFAULT_STEM
    if name not in stems:
        raise SystemExit(f"No stem called {name!r}. Stems: {', '.join(sorted(stems))}")
    shutil.copyfile(stems[name], take.stem)
    write_accompaniment(take.accompaniment, [p for n, p in stems.items() if n != name])
    take.record("isolate", tool="demucs htdemucs_6s", stem=name, source=str(src),
                stems=sorted(stems))
    frontend.log(f"Using the {name!r} stem. Others are in {take.stems} to listen to.")


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
