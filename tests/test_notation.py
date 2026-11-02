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
