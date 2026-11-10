"""The match check's Needs review list (score/review.py) and its app routes."""
from __future__ import annotations

import json

import pytest

from saxscribe.score import review


def write_report(runs, tmp_path):
    keys = runs / "keys" / "test" / "pfh"
    keys.mkdir(parents=True)
    (keys / "pfh.mp3").write_bytes(b"ID3fake")
    (keys / "pfh_key.json").write_text(json.dumps({"notes": [
        {"onset": 1.5, "offset": 2.0, "pitch": 65}, {"start": 0.5, "end": 1.0, "midi": 63}, {"onset": 3}]}))
    lines = [
        {"id": "getz_pfh_1959", "tune": "Pennies From Heaven", "audio": "keys/test/pfh/pfh.mp3",
         "key_json": "keys/test/pfh/pfh_key.json", "verdict": "pass", "heard_agree": 0.86, "in_training": False},
        {"id": "parker_x_1947", "tune": "X", "audio": str(tmp_path / "nowhere.mp3"), "verdict": "pass",
         "in_training": True},
        {"id": "bird_y_1950", "tune": "Y", "audio": "keys/test/pfh/pfh_key.json", "verdict": "reject",
         "reason": "lengths differ by 40 s"},
    ]
    (runs / "keys" / review.REPORT).write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n")


def test_load_and_benchmark_rule(tmp_path):
    runs = tmp_path / "runs"
    assert review.load(runs)["exists"] is False
    write_report(runs, tmp_path)
    got = {e["id"]: e for e in review.load(runs)["entries"]}
    assert set(got) == {"getz_pfh_1959", "parker_x_1947", "bird_y_1950"}
    assert got["getz_pfh_1959"]["benchmark"] is True
    assert got["parker_x_1947"]["benchmark"] is False  # a model trained on it
    assert got["bird_y_1950"]["benchmark"] is False
    # Austin's word overrides the check either way, and survives a rerun of the report
    review.save(runs, "bird_y_1950", "good")
    review.save(runs, "getz_pfh_1959", "wrong", "chart is the second chorus")
    got = {e["id"]: e for e in review.load(runs)["entries"]}
    assert got["bird_y_1950"]["benchmark"] is True
    assert got["getz_pfh_1959"]["benchmark"] is False
    assert got["getz_pfh_1959"]["austin_note"] == "chart is the second chorus"
    review.save(runs, "getz_pfh_1959", None)
    assert {e["id"]: e for e in review.load(runs)["entries"]}["getz_pfh_1959"]["benchmark"] is True
    with pytest.raises(ValueError):
        review.save(runs, "getz_pfh_1959", "maybe")
    with pytest.raises(KeyError):
        review.save(runs, "nobody", "good")


def test_audio_and_key(tmp_path):
    runs = tmp_path / "runs"
    write_report(runs, tmp_path)
    assert review.audio_path(runs, "getz_pfh_1959").name == "pfh.mp3"
    assert review.audio_path(runs, "parker_x_1947") is None  # missing file
    assert review.audio_path(runs, "bird_y_1950") is None  # not audio: never served
    notes = review.key_notes(runs, "getz_pfh_1959")
    assert [n["pitch"] for n in notes] == [63, 65]  # sorted, the incomplete note dropped


def test_review_routes(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from saxscribe.app.library import Library
    from saxscribe.app.server import create_app

    runs = tmp_path / "runs"
    client = TestClient(create_app(Library(tmp_path / "library", inline=True), runs=runs))
    assert client.get("/api/review").json()["entries"] == []
    write_report(runs, tmp_path)
    assert len(client.get("/api/review").json()["entries"]) == 3
    assert client.get("/api/review/getz_pfh_1959/audio").content == b"ID3fake"
    assert client.get("/api/review/bird_y_1950/audio").status_code == 404
    assert client.get("/api/review/nobody/key").status_code == 404
    assert len(client.get("/api/review/getz_pfh_1959/key").json()["notes"]) == 2
    r = client.post("/api/review/bird_y_1950", json={"verdict": "good", "note": "checked by ear"})
    assert r.status_code == 200
    assert {e["id"]: e for e in r.json()["entries"]}["bird_y_1950"]["austin_verdict"] == "good"
    assert client.post("/api/review/bird_y_1950", json={"verdict": "bad"}).status_code == 400
