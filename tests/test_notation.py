"""Layer 4: quantizing, swing, key, spelling and transposition."""
from __future__ import annotations

import json
from fractions import Fraction as F

import numpy as np
from music21 import converter

from saxscribe.horns import HORNS
from saxscribe.layers import notation

from . import fixture

SPB = 0.5  # seconds per beat at 120 BPM
GRID = [i * SPB for i in range(40)]


def at(beats_and_lengths, pitch=70, swing_pos=0.5):
    """Notes from (beat, length in beats) pairs, with off-beat eighths pushed to swing_pos."""
    out = []
    for b, n in beats_and_lengths:
        def sec(x):
            whole, frac = divmod(x, 1)
            if frac == 0.5:
                frac = swing_pos
            return (whole + frac) * SPB
        out.append({"onset": sec(b), "offset": sec(b + n) - 0.03, "pitch": pitch})
    return out


def placed(result):
    return [(p["start"], p["length"]) for p in result["notes"]]


def test_straight_eighths_and_quarters_land_on_the_grid():
    notes = at([(4, 1), (5, 0.5), (5.5, 0.5), (6, 2)])
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "straight")
    assert placed(r) == [(F(0), F(1)), (F(1), F(1, 2)), (F(3, 2), F(1, 2)), (F(2), F(2))]


def test_swing_is_detected_and_written_as_plain_eighths():
    pairs = [(4 + i * 0.5, 0.5) for i in range(16)]
    notes = at(pairs, swing_pos=2 / 3)
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    assert r["swing_source"] == "detected"
    assert abs(r["swing"] - 2 / 3) < 0.03
    assert all(length == F(1, 2) for _, length in placed(r))


def test_straight_playing_is_not_called_swing():
    notes = at([(4 + i * 0.5, 0.5) for i in range(16)])
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    assert r["swing"] == 0.5


def test_triplets_win_only_when_they_fit():
    notes = at([(4, 1 / 3), (4 + 1 / 3, 1 / 3), (4 + 2 / 3, 1 / 3), (5, 1)])
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "straight")
    assert placed(r)[:3] == [(F(0), F(1, 3)), (F(1, 3), F(1, 3)), (F(2, 3), F(1, 3))]


def test_tracked_beats_absorb_tempo_drift():
    beats = list(np.cumsum([0.0] + [0.5 + 0.01 * i for i in range(30)]))  # slowing down
    notes = [{"onset": beats[k], "offset": beats[k + 1] - 0.02, "pitch": 70} for k in range(4, 12)]
    r = notation.quantize(notes, beats, beats[::4], None, "straight")
    assert placed(r) == [(F(i), F(1)) for i in range(8)]


def test_spelling_follows_the_key():
    name = lambda m, k: notation.spell(m, k).nameWithOctave
    assert name(70, "B- major") == "B-4"
    assert name(68, "E major") == "G#4"
    assert name(66, "F major") == "G-4"   # chromatic in a flat key: flat
    assert name(63, "G major") == "D#4"   # chromatic in a sharp key: sharp
    assert name(60, "C# major") == "B#3"  # B# is still MIDI 60
    assert notation.spell(60, "C# major").midi == 60


def test_key_finder():
    bb_major = [58, 60, 62, 63, 65, 67, 69, 70, 65, 62, 58]
    assert notation.find_key(bb_major) == "B- major"


def test_alto_part_is_written_a_major_sixth_up():
    r = {"key": "B- major", "tempo_bpm": 120, "notes": [{"start": F(0), "length": F(4), "pitch": 70}]}
    written = notation.build_score(r, HORNS["alto"], written=True)
    n = written.recurse().notes.first()
    assert n.pitch.midi == 79 and n.pitch.name == "G"
    assert written.recurse().getElementsByClass("Key").first().tonic.name == "G"


def test_fixture_notation(take):
    data = json.loads(take.notation.read_text())
    assert data["swing"] == 0.5
    assert data["key"] in ("B- major", "F major", "G minor", "D minor")
    for path in (take.musicxml, take.written_musicxml("alto")):
        score = converter.parse(str(path))
        assert len(score.recurse().notes) == len(data["notes"])
    # Rhythm: quantize the detected notes on the phrase's true beat grid, so this
    # checks the notation step itself. How well a beat tracker follows a solo
    # horn with no band is a separate question (Beat This! and librosa place
    # this phrase's last bars differently), measured by beat F1 in the scorecard.
    from saxscribe.layers import notes as notes_layer
    est = notes_layer.read(take)["notes"]
    grid = [i * fixture.BEAT for i in range(40)]
    placed = notation.quantize(est, grid, grid[::4], fixture.BPM, "auto")["notes"]
    starts = [p["start"] for p in placed]
    truth = [F(b).limit_denominator(8) for b, _, _, _ in fixture.PHRASE]
    rel = [s - starts[0] for s in starts]
    expected = [t - truth[0] for t in truth]
    if len(starts) == len(truth):
        assert rel == expected
    else:  # a missed or extra note upstream: the rest of the rhythm must still line up
        assert len(set(rel) & set(expected)) >= 0.9 * len(truth)


def test_pdf_is_engraved_when_musescore_is_there(take, tmp_path, monkeypatch):
    """A stand-in for MuseScore that writes a file where it is told to (-o <pdf> <musicxml>)."""
    fake = tmp_path / "mscore"
    fake.write_text('#!/bin/sh\nprintf "%%PDF-1.4 fake" > "$2"\n')
    fake.chmod(0o755)
    monkeypatch.setenv("SAXSCRIBE_MUSESCORE", str(fake))
    from saxscribe.layers import engrave
    out = tmp_path / "score.pdf"
    assert engrave.to_pdf(take.musicxml, out)
    assert out.read_bytes().startswith(b"%PDF")


def test_no_musescore_means_no_pdf_and_no_error(take, tmp_path, monkeypatch):
    monkeypatch.setenv("SAXSCRIBE_MUSESCORE", str(tmp_path / "missing"))
    from saxscribe.layers import engrave
    assert not engrave.to_pdf(take.musicxml, tmp_path / "score.pdf")


def test_a_sparse_beat_grid_keeps_every_note():
    """Beat This! on a lone horn can return a dozen beats for a minute and a half
    (seen on an Omnibook stem). Every note must still be written."""
    beats = [16.62, 28.42, 66.48, 67.18, 67.88, 68.24, 85.92, 89.36, 89.72, 90.06, 90.42, 90.8, 91.2]
    notes = [{"onset": 4.0 + 0.22 * i, "offset": 4.0 + 0.22 * i + 0.18, "pitch": 60 + i % 12} for i in range(398)]
    r = notation.quantize(notes, beats, beats[:1], 85.7, "straight")
    assert len(r["notes"]) == len(notes)
    assert [p["index"] for p in r["notes"]] == list(range(len(notes)))
    starts = [p["start"] for p in r["notes"]]
    assert all(b > a for a, b in zip(starts, starts[1:]))
    assert all(p["length"] > 0 for p in r["notes"])
    assert r["grid"].startswith("filled")
    assert r["squeezed"] < 0.1 * len(notes)


def test_notes_on_one_grid_slot_are_both_written():
    notes = [{"onset": 2.00, "offset": 2.02, "pitch": 70}, {"onset": 2.03, "offset": 2.5, "pitch": 72}]
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "straight")
    assert [p["pitch"] for p in r["notes"]] == [70, 72]
    assert r["notes"][1]["start"] > r["notes"][0]["start"]


def musicxml_problems(path) -> list[str]:
    """What MuseScore refuses: notes without a <type>, tuplets other than 3:2,
    and tuplet brackets that do not open and close in pairs."""
    import xml.etree.ElementTree as ET
    problems, open_tuplets = [], 0
    for n in ET.parse(path).getroot().iter("note"):
        rest = n.find("rest")
        whole_bar_rest = rest is not None and rest.get("measure") == "yes"
        if n.find("type") is None and not whole_bar_rest:
            problems.append("note without type")
        tm = n.find("time-modification")
        if tm is not None and (tm.findtext("actual-notes"), tm.findtext("normal-notes")) != ("3", "2"):
            problems.append(f"tuplet {tm.findtext('actual-notes')}:{tm.findtext('normal-notes')}")
        for t in n.iter("tuplet"):
            if t.get("type") == "start":
                open_tuplets += 1
            elif t.get("type") == "stop":
                open_tuplets -= 1
            if open_tuplets < 0 or open_tuplets > 1:
                problems.append("tuplet brackets out of step")
    if open_tuplets:
        problems.append("unclosed tuplet")
    return problems


def test_messy_timing_still_writes_clean_musicxml(tmp_path):
    """Random human timing over a sparse beat grid (what an Omnibook stem gives)
    must come out as plain values and 3:2 triplets only."""
    rng = np.random.default_rng(3)
    t, notes = 4.0, []
    for _ in range(300):
        d = float(rng.choice([0.09, 0.12, 0.18, 0.25, 0.37, 0.5, 0.9]))
        notes.append({"onset": t, "offset": t + d * 0.9, "pitch": int(rng.integers(55, 80))})
        t += d + float(rng.choice([0, 0, 0.03, 0.2]))
    beats = [16.62, 28.42, 66.48, 67.18, 67.88, 68.24, 85.92, 89.36, 89.72, 90.06]
    r = notation.quantize(notes, beats, beats[:1], None, "auto")
    assert len(r["notes"]) == len(notes)
    r["key"] = "B- major"
    path = tmp_path / "messy.musicxml"
    notation.build_score(r, HORNS["alto"], written=True).write("musicxml", fp=str(path))
    assert musicxml_problems(path) == []
    assert len([n for n in converter.parse(str(path)).recurse().notes if not n.tie or n.tie.type == "start"]) == len(notes)


# ---------------------------------------------------------------- readability

def swung_line(seed, beats=24, ratio=0.62, jitter=0.025, triplet_beats=()):
    """Swung eighths with human timing (25 ms wobble), plus some real triplet beats."""
    rng = np.random.default_rng(seed)
    onsets, truth = [], []
    for b in range(4, 4 + beats):
        for frac in ((0, 1 / 3, 2 / 3) if b in triplet_beats else (0, ratio)):
            onsets.append((b + frac) * SPB + rng.normal(0, jitter))
            truth.append(F(b - 4) + (F(frac).limit_denominator(3) if b in triplet_beats else F(frac > 0, 2)))
    notes = [{"onset": a, "offset": a + (z - a) * 0.85, "pitch": 70}
             for a, z in zip(onsets, onsets[1:] + [onsets[-1] + 0.3])]
    return notes, truth


def test_a_swung_line_reads_as_eighths_not_dotted_figures():
    notes, truth = swung_line(5)
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    assert r["swing_source"] == "detected"
    starts = [p["start"] for p in r["notes"]]
    assert sum(s == t for s, t in zip(starts, truth)) >= 0.95 * len(truth)
    assert all(s.denominator in (1, 2) for s in starts)


def test_triplets_inside_a_swing_line_are_kept():
    notes, truth = swung_line(6, triplet_beats=(9, 15, 21))
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    starts = [p["start"] for p in r["notes"]]
    trips = [s for s in starts if s.denominator == 3]
    assert len(trips) == 6  # two inner notes in each of three triplet beats
    assert sum(s == t for s, t in zip(starts, truth)) >= 0.9 * len(truth)


def test_a_short_note_in_swing_is_an_eighth_not_a_sixteenth_and_rest():
    notes, _ = swung_line(7)
    notes[4]["offset"] = notes[4]["onset"] + 0.06  # a short, clipped note
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    assert all(p["length"] >= F(1, 2) or p["start"].denominator == 3 for p in r["notes"][:-1])


def test_empty_bars_become_one_multibar_rest(tmp_path):
    r = {"key": "B- major", "tempo_bpm": 120,
         "notes": [{"start": F(0), "length": F(4), "pitch": 70}, {"start": F(20), "length": F(4), "pitch": 72}]}
    path = tmp_path / "rests.musicxml"
    notation.build_score(r, HORNS["alto"], written=True).write("musicxml", fp=str(path))
    text = path.read_text()
    assert '<multiple-rest use-symbols="no">4</multiple-rest>' in text
    assert musicxml_problems(path) == []


def test_written_part_is_spelled_in_its_own_key():
    # Concert B major on alto is G# major written (8 sharps): write it as A-flat major.
    assert notation.display_key("B major", HORNS["alto"]) == "A- major"
    assert notation.display_key("B- major", HORNS["tenor"]) == "C major"
    chromatic = [{"start": F(i, 2), "length": F(1, 2), "pitch": 58 + i} for i in range(24)]
    for horn in ("alto", "tenor"):
        for key in ("B- major", "F major", "D minor", "E- major"):
            score = notation.build_score({"key": key, "tempo_bpm": 120, "notes": chromatic},
                                         HORNS[horn], written=True)
            names = {}
            for n in score.recurse().notes:
                names.setdefault(n.pitch.pitchClass, set()).add(n.pitch.name)
            assert all(len(v) == 1 for v in names.values()), (horn, key, names)
            assert [n.pitch.midi for n in score.recurse().notes] == [58 + i + HORNS[horn].written_shift
                                                                     for i in range(24)]


def test_off_grid_spots_after_a_triplet_are_cleaned_up(tmp_path):
    """Blues for Mary Jane bar 63: a squeeze after a triplet point left a note on
    23/24 of a beat, written as a 6:5 tuplet that MuseScore refused (exit 40)."""
    placed = [{"index": 0, "start": F(0), "length": F(3, 4), "pitch": 62},
              {"index": 1, "start": F(3, 4), "length": F(5, 24), "pitch": 74},
              {"index": 2, "start": F(23, 24), "length": F(1, 24), "pitch": 62},
              {"index": 3, "start": F(1), "length": F(2, 3), "pitch": 64},
              {"index": 4, "start": F(5, 3) + F(1, 8), "length": F(5, 24), "pitch": 65},
              {"index": 5, "start": F(2), "length": F(2), "pitch": 67}]
    fixed = notation.one_grid_per_beat([dict(p) for p in placed])
    assert len(fixed) == len(placed)
    points = [x for p in fixed for x in (p["start"], p["start"] + p["length"])]
    assert all(notation.on_grid(x) for x in points)
    assert all(b["start"] > a["start"] for a, b in zip(fixed, fixed[1:]))
    path = tmp_path / "bar63.musicxml"
    notation.build_score({"key": "C minor", "tempo_bpm": 120, "notes": fixed}, HORNS["tenor"], True
                         ).write("musicxml", fp=str(path))
    assert musicxml_problems(path) == []


def test_pdfs_can_be_turned_off(take, tmp_path, monkeypatch):
    fake = tmp_path / "mscore"
    fake.write_text('#!/bin/sh\ntouch "$2"\nexit 1\n')
    fake.chmod(0o755)
    from saxscribe.layers import engrave
    monkeypatch.setenv("SAXSCRIBE_MUSESCORE", "off")
    assert engrave.turned_off() and engrave.find_musescore() is None
    assert not engrave.to_pdf(take.musicxml, tmp_path / "score.pdf")
    assert not (tmp_path / "score.pdf").exists()
