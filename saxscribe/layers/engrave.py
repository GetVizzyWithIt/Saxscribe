"""Sheet music as PDF, engraved by MuseScore from the MusicXML.

MusicXML stays the source of truth: the PDF is made from it and can always be
remade. MuseScore (free, musescore.org) does the engraving; install it on a
Mac with `brew install --cask musescore`, or from the website. Where it lives:
the SAXSCRIBE_MUSESCORE environment variable, else [tools] musescore in
config.local.toml, else the usual install places and names on the PATH.
Without it, everything else still runs and the log says how to add it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .. import frontend

PLACES = ["/Applications/MuseScore 4.app/Contents/MacOS/mscore",
          "/Applications/MuseScore 3.app/Contents/MacOS/mscore"]
NAMES = ["mscore", "mscore4portable", "musescore", "musescore4", "MuseScore4", "mscore3"]


def find_musescore() -> str | None:
    from ..score.refs import config
    chosen = os.environ.get("SAXSCRIBE_MUSESCORE") or config().get("tools", {}).get("musescore")
    if chosen:
        return chosen if Path(chosen).expanduser().exists() else None
    for p in PLACES:
        if Path(p).exists():
            return p
    for name in NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def to_pdf(musicxml: Path, pdf: Path) -> bool:
    """Engrave one MusicXML file. True if the PDF was written."""
    exe = find_musescore()
    if not exe:
        return False
    env = dict(os.environ)
    if sys.platform.startswith("linux"):  # no display on a server; the Mac app only ships its own (cocoa) platform
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        subprocess.run([exe, "-o", str(pdf), str(musicxml)], check=True, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        frontend.log(f"  MuseScore could not engrave {musicxml.name}: {exc}")
        return False
    return pdf.exists() and pdf.stat().st_size > 0
