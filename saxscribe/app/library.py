"""The library: uploaded recordings, the transcription queue, and their status.

On disk, one folder per upload:

  <library>/<id>/
    <original file name>   the upload, untouched
    take/                  the take folder the pipeline writes (four layers)
    job.json               title, horn, solo or band, and where the job is

Jobs run one at a time on a background thread, because each one already
uses the whole machine (Demucs, CREPE, Basic Pitch).
"""
from __future__ import annotations

import json
import queue
import re
import threading
import time
import traceback
from pathlib import Path

from .. import LAYERS
from ..horns import HORNS
from ..take import Take

DEFAULT = Path("~/saxscribe-library").expanduser()
AUDIO = {".wav", ".aif", ".aiff", ".flac", ".mp3", ".m4a", ".ogg", ".opus", ".mp4", ".aac"}

STAGES = {  # what each layer is doing, in words for the page
    "isolate": "Separating the sax from the band",
    "contour": "Following the pitch",
    "notes": "Finding the notes and the beat",
    "notation": "Writing the sheet music",
}


def slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return s[:40] or "take"


class Library:
    def __init__(self, root: Path | None = None, inline: bool = False):
        """inline=True runs each job inside add() instead of on the worker (for tests)."""
        self.root = Path(root or DEFAULT).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.inline = inline
        self.jobs: queue.Queue[str] = queue.Queue()
        self.lock = threading.Lock()
        self.worker: threading.Thread | None = None
        # Anything left mid-run by a restart goes back in the queue.
        for item in self.list():
            if item["state"] in ("queued", "running"):
                self._set(item["id"], state="queued")
                self._enqueue(item["id"])

    # ---------------------------------------------------------------- reading

    def folder(self, take_id: str) -> Path:
        if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-z0-9-]+", take_id):
            raise KeyError(take_id)
        f = self.root / take_id
        if not (f / "job.json").exists():
            raise KeyError(take_id)
        return f

    def take(self, take_id: str) -> Take:
        return Take(self.folder(take_id) / "take")

    def job(self, take_id: str) -> dict:
        f = self.folder(take_id)
        data = json.loads((f / "job.json").read_text())
        take = Take(f / "take")
        done = [layer for layer in LAYERS if take.has(layer)]
        data["id"] = take_id
        data["layers_done"] = len(done)
        if data["state"] == "running":
            nxt = next((layer for layer in LAYERS if layer not in done), "notation")
            data["stage"] = STAGES[nxt]
        if data["state"] == "done":
            data["files"] = sorted(p.name for p in take.folder.iterdir() if p.is_file())
        return data

    def list(self) -> list[dict]:
        out = []
        for f in sorted(self.root.iterdir(), reverse=True):
            if (f / "job.json").exists():
                try:
                    out.append(self.job(f.name))
                except (KeyError, ValueError):
                    continue
        return out

    # ---------------------------------------------------------------- adding

    def add(self, filename: str, data: bytes, *, horn: str = "alto", mix: bool = False,
            title: str | None = None) -> str:
        name = Path(filename).name
        if Path(name).suffix.lower() not in AUDIO:
            raise ValueError(f"{name} is not an audio file this tool reads "
                             f"({', '.join(sorted(AUDIO))})")
        if horn not in HORNS:
            raise ValueError(f"unknown horn {horn}")
        stem = Path(name).stem
        take_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(stem)}"
        while (self.root / take_id).exists():
            take_id += "-2"
        f = self.root / take_id
        f.mkdir(parents=True)
        safe = re.sub(r"[^A-Za-z0-9 ._()-]+", "_", name)
        (f / safe).write_bytes(data)
        (f / "job.json").write_text(json.dumps({
            "title": title or stem, "filename": safe, "horn": horn, "mix": mix,
            "state": "queued", "added": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, indent=1) + "\n")
        self._enqueue(take_id)
        return take_id

    def _set(self, take_id: str, **fields) -> None:
        with self.lock:
            path = self.root / take_id / "job.json"
            data = json.loads(path.read_text())
            data.update(fields)
            path.write_text(json.dumps(data, indent=1) + "\n")

    def _enqueue(self, take_id: str) -> None:
        if self.inline:
            self.run(take_id)
            return
        self.jobs.put(take_id)
        if self.worker is None or not self.worker.is_alive():
            self.worker = threading.Thread(target=self._work, name="saxscribe-jobs", daemon=True)
            self.worker.start()

    def _work(self) -> None:
        while True:
            self.run(self.jobs.get())

    def run(self, take_id: str) -> None:
        from ..pipeline import transcribe
        f = self.root / take_id
        job = json.loads((f / "job.json").read_text())
        self._set(take_id, state="running", started=time.strftime("%Y-%m-%dT%H:%M:%S"))
        try:
            transcribe(f / job["filename"], f / "take", mix=job["mix"], horn=job["horn"])
        except (Exception, SystemExit) as exc:
            self._set(take_id, state="failed", error=str(exc) or type(exc).__name__,
                      trace=traceback.format_exc()[-4000:])
            return
        self._set(take_id, state="done", finished=time.strftime("%Y-%m-%dT%H:%M:%S"))
