"""The web server: FastAPI routes over the library and its take folders.

Pages:
  /                  the library: upload a recording, see every take
  /take/<id>         the play-along for one take
  /take/<id>/pdf     the PDF (MuseScore's), or the print page when there is none
  /take/<id>/print   the score as letter pages, to print or save as PDF from the browser

API (JSON unless noted):
  GET  /api/info                  addresses to open the app from another device
  GET  /api/takes                 every take, newest first
  POST /api/takes                 upload (form: file, horn, mix, title, artist)
  GET  /api/takes/<id>            one take's status
  POST /api/takes/<id>/stop       stop a running or waiting take
  POST /api/takes/<id>/retry      run it again
  DELETE /api/takes/<id>          remove the take and its files
  GET  /api/takes/<id>/score      ?view=alto|tenor|concert&size=0..3: SVG, timemap, sync
  GET  /api/takes/<id>/audio/<which>   source, stem or accompaniment (WAV, seekable)
  GET  /api/takes/<id>/file/<kind>     pdf, musicxml or midi, as a download (?view=)
"""
from __future__ import annotations

import re
import socket
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import score_view
from .library import Library

STATIC = Path(__file__).parent / "static"


def lan_addresses() -> list[str]:
    """This machine's addresses on the local network (for opening the app on an iPad)."""
    found = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))  # no packet is sent; this just picks the outgoing interface
            found.add(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    return sorted(a for a in found if not a.startswith("127."))


def file_name(job: dict, view: str) -> str:
    """e.g. "Blues for Mary Jane - Stan Getz (alto)", safe for a download name."""
    name = job["title"] + (f" - {job['artist']}" if job.get("artist") else "") + f" ({view})"
    return re.sub(r'[\\/:*?"<>|]+', "", name).strip() or "score"


def create_app(library: Library, port: int = 8765) -> FastAPI:
    app = FastAPI(title="Saxscribe", docs_url=None, redoc_url=None)

    def take_or_404(take_id: str):
        try:
            job = library.job(take_id)
        except KeyError:
            raise HTTPException(404, "No such take")
        return job, library.take(take_id)

    def done_or_409(take_id: str):
        job, take = take_or_404(take_id)
        if job["state"] != "done":
            raise HTTPException(409, f"This take is {job['state']}")
        return job, take

    def view_or_400(job: dict, view: str | None) -> str:
        view = view or job["horn"]
        if view not in score_view.VIEWS:
            raise HTTPException(400, f"view must be one of {', '.join(score_view.VIEWS)}")
        return view

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/take/{take_id}", include_in_schema=False)
    def play(take_id: str):
        take_or_404(take_id)
        return FileResponse(STATIC / "play.html")

    @app.get("/take/{take_id}/pdf", include_in_schema=False)
    def pdf_or_print(take_id: str, view: str | None = None):
        job, take = done_or_409(take_id)
        view = view_or_400(job, view)
        path = score_view.pdf(take, view, job)
        if path is None:
            return RedirectResponse(f"/take/{take_id}/print?view={view}", status_code=303)
        return FileResponse(path, media_type="application/pdf", filename=f"{file_name(job, view)}.pdf")

    @app.get("/take/{take_id}/print", include_in_schema=False)
    def print_page(take_id: str):
        done_or_409(take_id)
        return FileResponse(STATIC / "print.html")

    @app.get("/api/takes/{take_id}/pages")
    def pages(take_id: str, view: str | None = None):
        job, take = done_or_409(take_id)
        view = view_or_400(job, view)
        return {"view": view, "title": file_name(job, view), "pages": score_view.pages(take, view, job)}

    @app.get("/api/info")
    def info():
        return {"library": str(library.root),
                "urls": [f"http://{a}:{port}/" for a in lan_addresses()]}

    @app.get("/api/takes")
    def takes():
        return library.list()

    @app.post("/api/takes")
    async def upload(file: UploadFile = File(...), horn: str = Form("alto"),
                     mix: bool = Form(False), title: str = Form(""), artist: str = Form("")):
        data = await file.read()
        if not data:
            raise HTTPException(400, "The file is empty")
        try:
            take_id = library.add(file.filename or "take.wav", data, horn=horn, mix=mix,
                                  title=title.strip() or None, artist=artist.strip() or None)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return library.job(take_id)

    @app.get("/api/takes/{take_id}")
    def take_status(take_id: str):
        return take_or_404(take_id)[0]

    @app.post("/api/takes/{take_id}/stop")
    def stop(take_id: str):
        take_or_404(take_id)
        library.stop(take_id)
        return library.job(take_id)

    @app.post("/api/takes/{take_id}/retry")
    def retry(take_id: str):
        job, _ = take_or_404(take_id)
        if job["state"] == "running":
            raise HTTPException(409, "It is already running")
        library.retry(take_id)
        return library.job(take_id)

    @app.delete("/api/takes/{take_id}")
    def remove(take_id: str):
        take_or_404(take_id)
        library.remove(take_id)
        return {"removed": take_id}

    @app.get("/api/takes/{take_id}/score")
    def score(take_id: str, view: str | None = None, size: int = 1):
        job, take = done_or_409(take_id)
        return score_view.render(take, view_or_400(job, view), size, job)

    @app.get("/api/takes/{take_id}/audio/{which}")
    def audio(take_id: str, which: str):
        _, take = done_or_409(take_id)
        path = {"source": take.source, "stem": take.stem,
                "accompaniment": take.accompaniment}.get(which)
        if path is None or not path.exists():
            raise HTTPException(404, f"No {which} audio for this take")
        return FileResponse(path, media_type="audio/wav")

    @app.get("/api/takes/{take_id}/file/{kind}")
    def download(take_id: str, kind: str, view: str | None = None):
        job, take = done_or_409(take_id)
        view = view_or_400(job, view)
        name = file_name(job, view)
        if kind == "pdf":
            path = score_view.pdf(take, view, job)
            if path is None:
                raise HTTPException(404, "The PDF needs MuseScore on this Mac. Install it from "
                                         "musescore.org, then try again. MusicXML works now.")
            return FileResponse(path, media_type="application/pdf", filename=f"{name}.pdf")
        if kind == "musicxml":
            return FileResponse(score_view.musicxml(take, view, job),
                                media_type="application/vnd.recordare.musicxml+xml",
                                filename=f"{name}.musicxml")
        if kind == "midi":
            return FileResponse(take.midi, media_type="audio/midi",
                                filename=f"{job['title']}.mid")
        raise HTTPException(404, "kind must be pdf, musicxml or midi")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
