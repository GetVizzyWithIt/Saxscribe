"""Head-to-head rows and the error breakdown behind the Results page (score/experiments.py)."""
from __future__ import annotations

import json

from saxscribe.score import experiments, history


def n(on, off, pitch, bar=None, tags=None, **kw):
    d = {"onset": on, "offset": off, "pitch": pitch, **kw}
    if bar is not None:
        d["bar"] = bar
    if tags is not None:
        d["tags"] = tags
    return d


KEY = [n(1.0, 1.4, 60, 1, heard_ok=True), n(1.5, 1.9, 62, 1, heard_ok=True), n(2.0, 2.4, 64, 2, heard_ok=False),
       n(2.5, 2.7, 64, 2), n(3.0, 3.4, 65, 3), n(3.5, 3.9, 67, 3), n(4.0, 4.4, 69, 4), n(5.0, 5.4, 71, 5)]


def test_every_key_note_and_every_note_of_ours_gets_one_kind():
    ours = [
        n(1.01, 1.4, 60, tags=[]),            # right
        n(1.62, 1.9, 62, tags=[]),            # 120 ms late: timing
        n(2.0, 2.7, 64, tags=[]),             # right, and swallows the repeat at 2.5: merged
        n(3.0, 3.4, 66, tags=[]),             # wrong pitch
        n(3.2, 3.4, 65, tags=[]),             # split off the held 65 (no key note starts here)
        n(3.5, 3.9, 67, tags=["not_sax"]),    # real note, hidden
        n(4.6, 4.9, 50, tags=[]),             # nothing in the key sounds: in a rest
        n(4.1, 4.3, 57, tags=[]),             # extra while the sax plays
        n(4.7, 4.9, 40, tags=["not_sax"]),    # hidden and not in the key: bleed hidden as it should be
    ]
    out = experiments.classify(KEY, ours)
    assert out["key_notes"] == {"right": 2, "timing": 1, "wrong_pitch": 1, "merged": 1, "hidden": 1, "missed": 2}
    assert out["our_notes"] == {"right": 2, "timing": 1, "wrong_pitch": 1, "split": 1, "in_rest": 1, "extra": 1}
    assert out["hidden_notes"] == {"in_key": 1, "not_in_key": 1}
    assert out["n_key"] == len(KEY) and out["n_est"] == 7
    assert out["key_heard_ok"] == round(2 / 3, 4)
    assert out["found_heard"] == 0.5          # of the two heard key notes, 1.0 was found, 1.5 was late
    assert sum(out["key_notes"].values()) == len(KEY)


def test_a_key_note_inside_a_sax_rest_cut_counts_as_hidden_not_missed():
    out = experiments.classify(KEY, [], cuts=[(4.8, 6.0)])
    assert out["key_notes"]["hidden"] == 1 and out["key_notes"]["missed"] == 7


def test_bars_cover_rests_and_carry_counts():
    key = [n(1.0, 1.4, 60, 1), n(3.0, 3.4, 62, 3)]          # bar 2 is a rest in the key
    ours = [n(1.0, 1.4, 60), n(2.2, 2.5, 55)]
    bars = experiments.classify(key, ours, cuts=[(2.0, 3.0)])["bars"]
    assert [b["bar"] for b in bars] == [1, 2, 3]
    assert bars[0]["right"] == 1 and bars[1]["key"] == 0 and bars[1]["extra"] == 1
    assert bars[1]["t0"] == 2.0 and bars[1]["cut"] == 1.0 and bars[2]["key"] == 1 and bars[2]["right"] == 0


def test_rows_append_and_merge_with_the_repo_file(tmp_path, monkeypatch):
    repo = tmp_path / "repo.jsonl"
    old = {"id": "a", "when": "2026-11-05T00:00:00Z", "set": "pfh", "record": None,
           "setup": {"separator": "demucs"}, "metrics": {"note_f1": 0.49}}
    repo.write_text(json.dumps(old) + "\nnot json\n")
    monkeypatch.setattr(experiments, "REPO_EXPERIMENTS", repo)
    bd = experiments.classify(KEY, [n(1.0, 1.4, 60, tags=[])])
    rec = experiments.row("new-tunes", "resolution", {"separator": "mega", "spans_from": "same", "note_finder": "ours"},
                          {"note_f1": 0.5, "sax_found": 1 / 8}, breakdown=bd, key={"version": "stem-aligned"})
    assert rec["key"] == {"heard_ok": round(2 / 3, 4), "version": "stem-aligned"} and rec["bars"]
    experiments.append(rec, tmp_path / "runs")
    rows = experiments.load(tmp_path / "runs")
    assert [r["id"] for r in rows][0] == "a" and len(rows) == 2


def test_backfilled_experiments_are_well_formed_and_reach_the_dashboard():
    rows = experiments.read(experiments.REPO_EXPERIMENTS)
    assert len(rows) >= 20 and len({r["id"] for r in rows}) == len(rows)
    for r in rows:
        assert r["setup"]["separator"] in {"demucs", "mega", "hybrid", "mvsep-web", "rd-sax", "demucs-6s", "mega-local", "rd-filosax-demucs"}
        for v in r["metrics"].values():
            assert 0 <= v <= 1
        if "key_notes" in r:
            assert set(r["key_notes"]) == set(experiments.KEY_KINDS)
            assert sum(r["key_notes"].values()) == r["n_key"]
            assert sum(r["our_notes"].values()) == r["n_est"]
    assert {r["set"] for r in rows if r["default"]} >= {"parker-band", "pfh", "bfmj", "new-tunes"}
    assert "experiments" in history.dashboard_data()
