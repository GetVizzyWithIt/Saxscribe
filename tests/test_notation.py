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
    assert r["grid"].startswith(("filled", "from the notes"))
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
            # one rising run: each pitch spelled one way all through (sharps going up)
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


def test_a_lone_horn_with_a_wrong_sparse_tracker_gets_its_beat_from_the_notes():
    """Omnibook 7XTyc: Beat This! gave 13 beats about 1.5 beats apart, so a
    261 BPM line was written at 162 BPM, full of triplets and 32nds."""
    spb = 0.23
    notes, truth = [], []
    rng = np.random.default_rng(4)
    for b in range(8, 8 + 160):
        for frac in (0, 0.62):
            t = b * spb + frac * spb + rng.normal(0, 0.008)
            notes.append({"onset": t, "offset": t + 0.09, "pitch": 60 + b % 12})
    wrong = [notes[0]["onset"] + 0.36 * k * 9 for k in range(12)]  # sparse and at the wrong spacing
    r = notation.quantize(notes, wrong, wrong[:1], 109.0, "auto")
    assert r["grid"].startswith("from the notes")
    assert abs(r["tempo_bpm"] - 60 / spb) < 8
    starts = [p["start"] for p in r["notes"]]
    assert sum(s.denominator in (1, 2) for s in starts) >= 0.95 * len(starts)
    assert r["squeezed"] == 0


def test_a_steady_tracked_grid_is_kept():
    notes = at([(4 + i * 0.5, 0.5) for i in range(32)], swing_pos=0.62)
    r = notation.quantize(notes, GRID, GRID[::4], 120.0, "auto")
    assert r["grid"] == "tracked"


def blues_in_c():
    """A 12-bar blues line in C: C7 riffs with the flat third and seventh, F7 for the IV."""
    i_riff = [60, 63, 64, 67, 70, 69, 67, 60]      # C Eb E G Bb A G C
    iv_riff = [65, 69, 72, 75, 74, 72, 69, 65]     # F A C Eb D C A F
    v_riff = [67, 71, 74, 77, 74, 71, 67, 62]      # G B D F D B G D
    bars = [i_riff, iv_riff, i_riff, i_riff, iv_riff, iv_riff, i_riff, i_riff,
            v_riff, iv_riff, i_riff, i_riff]
    pitches = [p for bar in bars for p in bar] + [60]
    lengths = [0.25] * (len(pitches) - 1) + [2.0]
    return pitches, lengths


def test_key_finder_hears_the_blues_home_note():
    pitches, lengths = blues_in_c()
    assert notation.find_key(pitches, lengths) == "C major"


def test_key_finder_keeps_minor_keys():
    d_minor = [62, 65, 69, 74, 72, 70, 69, 67, 65, 64, 62, 61, 62, 65, 69, 62]
    assert notation.find_key(d_minor) == "D minor"


def test_syncopations_are_written_as_one_note_not_tied_eighths(tmp_path):
    """Eighth-quarter-eighth, the way a chart writes it; ties only across the middle of the bar."""
    P = notation.pieces
    assert P(F(1, 2), F(3, 2)) == [(F(1, 2), F(1))]          # syncopated quarter
    assert P(F(1, 2), F(2)) == [(F(1, 2), F(3, 2))]          # syncopated dotted quarter
    assert P(F(0), F(3, 2)) == [(F(0), F(3, 2))]             # dotted quarter on the beat
    assert P(F(3, 2), F(5, 2)) == [(F(3, 2), F(1, 2)), (F(2), F(1, 2))]  # crosses the middle: tied
    assert P(F(1, 3), F(4, 3)) == [(F(1, 3), F(2, 3)), (F(1), F(1, 3))]  # triplets stay inside their beat
    r = {"key": "F major", "tempo_bpm": 200,
         "notes": [{"start": F(0), "length": F(1, 2), "pitch": 65}, {"start": F(1, 2), "length": F(1), "pitch": 67},
                   {"start": F(3, 2), "length": F(1, 2), "pitch": 69}, {"start": F(2), "length": F(2), "pitch": 70}]}
    path = tmp_path / "sync.musicxml"
    score = notation.build_score(r, HORNS["tenor"], written=True)
    score.write("musicxml", fp=str(path))
    assert musicxml_problems(path) == []
    assert not any(n.tie for n in score.recurse().notes)
    assert [n.duration.quarterLength for n in score.recurse().notes] == [0.5, 1.0, 0.5, 2.0]


def test_chromatic_notes_are_spelled_the_way_the_line_moves():
    up = notation.spell(66, "C major", rising=True).name      # F# on the way up
    down = notation.spell(66, "C major", rising=False).name   # Gb on the way down
    assert (up, down) == ("F#", "G-")
    assert notation.spell(66, "C major").name == "G-"          # no direction: the key's way (flats in C)
    assert notation.spell(66, "D major", rising=False).name == "F#"   # in the key: never respelled


def test_a_rising_chromatic_run_is_written_in_sharps():
    r = {"key": "C major", "tempo_bpm": 120,
         "notes": [{"start": F(i, 2), "length": F(1, 2), "pitch": p} for i, p in enumerate([65, 66, 67, 68, 69])]}
    names = [n.pitch.name for n in notation.build_score(r, HORNS["alto"], written=False).recurse().notes]
    assert names == ["F", "F#", "G", "G#", "A"]


# ---------------------------------------------------------------- slow tunes

def slow_run(figures, spb=1.0, jitter=0.012, seed=7):
    """A ballad line at 60 BPM: each beat split into `figures[b]` even notes."""
    rng = np.random.default_rng(seed)
    grid = [i * spb for i in range(len(figures) + 8)]
    notes, truth = [], []
    for b, k in enumerate(figures):
        for j in range(k):
            on = (b + 4 + j / k) * spb + rng.normal(0, jitter)
            notes.append({"onset": on, "offset": on + 0.85 * spb / k, "pitch": 60 + (b + j) % 7})
            truth.append(F(b) + F(j, k))
    return notes, truth, grid


def test_a_ballad_run_of_six_and_eight_to_a_beat_is_written_where_it_was_played(tmp_path):
    """Sextuplets and thirty-seconds: a busy beat no longer piles notes onto one
    spot and pushes the rest of the run late (WJD ballads were 85% late misses)."""
    notes, truth, grid = slow_run([1, 6, 2, 8, 6, 1, 4, 6])
    r = notation.quantize(notes, grid, grid[::4], 60.0, "auto")
    starts = [p["start"] - r["shift"] - 4 for p in r["notes"]]
    assert len(starts) == len(notes)
    assert sum(s == t for s, t in zip(starts, truth)) >= 0.9 * len(truth), list(zip(starts, truth))
    path = tmp_path / "ballad.musicxml"
    notation.build_score(r, HORNS["alto"], written=False).write("musicxml", fp=str(path))
    assert musicxml_problems(path) == []
    assert len([n for n in converter.parse(str(path)).recurse().notes if not n.tie or n.tie.type == "start"]) == len(notes)


def test_a_sextuplet_beat_is_written_in_triplet_sixteenths():
    assert notation.pieces(F(1, 6), F(1), frozenset({0})) == [(F(k, 6), F(1, 6)) for k in range(1, 6)]
    assert notation.pieces(F(1, 3), F(1)) == [(F(1, 3), F(2, 3))]
    assert all(n in (F(1, 3), F(2, 3), F(1, 6)) for _, n in notation.pieces(F(1, 6), F(1)))


def test_the_phrase_chooser_keeps_one_feel_through_a_phrase():
    """A beat that fits sixteenths a hair better than triplets, between two triplet
    beats, stays a triplet once changing feel inside a phrase has a cost; an
    empty beat starts a new phrase, which may change feel for free."""
    T, S = notation.TRIPLET, notation.STRAIGHT
    tri = (0.10, T, [F(0), F(1, 3), F(2, 3)], [F(0), F(1, 3), F(2, 3)])
    six = (0.30, S, [F(0), F(1, 4), F(3, 4)], [F(0), F(1, 4), F(3, 4)])
    near_tri = (0.21, T, [F(0), F(1, 3)], [F(0), F(1, 3)])
    near_six = (0.20, S, [F(0), F(1, 4)], [F(0), F(1, 4)])
    options = {0: [tri, six], 1: [near_tri, near_six], 2: [tri, six], 4: [near_tri, near_six]}
    free = notation.choose_grids(options, 0.0)
    assert free[1][1] is S and free[4][1] is S
    phrased = notation.choose_grids(options, 0.4)
    assert phrased[1][1] is T          # inside the phrase: keeps the triplet feel
    assert phrased[4][1] is S          # after an empty beat: a new phrase


def test_bars_follow_most_downbeats_not_a_wrong_first_one():
    # The tracker's first downbeat lands on beat 2 of the bar; the rest are right (beats 4, 8, 12, ...).
    downbeats = [GRID[2]] + GRID[4::4]
    notes = at([(4, 1), (5, 1), (6, 2)])
    r = notation.quantize(notes, GRID, downbeats, 120.0, "straight")
    assert placed(r)[0][0] % 4 == 0  # the note on the downbeat starts a bar
    assert notation.bar_phase([2, 4, 8, 12]) == 0


def test_bar_phase_tie_keeps_the_first_downbeat():
    assert notation.bar_phase([2, 4, 10, 12]) == 2
    assert notation.bar_phase([]) == 0


TRUE = [i * SPB for i in range(160)]  # 40 bars at 120 BPM
DOWN = TRUE[::4]


def bars_in_step(beats, phase):
    idx, _ = notation.downbeat_places(beats, DOWN)
    return all((k - phase) % 4 == 0 for k in idx)


def test_an_extra_tracked_beat_is_merged_so_later_bars_stay_in_step():
    tracked = TRUE[:81] + [TRUE[80] + 0.25] + TRUE[81:]  # one beat too many in bar 21
    assert not bars_in_step(tracked, notation.bar_phase(notation.downbeat_places(tracked, DOWN)[0]))
    fixed, phase, fixes = notation.align_bars(tracked, DOWN)
    assert len(fixed) == len(TRUE) and bars_in_step(fixed, phase)
    assert [f["beats"] for f in fixes] == [-1]


def test_a_missing_beat_is_put_back():
    tracked = TRUE[:101] + TRUE[102:]  # one beat lost in bar 26
    fixed, phase, fixes = notation.align_bars(tracked, DOWN)
    assert len(fixed) == len(TRUE) and bars_in_step(fixed, phase)
    assert abs(fixed[101] - TRUE[101]) < 1e-9
    assert [f["beats"] for f in fixes] == [1]


def test_a_steady_grid_with_a_stray_downbeat_is_left_alone():
    downs = DOWN[:10] + [DOWN[10] + SPB] + DOWN[11:]  # one downbeat a beat late
    fixed, phase, fixes = notation.align_bars(TRUE, downs)
    assert fixed == TRUE and phase == 0 and fixes == []
