"""GRFIA-RealSax: the **kern reader and the answer-key loader."""
from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import soundfile as sf

from saxscribe.score import kern, refs

KERN = """**kern
*clefG2
*k[b-]
*M4/4
*MM96
=1
4c
8.d
16e
[4f
4f]
=2
2r
12g
12a
12b
4cc ee
=3
qd
4d#
4B-
2r
*-
"""


def test_kern_durations_and_pitches():
    assert kern.duration("4c") == 1 and kern.duration("8.d") == F(3, 4)
    assert kern.duration("12g") == F(1, 3) and kern.duration("2..r") == F(7, 2)
    assert kern.midi("c") == 60 and kern.midi("cc") == 72 and kern.midi("C") == 48
    assert kern.midi("BB-") == 46 and kern.midi("f#") == 66


def test_kern_parse_joins_ties_keeps_top_of_chords_and_skips_grace_notes():
    k = kern.parse(KERN)
    assert k["meter"] == "4/4" and k["tempo"] == 96
    got = [(n["start"], n["end"], n["pitch"]) for n in k["notes"]]
    assert got == [
        (0, 1, 60), (1, F(7, 4), 62), (F(7, 4), 2, 64), (2, 4, 65),   # tied f is one half note
        (6, F(19, 3), 67), (F(19, 3), F(20, 3), 69), (F(20, 3), 7, 71),
        (7, 8, 76),                                                   # chord: top note
        (8, 9, 63), (9, 10, 58),                                      # grace note skipped
    ]
    assert k["length"] == 12


def test_load_grfia_pairs_takes_with_scores_and_caches_the_aligned_key(tmp_path, monkeypatch):
    root = tmp_path / "real_a2s_sax_dataset"
    (root / "real" / "alto").mkdir(parents=True)
    (root / "krn" / "alto").mkdir(parents=True)
    (root / "Alto_Sax_Index.csv").write_text(
        "FILENAME;TYPE;TEMPO;PERFORMER;VIBRATO;GROWL\n"
        "Ex1;Exercise;96;Player;YES;NO\n"
        "Ex2;Exercise;96;Player;NO;NO\n", encoding="utf-8")
    (root / "krn" / "alto" / "Ex1.krn").write_text(KERN)
    (root / "krn" / "alto" / "Ex2.krn").write_text(KERN)
    # 12 quarters at 96 BPM is 7.5 s: Ex1 fits, Ex2 (30 s) is far too long and is skipped.
    sf.write(root / "real" / "alto" / "Ex1.wav", np.zeros(7 * 8000), 8000)
    sf.write(root / "real" / "alto" / "Ex2.wav", np.zeros(30 * 8000), 8000)
    calls = []

    def fake_align(audio, notes):
        calls.append(audio.name)
        return [{"onset": n["start"] * 0.625, "offset": n["end"] * 0.625, "pitch": n["pitch"],
                 "beat": n["start"]} for n in notes]

    monkeypatch.setattr("saxscribe.score.align.align_notes", fake_align)
    monkeypatch.setattr(refs, "grfia_key_cache", lambda horn: tmp_path / "keys" / f"grfia-{horn}")
    got = refs.load_grfia(tmp_path, "alto")
    assert [r.id for r in got] == ["Ex1"]
    r = got[0]
    assert r.notes[0]["pitch"] == 60 + refs.GRFIA_KERN_TO_CONCERT
    assert r.extra["horn"] == "alto" and r.extra["tags"] == ["vibrato"] and r.extra["tempo"] == 96
    assert (tmp_path / "keys" / "grfia-alto" / "Ex1.json").exists()
    assert (tmp_path / "keys" / "grfia-alto" / "Ex2.json").exists()   # the skip is cached too
    refs.load_grfia(tmp_path, "alto")
    assert calls == ["Ex1.wav"]   # aligned once, then read from the cache
