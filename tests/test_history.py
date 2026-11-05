"""The results history behind the app's Results page (score/history.py)."""
from __future__ import annotations

import json

import pytest

from saxscribe.score import history

CARD = {"set": "urmp", "split": "all", "settings": "default", "items": 11,
        "mean": {"note_f1": 0.644, "onset_f1": 0.816, "pitch_accuracy": 0.944}}


def test_a_scorecard_run_lands_in_the_runs_folder(tmp_path):
    path = history.append(history.record(CARD, note="first try"), tmp_path)
    assert path == tmp_path / "results.jsonl"
    rec = history.read(path)[0]
    assert rec["set"] == "urmp" and rec["default"] is True and rec["note"] == "first try"
    assert rec["metrics"]["note_f1"] == 0.644
    assert rec["when"].endswith("Z") and rec["source"] == "scorecard"


def test_other_settings_are_not_the_trend_line():
    assert history.record({**CARD, "settings": "notes-segment"})["default"] is False


def test_repo_and_local_runs_merge_once_each_in_time_order(tmp_path, monkeypatch):
    repo = tmp_path / "repo.jsonl"
    early = {"id": "a", "when": "2026-11-01T00:00:00Z", "set": "urmp", "metrics": {"note_f1": 0.5}}
    late = {"id": "b", "when": "2099-01-01T00:00:00Z", "set": "urmp", "metrics": {"note_f1": 0.7}}
    repo.write_text(json.dumps(late) + "\nnot json\n" + json.dumps(early) + "\n")
    monkeypatch.setattr(history, "REPO_RESULTS", repo)
    local = tmp_path / "runs"
    local.mkdir()
    (local / "results.jsonl").write_text(json.dumps(late) + "\n")  # copied into the repo later: shown once
    history.append(history.record(CARD), local)
    runs = history.load(local)
    assert runs[0]["id"] == "a" and runs[-1]["id"] == "b" and len(runs) == 3


def test_backfilled_history_and_changes_are_well_formed():
    runs = history.read(history.REPO_RESULTS)
    assert len(runs) >= 20
    assert len({r["id"] for r in runs}) == len(runs)
    for r in runs:
        for k, v in r["metrics"].items():
            assert k == "seconds_per_minute" or 0 <= v <= 1, (r["id"], k, v)
    changes = history.changes()
    assert {c["pr"] for c in changes} >= {10, 16, 22, 24, 34}
    for c in changes:
        assert c["merged"] is None or c["merged"].endswith("Z")


def test_results_page_and_api(tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from saxscribe.app.library import Library
    from saxscribe.app.server import create_app

    history.append(history.record(CARD, note="from this machine"), tmp_path / "runs")
    client = TestClient(create_app(Library(tmp_path / "library", inline=True), runs=tmp_path / "runs"))
    assert "Results" in client.get("/results").text
    data = client.get("/api/results").json()
    assert any(r.get("note") == "from this machine" for r in data["runs"])
    assert data["targets"]["note_f1"] == {"solo": 0.8, "mix": 0.6}
    assert "omnibook" in data["mix_sets"]
    assert any(c["pr"] == 24 for c in data["changes"])
