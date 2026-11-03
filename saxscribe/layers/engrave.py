"""Sheet music as PDF, engraved by MuseScore from the MusicXML.

MusicXML stays the source of truth: the PDF is made from it and can always be
remade. MuseScore (free, musescore.org) does the engraving; install it on a
Mac with `brew install --cask musescore`, or from the website. Where it lives:
the SAXSCRIBE_MUSESCORE environment variable, else [tools] musescore in
config.local.toml, else the usual install places and names on the PATH.
Without it, everything else still runs and the log says how to add it.

To turn PDFs off (open the MusicXML in MuseScore yourself instead), set
[tools] musescore = "off" in config.local.toml, or SAXSCRIBE_MUSESCORE=off.
A PDF that fails never stops a take: the MusicXML is always written first.
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


def chosen_setting() -> str:
    from ..score.refs import config
    return str(os.environ.get("SAXSCRIBE_MUSESCORE") or config().get("tools", {}).get("musescore") or "")


def turned_off() -> bool:
    return chosen_setting().strip().lower() in ("off", "no", "false", "0", "none")


def find_musescore() -> str | None:
    chosen = chosen_setting()
    if turned_off():
        return None
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
        code = getattr(exc, "returncode", None)
        why = f"exit {code}" if code is not None else type(exc).__name__
        frontend.log(f"  MuseScore refused {musicxml.name} ({why}); the MusicXML is kept, open it in MuseScore yourself")
        return False
    return pdf.exists() and pdf.stat().st_size > 0
