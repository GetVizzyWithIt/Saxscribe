"""Copy a finished transcription to a folder on the Desktop.

Austin opens the sheet music in MuseScore himself, so every finished upload
is also copied to ~/Desktop/Saxscribe/<title - artist>/:

  <name> (<horn>).musicxml    the horn's written part, with title and artist
  <name> (concert).musicxml   concert pitch
  <name> (<horn>).pdf         when MuseScore made one
  <name>.mid                  the notes as played

The folder is set in config.local.toml ([app] desktop = "~/somewhere"), and
desktop = "off" turns the copy off. A failed copy never fails the upload.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from ..take import Take

DEFAULT = "~/Desktop/Saxscribe"


def folder_setting() -> Path | None:
    from ..score.refs import config
    chosen = os.environ.get("SAXSCRIBE_DESKTOP") or config().get("app", {}).get("desktop") or DEFAULT
    if str(chosen).lower() in ("off", "no", "false", "0", "none"):
        return None
    return Path(str(chosen)).expanduser()


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "", name).strip() or "score"


def copy_out(take: Take, job: dict) -> Path | None:
    """Copy the take's sheet music to the Desktop folder. Returns the folder, or None."""
    from . import score_view
    base = folder_setting()
    if base is None:
        return None
    song = {"title": job.get("title", ""), "artist": job.get("artist", "")}
    name = safe(song["title"] + (f" - {song['artist']}" if song["artist"] else ""))
    dst = base / name
    dst.mkdir(parents=True, exist_ok=True)
    horn = job.get("horn", "alto")
    for view in (horn, "concert"):
        shutil.copyfile(score_view.musicxml(take, view, song), dst / f"{name} ({view}).musicxml")
    pdf = score_view.pdf(take, horn, song)
    if pdf is not None:
        shutil.copyfile(pdf, dst / f"{name} ({horn}).pdf")
    if take.midi.exists():
        shutil.copyfile(take.midi, dst / f"{name}.mid")
    return dst
