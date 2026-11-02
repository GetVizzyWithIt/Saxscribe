"""A take's folder on disk: where each layer lives, and take.json.

take.json is the manifest: the source file, the horn, whether the take is a
full mix, and for each layer the tool that made it and when.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import LAYOUT_VERSION


@dataclass
class Take:
    folder: Path

    @property
    def manifest(self) -> Path:
        return self.folder / "take.json"

    # Layer 1: isolate
    @property
    def source(self) -> Path:
        return self.folder / "source.wav"  # the original, decoded; the time reference for every layer

    @property
    def stems(self) -> Path:
        return self.folder / "stems"  # every Demucs stem, kept for auditioning (full mixes only)

    @property
    def stem(self) -> Path:
        return self.folder / "stem.wav"

    @property
    def accompaniment(self) -> Path:
        return self.folder / "accompaniment.wav"

    # Layer 2: contour
    @property
    def contour(self) -> Path:
        return self.folder / "contour.csv"

    # Layer 3: notes
    @property
    def notes(self) -> Path:
        return self.folder / "notes.json"

    # Layer 4: notation
    @property
    def midi(self) -> Path:
        return self.folder / "score.mid"

    def outputs(self, layer: str) -> list[Path]:
        """The files that mean a layer is done."""
        return {"isolate": [self.source, self.stem], "contour": [self.contour],
                "notes": [self.notes], "notation": [self.midi]}[layer]

    def has(self, layer: str) -> bool:
        return all(p.exists() for p in self.outputs(layer))

    def read_manifest(self) -> dict:
        if self.manifest.exists():
            return json.loads(self.manifest.read_text())
        return {"layout_version": LAYOUT_VERSION, "layers": {}}

    def write_manifest(self, data: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps(data, indent=2) + "\n")

    def record(self, layer: str, **info) -> None:
        """Notes in take.json which tool made a layer, and when."""
        data = self.read_manifest()
        data.setdefault("layers", {})[layer] = {**info, "made": time.strftime("%Y-%m-%dT%H:%M:%S")}
        self.write_manifest(data)


def default_folder(src: Path) -> Path:
    """Next to the audio file: song.wav -> song.saxscribe/"""
    return src.with_name(src.stem + ".saxscribe")
