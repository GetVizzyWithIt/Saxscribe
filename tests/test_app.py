"""The web app on the fixture: upload, transcribe, score with its timing map, audio, downloads."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("verovio")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from saxscribe.app.library import Library  # noqa: E402
from saxscribe.app.server import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory, fixture_wav):
    library = Library(tmp_path_factory.mktemp("library"), inline=True)
    c = TestClient(create_app(library))
    c.library = library
    r = c.post("/api/takes", files={"file": ("phrase.wav", fixture_wav.read_bytes(), "audio/wav")},
               data={"horn": "alto", "mix": "false", "title": "Fixture phrase"})
    assert r.status_code == 200, r.text
    c.take_id = r.json()["id"]
    return c


def test_upload_runs_the_pipeline(client):
    job = client.get(f"/api/takes/{client.take_id}").json()
    assert job["state"] == "done", job.get("error")
    assert job["layers_done"] == 4
    assert job["title"] == "Fixture phrase"
    assert [t["id"] for t in client.get("/api/takes").json()] == [client.take_id]


def test_rejects_files_that_are_not_audio(client):
    r = client.post("/api/takes", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_score_has_every_note_and_a_rising_timing_map(client):
    data = client.get(f"/api/takes/{client.take_id}/score").json()
    assert data["view"] == "alto"
    assert data["svg"].count('class="note"') >= 10
    sync = data["sync"]
    assert len(sync) >= 10
    assert all(b[0] > a[0] and b[1] > a[1] for a, b in zip(sync, sync[1:]))
    # Every note Verovio drew is in the timing map Verovio returned.
    on = {i for e in data["timemap"] for i in e.get("on", [])}
    assert sum(1 for i in on if f'id="{i}" class="note"' in data["svg"]) == data["svg"].count('class="note"')


def test_written_notes_sit_at_their_played_onsets(client):
    """Most sync pairs are a written note at the exact onset it was played in notes.json."""
    import json
    from fractions import Fraction
    take = client.library.take(client.take_id)
    played = json.loads(take.notes.read_text())["notes"]
    sync = dict(map(tuple, client.get(f"/api/takes/{client.take_id}/score").json()["sync"]))
    written = json.loads(take.notation.read_text())["notes"]
    hits = 0
    for n in written:
        q = round((n["bar"] - 1) * 4 + float(Fraction(n["beat"])) - 1, 4)
        if q in sync:
            hits += abs(sync[q] - played[n["index"]]["onset"]) < 0.001
    assert hits >= 0.8 * len(written)


def test_tenor_and_concert_views(client):
    for view in ("tenor", "concert"):
        data = client.get(f"/api/takes/{client.take_id}/score", params={"view": view}).json()
        assert data["view"] == view and 'class="note"' in data["svg"]
    assert client.get(f"/api/takes/{client.take_id}/score", params={"view": "tuba"}).status_code == 400


def test_tenor_part_is_a_fifth_below_alto_on_paper(client):
    from music21 import converter
    alto = client.get(f"/api/takes/{client.take_id}/file/musicxml", params={"view": "alto"})
    tenor = client.get(f"/api/takes/{client.take_id}/file/musicxml", params={"view": "tenor"})
    a = [n.pitch.midi for n in converter.parseData(alto.content.decode()).flatten().notes]
    t = [n.pitch.midi for n in converter.parseData(tenor.content.decode()).flatten().notes]
    assert len(a) == len(t) and all(x - y == -5 for x, y in zip(a, t))  # tenor is written a 4th above alto


def test_audio_is_seekable(client):
    r = client.get(f"/api/takes/{client.take_id}/audio/source", headers={"Range": "bytes=0-99"})
    assert r.status_code == 206 and len(r.content) == 100
    assert client.get(f"/api/takes/{client.take_id}/audio/nothing").status_code == 404


def test_downloads(client):
    assert client.get(f"/api/takes/{client.take_id}/file/midi").status_code == 200
    pdf = client.get(f"/api/takes/{client.take_id}/file/pdf")
    assert pdf.status_code in (200, 404)  # 404 = no MuseScore here, with a message saying so
    if pdf.status_code == 404:
        assert "MuseScore" in pdf.json()["detail"]


def test_pages(client):
    assert "Transcribe a recording" in client.get("/").text
    assert "play.js" in client.get(f"/take/{client.take_id}").text
    assert client.get("/take/20990101-000000-nope").status_code == 404
