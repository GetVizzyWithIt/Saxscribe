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


def test_a_finished_upload_is_copied_to_the_desktop_folder(client):
    import os
    from pathlib import Path
    job = client.get(f"/api/takes/{client.take_id}").json()
    dst = Path(os.environ["SAXSCRIBE_DESKTOP"]) / "Fixture phrase"
    assert job.get("desktop") == str(dst)
    names = sorted(p.name for p in dst.iterdir())
    assert "Fixture phrase (alto).musicxml" in names and "Fixture phrase (concert).musicxml" in names
    assert "Fixture phrase.mid" in names
    assert "Fixture phrase" in (dst / "Fixture phrase (alto).musicxml").read_text()   # title in the file


def test_the_desktop_copy_can_be_turned_off(monkeypatch):
    from saxscribe.app import export
    monkeypatch.setenv("SAXSCRIBE_DESKTOP", "off")
    assert export.folder_setting() is None


def test_flag_a_bar_for_review(client):
    """Flags are saved to flags.json beside the take, with the bar's time and notes, and
    never change the transcription."""
    import json
    take = client.library.take(client.take_id)
    before = (take.notes.read_text(), take.notation.read_text())
    url = f"/api/takes/{client.take_id}/flags"
    assert client.get(url).json()["flags"] == []
    written = json.loads(take.notation.read_text())["notes"]
    bar = written[0]["bar"]
    in_bar = [n for n in written if n["bar"] == bar]

    r = client.post(url, json={"bar": bar, "categories": ["pitch", "bogus"], "scope": "bar",
                               "text": "sounds a half step high", "view": "alto"})
    assert r.status_code == 200, r.text
    f = r.json()["flags"][0]
    assert f["categories"] == ["pitch"] and f["scope"] == "bar"
    assert f["end"] > f["start"] >= 0
    assert [n["index"] for n in f["notes"]] == [n["index"] for n in in_bar]
    assert not any(n["picked"] for n in f["notes"])

    # Narrow it to one tapped note (its place in quarter notes from bar 1).
    from fractions import Fraction
    q = (bar - 1) * 4 + float(Fraction(in_bar[0]["beat"])) - 1
    r = client.put(f"{url}/{f['id']}", json={"bar": bar, "categories": ["missing", "timing"],
                                              "scope": "notes", "picked": [q]})
    f2 = r.json()["flags"][0]
    assert f2["id"] == f["id"] and f2["created"] == f["created"] and len(r.json()["flags"]) == 1
    assert [n["picked"] for n in f2["notes"]][0] is True
    assert sum(n["picked"] for n in f2["notes"]) == 1

    saved = json.loads((client.library.folder(client.take_id) / "flags.json").read_text())
    assert saved["title"] == "Fixture phrase" and saved["horn"] == "alto" and len(saved["flags"]) == 1
    text = client.get(f"/api/takes/{client.take_id}/flags.txt").text
    assert f"Bar {bar}" in text and "Missing note, Timing off" in text
    assert client.get(f"/api/takes/{client.take_id}/flags.json").status_code == 200

    # The Desktop copy (a temp folder in tests) gets the file and the summary.
    import os
    from pathlib import Path
    DESKTOP = os.environ["SAXSCRIBE_DESKTOP"]
    assert list(Path(DESKTOP).glob("Fixture phrase/* flags.json"))
    assert list(Path(DESKTOP).glob("Fixture phrase/* flags.txt"))

    assert client.post(url, json={"bar": bar, "categories": ["bogus"]}).status_code == 400
    assert client.post(url, json={"bar": bar + 1, "to": bar}).status_code == 400
    assert client.post(url, json={"bar": 0, "categories": ["pitch"]}).status_code == 400
    assert client.put(f"{url}/nope", json={"bar": bar, "categories": ["pitch"]}).status_code == 404
    assert client.delete(f"{url}/{f['id']}").json()["flags"] == []
    assert client.delete(f"{url}/{f['id']}").status_code == 404
    assert (take.notes.read_text(), take.notation.read_text()) == before


def test_possibly_not_sax_stretches_are_offered_for_an_answer(client):
    """Notes marked maybe_not_sax show as a suggested stretch; Austin's answer is stored with
    the flags, and the notes themselves stay as they were."""
    import json
    take = client.library.take(client.take_id)
    original = take.notes.read_text()
    try:
        data = json.loads(original)
        written = json.loads(take.notation.read_text())["notes"]
        bar = written[-1]["bar"]
        for n in written:
            if n["bar"] == bar:
                data["notes"][n["index"]]["tags"].append("maybe_not_sax")
        take.notes.write_text(json.dumps(data))
        url = f"/api/takes/{client.take_id}"
        s = client.get(f"{url}/flags").json()["suggested"]
        assert s == [{"bars": [bar, bar], "notes": sum(n["bar"] == bar for n in written), "answer": None}]
        r = client.post(f"{url}/suggestions", json={"bars": [bar, bar], "answer": "not_sax"})
        assert r.status_code == 200, r.text
        assert r.json()["suggested"][0]["answer"] == "not_sax"
        r = client.post(f"{url}/suggestions", json={"bars": [bar, bar], "answer": "sax"})  # changed his mind
        saved = json.loads((client.library.folder(client.take_id) / "flags.json").read_text())
        assert [x["answer"] for x in saved["reviewed"]] == ["sax"] and saved["reviewed"][0]["end"] > 0
        assert "Austin says sax" in client.get(f"{url}/flags.txt").text
        assert client.post(f"{url}/suggestions", json={"bars": [bar, bar], "answer": "maybe"}).status_code == 400
        assert take.notes.read_text() == json.dumps(data)  # an answer never changes the notes
    finally:
        take.notes.write_text(original)
        (client.library.folder(client.take_id) / "flags.json").unlink(missing_ok=True)


def test_feedback_flags_ranges_merge_undo_and_runs(client):
    """The play-along feedback: quick flags with no reason yet (to sort), ranges of bars,
    overlapping quick flags merging, undo, bars that look right, and flags kept across a re-run."""
    import json
    take = client.library.take(client.take_id)
    folder = client.library.folder(client.take_id)
    url = f"/api/takes/{client.take_id}"
    written = json.loads(take.notation.read_text())["notes"]
    last = max(n["bar"] for n in written)
    manifest = take.manifest.read_text()
    try:
        # A quick flag over two bars: no reason yet, so it is "to sort".
        r = client.post(f"{url}/flags", json={"bar": 1, "to": 2, "merge": True})
        assert r.status_code == 200, r.text
        out = r.json()
        f = out["flags"][0]
        assert (f["bar"], f["to"], f["categories"], f["sorted"]) == (1, 2, [], False)
        assert {n["bar"] for n in f["notes"]} <= {1, 2} and f["end"] > f["start"]
        assert out["last"]["undo"] == {"delete": f["id"]}
        assert out["run"]["id"] and f["run"] == out["run"]["id"] and out["run"]["label"].startswith("Standard")
        assert set(out["groups"]) == {"wrong_notes", "rhythm_feel", "not_sax", "other"}
        assert "not sorted yet" in out["text"]

        # Another quick flag overlapping it grows it; undo puts the old range back.
        r = client.post(f"{url}/flags", json={"bar": 2, "to": 3, "merge": True}).json()
        assert len(r["flags"]) == 1 and (r["flags"][0]["bar"], r["flags"][0]["to"]) == (1, 3)
        assert r["last"]["undo"] == {"put": f["id"], "body": {"bar": 1, "to": 2}}
        r = client.put(f"{url}/flags/{f['id']}", json=r["last"]["undo"]["body"]).json()
        assert (r["flags"][0]["bar"], r["flags"][0]["to"]) == (1, 2)

        # Sorting it: a big reason with no detail, and a note. Fields not sent stay.
        r = client.put(f"{url}/flags/{f['id']}", json={"categories": ["wrong_notes"], "text": "a scoop"}).json()
        g = r["flags"][0]
        assert g["sorted"] and (g["bar"], g["to"], g["categories"]) == (1, 2, ["wrong_notes"])
        assert "Bars 1-2" in r["text"] and "Wrong notes" in r["text"] and '"a scoop"' in r["text"]

        # A separate quick flag, then undo deletes it.
        r = client.post(f"{url}/flags", json={"bar": last, "merge": True}).json()
        assert len(r["flags"]) == 2
        r = client.delete(f"{url}/flags/{r['last']['undo']['delete']}").json()
        assert len(r["flags"]) == 1

        # Bars played through: "looks right" unless flagged.
        r = client.post(f"{url}/heard", json={"bars": [1, 2, 3]}).json()
        assert r["looks_right"] == [3] and r["heard"] == [1, 2, 3]
        assert client.post(f"{url}/heard", json={"bars": ["x"]}).status_code == 400

        # Run it again (here: the notes layer says it was made later). The flag moves to the
        # earlier runs, with whether this run's notes changed there; nothing is lost.
        data = json.loads(manifest)
        data["layers"]["notes"]["made"] = "2099-01-02T03:04:05"
        take.manifest.write_text(json.dumps(data))
        r = client.get(f"{url}/flags").json()
        assert r["flags"] == [] and len(r["past"]) == 1 and r["past"][0]["id"] == f["id"]
        assert r["past"][0]["status"] == "same"  # the notes there are the same
        notes_before = take.notes.read_text()
        try:  # the new run places one of its notes 0.2 s later: "changed"
            nd = json.loads(notes_before)
            idx = next(n["index"] for n in written if n["bar"] in (1, 2))  # the flag covers bars 1-2
            nd["notes"][idx]["onset"] = float(nd["notes"][idx]["onset"]) + 0.2
            take.notes.write_text(json.dumps(nd))
            assert client.get(f"{url}/flags").json()["past"][0]["status"] == "changed"
        finally:
            take.notes.write_text(notes_before)
        assert r["looks_right"] == [] and r["run"]["date"].startswith("2 Jan")
        assert "Earlier runs:" in r["text"] and "unchanged" in r["text"]
        # A quick flag on the new run doesn't merge into the earlier run's flag.
        r = client.post(f"{url}/flags", json={"bar": 1, "merge": True}).json()
        assert len(r["flags"]) == 1 and len(r["past"]) == 1

        saved = json.loads((folder / "flags.json").read_text())
        assert len(saved["flags"]) == 2 and set(saved["looks_right"]) == {json.loads(manifest)["layers"]["notes"]["made"]}
    finally:
        take.manifest.write_text(manifest)
        (folder / "flags.json").unlink(missing_ok=True)


def test_flags_saved_before_runs_were_tracked_still_load(client):
    """flags.json from before ranges and runs (PR #116): read as one-bar flags on the run that
    made the file."""
    import json
    take = client.library.take(client.take_id)
    folder = client.library.folder(client.take_id)
    made_by = json.loads(take.manifest.read_text())["layers"]
    (folder / "flags.json").write_text(json.dumps({"made_by": made_by, "flags": [
        {"id": "old1", "bar": 1, "categories": ["pitch"], "scope": "bar", "picked": [], "text": "",
         "start": 0.0, "end": 1.0, "notes": [], "created": "x", "updated": "x"}]}))
    try:
        r = client.get(f"/api/takes/{client.take_id}/flags").json()
        assert [(f["id"], f["to"], f["sorted"]) for f in r["flags"]] == [("old1", 1, True)]
    finally:
        (folder / "flags.json").unlink(missing_ok=True)


def test_play_page_has_no_horn_switch_and_the_chart_carries_the_title(client):
    page = client.get(f"/take/{client.take_id}").text
    assert 'id="view"' not in page and "Flags go to" in page and 'id="tracker"' in page
    svg = client.get(f"/api/takes/{client.take_id}/score").json()["svg"]
    assert "Fixture phrase" in svg and 'font-weight="bold"' in svg


def test_flags_json_survives_saves_at_the_same_moment(client):
    """The page can save a flag and the bars heard at once; flags.json must stay whole."""
    import json
    import threading
    from saxscribe.app import flags as store
    take = client.library.take(client.take_id)
    folder = client.library.folder(client.take_id)
    job = client.library.job(client.take_id)
    try:
        def flag(i):
            store.save(folder, take, job, {"bar": 1 + i % 3, "merge": False})

        def heard(i):
            store.heard(folder, take, job, [i % 5 + 1])
        threads = [threading.Thread(target=(flag if i % 2 else heard), args=(i,)) for i in range(24)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        data = json.loads((folder / "flags.json").read_text())
        assert len(data["flags"]) == 12 and not list(folder.glob("flags*.tmp"))
    finally:
        (folder / "flags.json").unlink(missing_ok=True)
