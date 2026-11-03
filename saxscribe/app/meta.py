"""Song details for the sheet music: title, artist, and a Saxscribe credit.

The title and artist come from what was typed at upload, else from the audio
file's own tags (read with ffprobe). They are written into the take's
MusicXML, so every PDF made from it carries them: MuseScore's and the
browser's print page alike. Only the header changes; no note is touched.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

CREDIT = "Transcribed with Saxscribe"


def tags(audio: Path) -> dict:
    """{'title': ..., 'artist': ...} from the file's tags; empty where there are none."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-of", "json", "-show_entries",
                              "format_tags:stream_tags", str(audio)],
                             capture_output=True, text=True, timeout=30, check=True).stdout
        data = json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}
    found = {}
    for block in [data.get("format", {})] + data.get("streams", []):
        for k, v in (block.get("tags") or {}).items():
            found.setdefault(k.lower(), str(v).strip())
    return {"title": found.get("title", ""),
            "artist": found.get("artist") or found.get("album_artist") or found.get("performer", "")}


def stamp(xml: str, title: str, artist: str) -> str:
    """The MusicXML with its title, 'As played by <artist>' and the credit in the header."""
    t = escape(title or "Transcription")
    if "<work-title>" in xml:
        xml = re.sub(r"<work-title>.*?</work-title>", lambda m: f"<work-title>{t}</work-title>",
                     xml, count=1, flags=re.S)
    else:
        xml = re.sub(r"<score-partwise\b[^>]*>",
                     lambda m: f"{m.group(0)}\n  <work>\n    <work-title>{t}</work-title>\n  </work>",
                     xml, count=1)
    xml = re.sub(r"<movement-title>.*?</movement-title>", lambda m: f"<movement-title>{t}</movement-title>",
                 xml, count=1, flags=re.S)
    xml = re.sub(r"\s*<creator\b[^>]*>.*?</creator>", "", xml, flags=re.S)
    xml = re.sub(r"\s*<rights\b[^>]*>.*?</rights>", "", xml, flags=re.S)
    lines = []
    if artist:
        lines.append(f'<creator type="composer">As played by {escape(artist)}</creator>')
    lines.append(f'<creator type="lyricist">{CREDIT}</creator>')
    lines.append(f"<rights>{CREDIT}</rights>")
    block = "".join(f"\n    {ln}" for ln in lines)
    # Printed header lines (MuseScore and Verovio draw the page from these).
    xml = re.sub(r"\s*<credit\b.*?</credit>", "", xml, flags=re.S)
    credits = [("title", "center", 24, t)]
    if artist:
        credits.append(("composer", "right", 12, f"As played by {escape(artist)}"))
    credits.append(("lyricist", "left", 10, CREDIT))
    credit_xml = "".join(
        f'\n  <credit page="1">\n    <credit-type>{kind}</credit-type>\n    <credit-words justify="{side}" '
        f'valign="top" font-size="{size}">{words}</credit-words>\n  </credit>'
        for kind, side, size, words in credits)
    xml = re.sub(r"\s*<part-list>", lambda m: credit_xml + m.group(0), xml, count=1)
    if "<identification>" in xml:
        return xml.replace("<identification>", "<identification>" + block, 1)
    return re.sub(r"<(?:defaults|credit|part-list)\b",  # identification comes before these
                  lambda m: f"<identification>{block}\n  </identification>\n  {m.group(0)}", xml, count=1)


def stamp_file(path: Path, title: str, artist: str) -> None:
    """Rewrites the file only when its header would change (so PDFs aren't remade for nothing)."""
    old = path.read_text(encoding="utf-8")
    new = stamp(old, title, artist)
    if new != old:
        path.write_text(new, encoding="utf-8")
