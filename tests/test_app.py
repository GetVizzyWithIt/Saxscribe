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


def test_job_keeps_a_log_for_the_page(client):
    from saxscribe.app.library import last_lines
    log = client.library.folder(client.take_id) / "log.txt"
    assert "Layer 4/4" in log.read_text()
    assert last_lines(log, 1) and last_lines(log, 1)[0].startswith("[saxscribe]")


def test_stop_and_remove(tmp_path, fixture_wav):
    """Stop ends a running transcription at once; Remove deletes the take."""
    import time as clock
    library = Library(tmp_path / "lib")
    c = TestClient(create_app(library))
    take_id = c.post("/api/takes", files={"file": ("phrase.wav", fixture_wav.read_bytes(), "audio/wav")},
                     data={"horn": "tenor", "mix": "false"}).json()["id"]
    for _ in range(100):  # wait for the worker to start it
        if c.get(f"/api/takes/{take_id}").json()["state"] != "queued":
            break
        clock.sleep(0.05)
    assert c.post(f"/api/takes/{take_id}/stop").json()["state"] == "stopped"
    for _ in range(100):
        if library.proc is None:
            break
        clock.sleep(0.05)
    assert library.proc is None
    assert c.get(f"/api/takes/{take_id}").json()["state"] == "stopped"
    assert c.delete(f"/api/takes/{take_id}").status_code == 200
    assert c.get(f"/api/takes/{take_id}").status_code == 404
    assert c.get("/api/takes").json() == []


def test_a_take_cut_off_by_a_restart_waits_for_run_again(tmp_path, fixture_wav):
    import json
    library = Library(tmp_path / "lib", inline=True)
    take_id = library.add("phrase.wav", fixture_wav.read_bytes())
    library._set(take_id, state="running")  # as if the app was closed mid-run
    reopened = Library(tmp_path / "lib", inline=True)
    assert reopened.job(take_id)["state"] == "stopped"
    reopened.retry(take_id)
    assert json.loads((reopened.folder(take_id) / "job.json").read_text())["state"] == "done"


def test_pdf_falls_back_to_a_print_page(client):
    """Without MuseScore's PDF, the PDF link opens a printable page of the same score."""
    from saxscribe.app import score_view
    take = client.library.take(client.take_id)
    r = client.get(f"/take/{client.take_id}/pdf", params={"view": "tenor"}, follow_redirects=False)
    if score_view.pdf(take, "tenor") is None:
        assert r.status_code == 303 and r.headers["location"].endswith("/print?view=tenor")
    else:
        assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert "window.print" in client.get(f"/take/{client.take_id}/print").text
    data = client.get(f"/api/takes/{client.take_id}/pages", params={"view": "tenor"}).json()
    assert data["pages"] and "Fixture phrase" in data["pages"][0]
    assert sum(p.count('class="note"') for p in data["pages"]) >= 10


def test_sheet_music_carries_title_artist_and_credit(tmp_path, fixture_wav):
    """Title and artist come from the file's tags; the header says who played it and who transcribed it."""
    import shutil
    import subprocess
    if not shutil.which("ffmpeg"):
        pytest.skip("needs ffmpeg")
    tagged = tmp_path / "tagged.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(fixture_wav), "-metadata",
                    "title=Blues for Testing", "-metadata", "artist=Test Player", str(tagged)], check=True)
    library = Library(tmp_path / "lib", inline=True)
    c = TestClient(create_app(library))
    job = c.post("/api/takes", files={"file": ("tagged.wav", tagged.read_bytes(), "audio/wav")},
                 data={"horn": "alto", "mix": "false"}).json()
    assert (job["title"], job["artist"]) == ("Blues for Testing", "Test Player")
    for view in ("alto", "tenor", "concert"):
        xml = c.get(f"/api/takes/{job['id']}/file/musicxml", params={"view": view})
        from urllib.parse import unquote
        assert "Blues for Testing - Test Player" in unquote(xml.headers["content-disposition"])
        text = xml.text
        assert "<work-title>Blues for Testing</work-title>" in text
        assert "As played by Test Player" in text and "Transcribed with Saxscribe" in text
    page = c.get(f"/api/takes/{job['id']}/pages").json()["pages"][0]
    assert "Blues for Testing" in page and "Test Player" in page and "Saxscribe" in page


def test_stamp_keeps_every_note():
    from saxscribe.app.meta import stamp
    xml = ('<score-partwise><work><work-title>Transcription</work-title></work>'
           '<identification><creator type="composer">saxscribe</creator></identification>'
           '<part-list/><part><note/><note/></part></score-partwise>')
    out = stamp(xml, "A & B", "Someone")
    assert out.count("<note/>") == 2 and "A &amp; B" in out and "saxscribe</creator>" not in out
    assert stamp(out, "A & B", "Someone") == out  # stamping twice changes nothing


def test_musescore_files_have_no_printed_credits():
    """MuseScore 4 piles position-less <credit>s at the page foot, so the files carry header
    fields only (MuseScore builds its title block from them); credits are for Verovio's page."""
    from saxscribe.app.meta import stamp
    xml = ('<score-partwise><work><work-title>T</work-title></work><identification>'
           '<rights>old</rights></identification><credit page="1"><credit-words>old</credit-words>'
           '</credit><part-list/></score-partwise>')
    plain = stamp(xml, "Song", "Player")
    assert "<credit" not in plain.replace("<creator", "") and "<rights>" not in plain
    assert '<creator type="composer">As played by Player</creator>' in plain
    assert plain.count("<credit page") == 0 and stamp(xml, "Song", "Player", credits=True).count("<credit page") == 3
