"""The score as the play-along page shows it, and the map that keeps it in time.

The page needs three things for a take and a view (alto, tenor, concert...):
  svg      the score drawn by Verovio, one long page of systems
  timemap  Verovio's list of where each note and bar starts, in quarter notes
  sync     pairs of (quarter notes from the start of bar 1, seconds in the
           recording), so the page can turn the audio clock into a place in
           the score and back

The sync pairs come from the layers below the notation: each written note
points back to its note in notes.json, whose onset is the exact time it was
played, and the beat grid fills the gaps between notes (rests, long notes).
Nothing is re-measured here.
"""
from __future__ import annotations

import bisect
import json
from fractions import Fraction
from pathlib import Path

from ..horns import HORNS
from ..layers.notation import BEATS_PER_BAR
from ..take import Take

VIEWS = ("concert", *HORNS)
SIZES = (2100, 1700, 1400, 1150)  # page widths for the size buttons: narrower page, bigger notes


def musicxml(take: Take, view: str, song: dict | None = None) -> Path:
    """The MusicXML for a view. A horn's written part is made from the concert
    score the first time it is asked for (e.g. tenor for a take made as alto).
    song = {"title", "artist"} goes into the header (see meta.py)."""
    from .meta import stamp_file
    if song:
        stamp_file(take.musicxml, song.get("title", ""), song.get("artist", ""))
    if view == "concert":
        return take.musicxml
    if view not in HORNS:
        raise KeyError(view)
    path = take.written_musicxml(view)
    if not path.exists() or path.stat().st_mtime < take.notation.stat().st_mtime:
        from music21 import converter, interval
        horn = HORNS[view]
        score = converter.parse(str(take.musicxml))
        written = score.transpose(interval.Interval(horn.written_interval))
        for part in written.parts:
            part.partName = f"{horn.name.capitalize()} Sax in {horn.key}"
        from ..layers.ranges import mark_unplayable
        # Notes this horn can't play (a take made on another horn) stay as heard, shown red.
        mark_unplayable(written, horn, horn.written_shift)
        written.write("musicxml", fp=str(path))
    if song:
        stamp_file(path, song.get("title", ""), song.get("artist", ""))
    return path


def pdf_path(take: Take, view: str) -> Path:
    return take.pdf if view == "concert" else take.written_pdf(view)


def pdf(take: Take, view: str, song: dict | None = None) -> Path | None:
    """The PDF for a view, made with MuseScore if it isn't there yet (or is older than
    its MusicXML). None when it can't be made."""
    out = pdf_path(take, view)
    xml = musicxml(take, view, song)
    if out.exists() and out.stat().st_mtime >= xml.stat().st_mtime:
        return out
    from ..layers import engrave  # the pipeline's PDF step (MuseScore)
    return out if engrave.to_pdf(xml, out) and out.exists() else None


def toolkit():
    """A Verovio toolkit pointed at its fonts. Verovio looks for them per thread, and
    the web server renders on worker threads, so the path is set by hand (and not
    loaded at start, which prints font errors on those threads)."""
    import verovio
    tk = verovio.toolkit(False)
    tk.setResourcePath(str(Path(verovio.__file__).parent / "data"))
    return tk


def pages(take: Take, view: str, song: dict | None = None) -> list[str]:
    """The score as US Letter pages (SVG), with its title, artist and credit, for
    printing or saving as PDF when MuseScore's PDF isn't there."""
    tk = toolkit()
    tk.setOptions({"pageWidth": 2159, "pageHeight": 2794, "scale": 45, "footer": "none",
                   "pageMarginLeft": 120, "pageMarginRight": 120, "pageMarginTop": 100,
                   "pageMarginBottom": 100, "spacingSystem": 10, "svgViewBox": True})
    from .meta import stamp
    song = song or {}
    xml = stamp(musicxml(take, view, song).read_text(encoding="utf-8"),
                song.get("title", ""), song.get("artist", ""), credits=True)
    if not tk.loadData(xml):
        raise ValueError(f"Verovio could not read the {view} score")
    out = [tk.renderToSVG(p) for p in range(1, tk.getPageCount() + 1)]
    if out and song and song.get("title"):
        # Verovio draws header lines at one text size; make the title stand out.
        import re
        from xml.sax.saxutils import escape
        out[0] = re.sub(r'<tspan font-size="(\d+)px">' + re.escape(escape(song["title"])) + "</tspan>",
                        lambda m: f'<tspan font-size="{int(m.group(1)) * 3 // 2}px" font-weight="bold">'
                                  f'{escape(song["title"])}</tspan>', out[0], count=1)
    return out


def render(take: Take, view: str, size: int = 1, song: dict | None = None) -> dict:
    tk = toolkit()
    tk.setOptions({
        "pageWidth": SIZES[max(0, min(len(SIZES) - 1, size))], "pageHeight": 60000, "adjustPageHeight": True, "scale": 40,
        "svgViewBox": True, "header": "none", "footer": "none", "breaks": "auto",
        "pageMarginTop": 40, "pageMarginBottom": 40, "spacingSystem": 12,
    })
    if not tk.loadFile(str(musicxml(take, view, song))):
        raise ValueError(f"Verovio could not read the {view} score")
    svg = "".join(tk.renderToSVG(p) for p in range(1, tk.getPageCount() + 1))
    timemap = tk.renderToTimemap({"includeMeasures": True, "includeRests": True})
    return {"view": view, "svg": svg, "timemap": timemap, "sync": sync(take)}


def sync(take: Take) -> list[list[float]]:
    """[[quarter notes from bar 1, seconds], ...], rising in both."""
    notes = json.loads(take.notes.read_text())
    nota = json.loads(take.notation.read_text())
    shift = Fraction(nota.get("beat_shift", "0"))
    played = notes["notes"]

    # Written notes at the moment they were played.
    pts = []
    for n in nota["notes"]:
        q = (n["bar"] - 1) * BEATS_PER_BAR + Fraction(n["beat"]) - 1
        pts.append((float(q), float(played[n["index"]]["onset"])))
    pts.sort()
    anchors: list[tuple[float, float]] = []
    for q, t in pts:
        if not anchors or (q > anchors[-1][0] and t > anchors[-1][1]):
            anchors.append((q, t))

    # The beat grid between them: tracked beat i sits at i + shift in the score.
    beats = notes.get("beats") or []
    if len(beats) >= 2:
        grid = [(float(i + shift), float(b)) for i, b in enumerate(beats)]
    else:
        spb = 60.0 / (notes.get("tempo_bpm") or nota.get("tempo_bpm") or 120.0)
        end = max([q for q, _ in anchors], default=0.0) + BEATS_PER_BAR
        grid = [(float(q), (q - float(shift)) * spb) for q in range(0, int(end) + 1)]
    out = list(anchors)
    qs = [q for q, _ in anchors]
    for q, t in grid:
        i = bisect.bisect_left(qs, q)
        before = anchors[i - 1] if i > 0 else None
        after = anchors[i] if i < len(anchors) else None
        if (before is None or (q > before[0] and t > before[1])) and \
           (after is None or (q < after[0] and t < after[1])):
            out.append((q, t))
    out.sort()
    return [[round(q, 4), round(t, 4)] for q, t in out]
