"""The library: uploaded recordings, the transcription queue, and their status.

On disk, one folder per upload:

  <library>/<id>/
    <original file name>   the upload, untouched
    take/                  the take folder the pipeline writes (four layers)
    job.json               title, horn, solo or band, and where the job is
    log.txt                what the pipeline printed while it ran (shown on the page)

Jobs run one at a time, because each one already uses the whole machine
(Demucs, CREPE, Basic Pitch). Each runs as its own `python -m saxscribe
transcribe` process, so Stop can end it at once and everything it prints
(including Demucs' progress) lands in log.txt for the page.
"""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
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


def last_lines(path: Path, n: int = 3) -> list[str]:
    """The last n lines of a log, reading progress bars (\\r) as new lines."""
    if not path.exists():
        return []
    with open(path, "rb") as f:
        f.seek(max(0, path.stat().st_size - 8000))
        text = f.read().decode("utf-8", "replace")
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    return lines[-n:]


# How notes are found. standard: Demucs + Basic Pitch with the sax-rest and
# bleed checks. filosax: Riley and Dixon's sax separator and transcriber
# (saxscribe/filosax.py), an opt-in test while it is compared on more records.
ENGINES = ("standard", "filosax")

class Library:
    def __init__(self, root: Path | None = None, inline: bool = False):
        """inline=True runs each job inside add() instead of on the worker (for tests)."""
        self.root = Path(root or DEFAULT).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.inline = inline
        self.jobs: queue.Queue[str] = queue.Queue()
        self.lock = threading.Lock()
        self.worker: threading.Thread | None = None
        self.proc: subprocess.Popen | None = None
        self.current: str | None = None
        # Waiting jobs carry on after a restart; one cut off mid-run waits for Run again.
        for item in reversed(self.list()):
            if item["state"] == "running":
                self._set(item["id"], state="stopped", error="The app was closed while this ran.")
            elif item["state"] == "queued":
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
        if "artist" not in data:  # older takes: fill title and artist from the file's tags once
            from .meta import tags
            found = tags(f / data["filename"])
            fields = {"artist": found.get("artist", "")}
            if found.get("title") and data["title"] == Path(data["filename"]).stem:
                fields["title"] = found["title"]
            self._set(take_id, **fields)
            data.update(fields)
        take = Take(f / "take")
        done = [layer for layer in LAYERS if take.has(layer)]
        data["id"] = take_id
        data["layers_done"] = len(done)
        if data["state"] == "running":
            nxt = next((layer for layer in LAYERS if layer not in done), "notation")
            data["stage"] = STAGES[nxt]
        if data["state"] in ("running", "failed", "stopped"):
            data["log"] = last_lines(f / "log.txt")
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
            title: str | None = None, artist: str | None = None, engine: str = "standard") -> str:
        name = Path(filename).name
        if Path(name).suffix.lower() not in AUDIO:
            raise ValueError(f"{name} is not an audio file this tool reads "
                             f"({', '.join(sorted(AUDIO))})")
        if horn not in HORNS:
            raise ValueError(f"unknown horn {horn}")
        if engine not in ENGINES:
            raise ValueError(f"unknown engine {engine}")
        stem = Path(name).stem
        take_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(stem)}"
        while (self.root / take_id).exists():
            take_id += "-2"
        f = self.root / take_id
        f.mkdir(parents=True)
        safe = re.sub(r"[^A-Za-z0-9 ._()-]+", "_", name)
        (f / safe).write_bytes(data)
        from .meta import tags
        found = tags(f / safe)
        (f / "job.json").write_text(json.dumps({
            "title": title or found.get("title") or stem, "artist": artist or found.get("artist", ""),
            "filename": safe, "horn": horn, "mix": mix, "engine": engine,
            "state": "queued", "added": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, indent=1) + "\n")
        self._enqueue(take_id)
        return take_id

    def _set(self, take_id: str, **fields) -> None:
        with self.lock:
            path = self.root / take_id / "job.json"
            data = json.loads(path.read_text())
            data.update(fields)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=1) + "\n")
            tmp.replace(path)  # never half-written while the page reads it

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

    def command(self, take_id: str) -> list[str]:
        f = self.root / take_id
        job = json.loads((f / "job.json").read_text())
        cmd = [sys.executable, "-m", "saxscribe", "transcribe", str(f / job["filename"]),
               "-o", str(f / "take"), "--horn", job["horn"]]
        cmd += ["--mix"] if job["mix"] else []
        if job.get("engine") == "filosax":
            cmd += ["--notes-tool", "filosax"] + (["--separator", "filosax"] if job["mix"] else [])
        return cmd

    def run(self, take_id: str) -> None:
        f = self.root / take_id
        if json.loads((f / "job.json").read_text())["state"] != "queued":
            return  # stopped or removed while it waited
        self._set(take_id, state="running", started=time.strftime("%Y-%m-%dT%H:%M:%S"),
                  error=None)
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        root = Path(__file__).resolve().parents[2]  # so -m saxscribe finds this copy
        with open(f / "log.txt", "ab") as log:
            with self.lock:
                self.current = take_id
                self.proc = subprocess.Popen(self.command(take_id), cwd=root, env=env,
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while chunk := os.read(self.proc.stdout.fileno(), 4096):
                log.write(chunk)
                log.flush()
                sys.__stdout__.write(chunk.decode("utf-8", "replace"))
                sys.__stdout__.flush()
            code = self.proc.wait()
        with self.lock:
            self.proc, self.current = None, None
        if not (f / "job.json").exists():
            return  # removed while running
        state = json.loads((f / "job.json").read_text())["state"]
        if state == "stopped":
            return
        if code == 0:
            self._set(take_id, state="done", finished=time.strftime("%Y-%m-%dT%H:%M:%S"))
            self.copy_to_desktop(take_id)
        else:
            tail = last_lines(f / "log.txt", 1)
            self._set(take_id, state="failed", error=tail[0] if tail else f"exit code {code}")

    def copy_to_desktop(self, take_id: str) -> None:
        """Copy the finished sheet music to ~/Desktop/Saxscribe (see export.py)."""
        from .export import copy_out
        f = self.root / take_id
        try:
            dst = copy_out(self.take(take_id), json.loads((f / "job.json").read_text()))
        except Exception as exc:  # the upload worked; only the copy didn't
            with open(f / "log.txt", "a") as log:
                log.write(f"[saxscribe] Could not copy to the Desktop: {exc}\n")
            return
        if dst is not None:
            self._set(take_id, desktop=str(dst))
            with open(f / "log.txt", "a") as log:
                log.write(f"[saxscribe] Copied the sheet music to {dst}\n")

    # ---------------------------------------------------------------- stop, retry, remove

    def stop(self, take_id: str) -> None:
        self.folder(take_id)
        self._set(take_id, state="stopped", error="Stopped.")
        with self.lock:
            if self.current == take_id and self.proc is not None:
                self.proc.terminate()

    def retry(self, take_id: str) -> None:
        self.folder(take_id)
        self._set(take_id, state="queued", error=None)
        self._enqueue(take_id)

    def remove(self, take_id: str) -> None:
        f = self.folder(take_id)
        with self.lock:
            if self.current == take_id and self.proc is not None:
                self.proc.terminate()
        shutil.rmtree(f, ignore_errors=True)
