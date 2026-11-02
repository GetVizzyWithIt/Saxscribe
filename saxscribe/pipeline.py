"""Runs the four layers in order, skipping any already on disk.

A layer runs when its files are missing, when --redo names it or a layer
below it, or when a layer below it just ran. Lower layers are never deleted
to make a higher one, so a hand-fixed notes.json survives --redo notation.
"""
from __future__ import annotations

from pathlib import Path

from . import LAYERS, frontend
from .horns import HORNS
from .layers import contour, isolate, notation, notes
from .take import Take, default_folder


def transcribe(src: Path, out: Path | None = None, *, mix: bool = False, stem: str | None = None,
               horn: str = "alto", redo: str | None = None, contour_tool: str = "auto",
               notes_tool: str = "auto", swing: str = "auto") -> Take:
    src = Path(src).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"No such file: {src}")
    take = Take(Path(out).expanduser().resolve() if out else default_folder(src))
    h = HORNS[horn]
    manifest = take.read_manifest()
    manifest.update({"source": str(src), "horn": horn, "mix": mix})
    take.write_manifest(manifest)

    start = LAYERS.index(redo) if redo else len(LAYERS)
    for i, layer in enumerate(LAYERS):
        if not take.has(layer):
            start = min(start, i)
    if start == len(LAYERS):
        frontend.log(f"All four layers are already in {take.folder} (use --redo to remake one).")
        return take

    steps = {
        "isolate": lambda: isolate.run(take, src, mix, stem),
        "contour": lambda: contour.run(take, h, contour_tool),
        "notes": lambda: notes.run(take, h, notes_tool),
        "notation": lambda: notation.run(take, h, swing),
    }
    for layer in LAYERS[start:]:
        steps[layer]()
    frontend.log(f"Done: {take.folder}")
    return take
