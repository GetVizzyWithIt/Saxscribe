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


def test_tidy_gives_every_key_note_a_length_and_keeps_them_all():
    from saxscribe.score.align import MIN_NOTE, tidy
    # A thirty-second warped onto the same instant as its neighbour (seen on GRFIA alto 000100047).
    notes = [{"onset": 1.0, "offset": 1.1146, "pitch": 71},
             {"onset": 1.1146, "offset": 1.1146, "pitch": 69},
             {"onset": 1.1146, "offset": 1.4, "pitch": 67}]
    out = tidy(notes)
    assert [n["pitch"] for n in out] == [71, 69, 67]
    assert all(n["offset"] - n["onset"] >= MIN_NOTE - 1e-9 for n in out)
    assert all(a["onset"] < b["onset"] for a, b in zip(out, out[1:]))


def test_cached_grfia_keys_are_tidied_on_load(tmp_path, monkeypatch):
    import json
    root = tmp_path / "real_a2s_sax_dataset"
    (root / "real" / "tenor").mkdir(parents=True)
    (root / "krn" / "tenor").mkdir(parents=True)
    (root / "krn" / "tenor" / "T1.krn").write_text(KERN)
    sf.write(root / "real" / "tenor" / "T1.wav", np.zeros(8000), 8000)
    cache = tmp_path / "keys" / "grfia-tenor"
    cache.mkdir(parents=True)
    (cache / "T1.json").write_text(json.dumps({"notes": [
        {"onset": 3.0, "offset": 3.9474, "pitch": 50, "beat": 4.5},
        {"onset": 3.9474, "offset": 3.9474, "pitch": 49, "beat": 4.875}], "meter": "4/4", "tempo": 96, "method": "dtw"}))
    monkeypatch.setattr(refs, "grfia_key_cache", lambda horn: cache)
    r = refs.load_grfia(tmp_path, "tenor")[0]
    assert all(n["offset"] > n["onset"] for n in r.notes)


def test_alignment_holds_on_a_repeated_figure_after_a_long_count_in(tmp_path):
    """GRFIA exercises: one short figure repeated, with seconds of silence before
    the first note. The aligned key must not slip a note or a figure."""
    from saxscribe.score import align
    from . import fixture
    rate, beat = 22050, 0.5                      # 120 BPM, eighth notes
    figure = [60, 62, 64, 62]
    pitches = (figure * 3)[:11]
    lead, tail = 2.5, 1.5
    y = np.zeros(int(rate * (lead + len(pitches) * beat / 2 + tail)))
    truth = []
    for i, p in enumerate(pitches):
        t0 = lead + i * beat / 2
        n = np.arange(int(rate * beat / 2 * 0.9))
        tone = sum(np.sin(2 * np.pi * k * fixture.hz(p) * n / rate) / k for k in range(1, 5))
        y[int(t0 * rate):int(t0 * rate) + len(n)] += 0.3 * tone * np.minimum(1, n / 200)
        truth.append(t0)
    sf.write(tmp_path / "take.wav", y, rate)
    notes = [{"start": i / 2, "end": i / 2 + 0.5, "pitch": p} for i, p in enumerate(pitches)]
    got = align.align_notes(tmp_path / "take.wav", notes)
    assert [n["pitch"] for n in got] == pitches
    errors = np.abs(np.array([n["onset"] for n in got]) - truth)
    assert np.mean(errors <= 0.05) >= 0.9, errors.round(3)


def test_steady_alignment_lines_up_a_one_pitch_drill_played_to_a_metronome(tmp_path):
    """GRFIA articulation drills: one pitch, repeated. Chroma DTW has nothing to
    lock onto there; the metronome fit must put every key note on its attack."""
    from saxscribe.score import align
    from . import fixture
    rate, tempo, played = 22050, 100.0, 1.02     # marked 100 BPM, played 2% slow
    beats = [0, 1, 2, 2.5, 3, 4, 5, 6, 6.5, 7, 8, 9, 10, 11]
    lead = 1.7
    y = np.zeros(int(rate * (lead + 12 * 0.6 * played + 1)))
    truth = []
    for b in beats:
        t0 = lead + b * 60 / tempo * played
        n = np.arange(int(rate * 0.22))
        tone = sum(np.sin(2 * np.pi * k * fixture.hz(65) * n / rate) / k for k in range(1, 5))
        y[int(t0 * rate):int(t0 * rate) + len(n)] += 0.3 * tone * np.minimum(1, n / 200)
        truth.append(t0)
    sf.write(tmp_path / "drill.wav", y, rate)
    notes = [{"start": b, "end": b + 0.5, "pitch": 65} for b in beats]
    got, fit = align.align_steady(tmp_path / "drill.wav", notes, tempo)
    assert fit >= align.STEADY_GOOD
    assert len(got) == len(beats) and all(n["pitch"] == 65 for n in got)
    errors = np.abs(np.array([n["onset"] for n in got]) - truth)
    assert errors.max() <= 0.04, errors.round(3)


def test_grfia_keys_from_the_old_aligner_are_made_again(tmp_path, monkeypatch):
    import json
    root = tmp_path / "real_a2s_sax_dataset"
    (root / "real" / "alto").mkdir(parents=True)
    (root / "krn" / "alto").mkdir(parents=True)
    for name in ("Old", "New", "Skip"):
        (root / "krn" / "alto" / f"{name}.krn").write_text(KERN)
        sf.write(root / "real" / "alto" / f"{name}.wav", np.zeros(7 * 8000), 8000)
    cache = tmp_path / "keys" / "grfia-alto"
    cache.mkdir(parents=True)
    old = {"notes": [{"onset": 1.0, "offset": 1.5, "pitch": 48, "beat": 0}], "meter": "4/4", "tempo": 96}
    (cache / "Old.json").write_text(json.dumps(old))
    (cache / "New.json").write_text(json.dumps({**old, "method": "steady"}))
    (cache / "Skip.json").write_text(json.dumps({"skip": "take/score length 3.00"}))
    made = []

    def fake_steady(audio, notes, tempo):
        made.append(audio.name)
        return [{"onset": 0.5 + n["start"] * 0.625, "offset": 0.5 + n["end"] * 0.625,
                 "pitch": n["pitch"], "beat": n["start"]} for n in notes], 0.9

    monkeypatch.setattr("saxscribe.score.align.align_steady", fake_steady)
    monkeypatch.setattr(refs, "grfia_key_cache", lambda horn: cache)
    got = {r.id: r for r in refs.load_grfia(tmp_path, "alto")}
    assert made == ["Old.wav"]
    assert set(got) == {"Old", "New"}
    assert json.loads((cache / "Old.json").read_text())["method"] == "steady"
    assert len(got["Old"].notes) > 1 and len(got["New"].notes) == 1
