"""Rhythm scorecard on a tiny Weimar-Jazz-Database-shaped sqlite file."""
from __future__ import annotations

import sqlite3
from fractions import Fraction

from saxscribe.score import rhythm


def make_db(path, solos):
    con = sqlite3.connect(path)
    con.executescript("""
      CREATE TABLE solo_info (melid INTEGER, performer TEXT, title TEXT, instrument TEXT, style TEXT,
                              avgtempo FLOAT, tempoclass TEXT, rhythmfeel TEXT, signature TEXT);
      CREATE TABLE beats (beatid INTEGER PRIMARY KEY, melid INTEGER, onset REAL, bar INTEGER, beat INTEGER);
      CREATE TABLE melody (eventid INTEGER PRIMARY KEY, melid INTEGER, onset REAL, pitch REAL, duration REAL,
                           division INTEGER, bar INTEGER, beat INTEGER, tatum INTEGER);
    """)
    for melid, performer, instrument, spb, figure in solos:
        con.execute("INSERT INTO solo_info VALUES (?,?,?,?,?,?,?,?,?)",
                    (melid, performer, f"tune {melid}", instrument, "BEBOP", 60 / spb, "MEDIUM", "SWING", "4/4"))
        t0 = 1.0
        for i in range(32):
            con.execute("INSERT INTO beats (melid, onset, bar, beat) VALUES (?,?,?,?)",
                        (melid, t0 + i * spb, i // 4 + 1, i % 4 + 1))
        for i in range(4, 28):
            for frac, division, tatum in figure(i):
                on = t0 + (i + frac) * spb
                con.execute("INSERT INTO melody (melid, onset, pitch, duration, division, bar, beat, tatum) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (melid, on, 60 + i % 5, spb * 0.4, division, i // 4 + 1, i % 4 + 1, tatum))
    con.commit()
    con.close()


def straight_eighths(i):
    return [(0.0, 2, 1), (0.5, 2, 2)]


def triplets_every_other_beat(i):
    if i % 2:
        return [(0.0, 3, 1), (1 / 3, 3, 2), (2 / 3, 3, 3)]
    return [(0.0, 1, 1)]


def test_rhythm_card_gets_clean_lines_right_and_keeps_every_note(tmp_path):
    db = tmp_path / "wjazzd.db"
    make_db(db, [(1, "A", "ts", 0.5, straight_eighths), (2, "B", "as", 0.4, triplets_every_other_beat),
                 (52, "Charlie Parker", "as", 0.3, straight_eighths), (3, "C", "tp", 0.5, straight_eighths)])
    solos = rhythm.load(db)
    assert [s["melid"] for s in solos] == [1, 2, 3]          # 52 is also in the Omnibook
    assert solos[1]["notes"][2]["place"] == 5 + Fraction(1, 3)
    assert [s["melid"] for s in rhythm.load(db, saxes=True)] == [1, 2]
    c = rhythm.card(solos)
    assert c["items"] == 3
    assert c["mean"]["notes_kept"] == 1.0
    assert c["mean"]["position_exact"] >= 0.95, [r["position_exact"] for r in c["rows"]]
    assert 0.9 <= c["rows"][1]["triplet_ratio"] <= 1.1
    assert set(c["by"]["instrument"]) == {"as", "tp", "ts"}


def test_rhythm_split_is_by_performer(tmp_path):
    db = tmp_path / "wjazzd.db"
    make_db(db, [(i, f"player {i % 7}", "ts", 0.5, straight_eighths) for i in range(1, 15)])
    train, test = rhythm.load(db, "train"), rhythm.load(db, "test")
    players = lambda ss: {s["info"]["performer"] for s in ss}
    assert not players(train) & players(test)
    assert len(train) + len(test) == 14


def test_rhythm_command_writes_a_card(tmp_path, capsys):
    from saxscribe.__main__ import main
    db = tmp_path / "wjazzd.db"
    make_db(db, [(1, "A", "ts", 0.5, straight_eighths)])
    assert main(["rhythm", "--data", str(db), "--runs", str(tmp_path / "runs")]) == 0
    assert "Rhythm scorecard" in capsys.readouterr().out
    assert list((tmp_path / "runs" / "rhythm").glob("wjd-rhythm-all-*.json"))
