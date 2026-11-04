"""Range rules: the horn table, and what happens to notes outside a horn's range."""
from __future__ import annotations

import json

import numpy as np
import pytest

from saxscribe.horns import HORNS, hz
from saxscribe.layers import ranges

RATE = ranges.RATE


def tone(midi: float, seconds: float = 0.5, partials=None) -> np.ndarray:
    """A sax-like note: partial k at weight partials[k-1] (default: strong, slowly falling)."""
    partials = partials or [0.9 ** k / k ** 0.5 for k in range(1, 9)]
    t = np.arange(int(seconds * RATE)) / RATE
    f = hz(midi)
    y = sum(w * np.sin(2 * np.pi * f * k * t) for k, w in enumerate(partials, 1) if f * k < RATE / 2)
    return 0.3 * y / np.max(np.abs(y)) + np.random.default_rng(1).normal(0, 0.001, len(t))


def note(pitch, onset=0.0, offset=0.5, tags=None):
    return {"onset": onset, "offset": offset, "pitch": pitch, "cents": 0.0, "tags": list(tags or [])}


def test_the_table_holds_each_sax_at_concert_pitch():
    alto, tenor, bari, sop = HORNS["alto"], HORNS["tenor"], HORNS["baritone"], HORNS["soprano"]
    assert (alto.low, alto.top, alto.altissimo) == (49, 81, 96)    # Db3, A5, C7
    assert (tenor.low, tenor.top, tenor.altissimo) == (44, 76, 91)  # Ab2, E5, G6
    assert (bari.low, bari.top) == (36, 69)                         # C2 (low A), A4
    assert (sop.low, sop.top) == (56, 88)                           # Ab3, E6
    assert alto.register(85) == "altissimo" and alto.register(97) == "above" and alto.register(48) == "below"
    # The search reaches every altissimo note: tenor used to stop at 1100 Hz (written D#7).
    assert tenor.max_hz > hz(tenor.altissimo) and alto.min_hz < hz(alto.low)


def test_altissimo_is_kept_and_tagged_not_moved():
    n = note(90)  # concert F#6: written D#7 on alto
    counts = ranges.apply([n], HORNS["alto"], tone(90))
    assert n["pitch"] == 90 and "detected_pitch" not in n
    assert n["tags"] == ["altissimo"] and counts["altissimo"] == 1 and counts["moved"] == 0


def test_a_low_note_heard_an_octave_up_is_tagged_overtone():
    # Low D (concert D3 = 50) with a weak fundamental and a loud second partial:
    # the detector reported D4 (62).
    y = tone(50, partials=[0.3, 1.0, 0.6, 0.5, 0.35, 0.25, 0.15, 0.1])
    kept = note(62)
    ranges.apply([kept], HORNS["alto"], y, mode="flag")
    assert kept["pitch"] == 62 and "overtone" in kept["tags"]  # flag: tagged, kept as heard
    plain = note(62)
    ranges.apply([plain], HORNS["alto"], y)  # default: no overtone check on playable notes
    assert plain["pitch"] == 62 and plain["tags"] == []
    moved = note(62)
    ranges.apply([moved], HORNS["alto"], y, mode="overtones")
    assert moved["pitch"] == 50 and moved["detected_pitch"] == 62


def test_a_clean_note_is_not_called_an_overtone():
    for p in (52, 62, 72, 80):
        n = note(p)
        ranges.apply([n], HORNS["alto"], tone(p), mode="flag")
        assert "overtone" not in n["tags"], p


def test_above_the_altissimo_moves_down_to_the_fundamental():
    # Concert A5 (81) whose third partial (E7, 100) the detector picked: above any alto altissimo.
    y = tone(81, partials=[0.5, 0.6, 1.0, 0.4, 0.3, 0.2])
    n = note(100)
    ranges.apply([n], HORNS["alto"], y)
    assert n["pitch"] == 81 and n["detected_pitch"] == 100 and "octave_down" in n["tags"]
    # With no audio to say which partial, an octave at a time.
    n = note(100)
    ranges.apply([n], HORNS["alto"])
    assert n["pitch"] == 88 and "octave_down" in n["tags"]


def test_below_the_low_note():
    far, bend = note(37), note(48)
    counts = ranges.apply([far, bend], HORNS["alto"])
    assert far["pitch"] == 49 and far["detected_pitch"] == 37 and "octave_up" in far["tags"]
    assert bend["pitch"] == 48 and bend["tags"] == ["below_range", "not_sax"]  # kept, off the score
    assert counts["moved"] == 1


def test_a_note_just_below_the_horn_is_kept_but_left_off_the_score():
    # Pennies From Heaven: piano/bass a half step under tenor low Bb came out as red sax notes.
    bleed, real = note(43), note(44)
    counts = ranges.apply([bleed, real], HORNS["tenor"])
    assert bleed["pitch"] == 43 and bleed["tags"] == ["below_range", "not_sax"]  # kept, not moved
    assert real["tags"] == [] and counts["below_range"] == 1
    low_a = note(36)  # baritone low A (concert C2) is in range
    ranges.apply([low_a], HORNS["baritone"])
    assert low_a["tags"] == []


def test_flag_mode_moves_nothing_and_off_does_nothing():
    a, b = note(37), note(100)
    ranges.apply([a, b], HORNS["alto"], mode="flag")  # no audio here, so no overtone tags
    assert (a["pitch"], b["pitch"]) == (37, 100) and a["tags"] == b["tags"] == ["out_of_range"]
    c = note(37)
    assert ranges.apply([c], HORNS["alto"], mode="off") == {"mode": "off"} and c["tags"] == []


def test_a_take_made_with_the_wrong_horn_is_left_alone():
    # A tenor line (concert Ab2-C3) transcribed as alto: no octave moves, a hint instead.
    notes = [note(p, i * 0.5, i * 0.5 + 0.4) for i, p in enumerate([44, 45, 46, 47, 44, 46, 55, 57])]
    counts = ranges.apply(notes, HORNS["alto"])
    assert counts["moved"] == 0 and counts["better_horn"] == "tenor"
    assert [n["pitch"] for n in notes[:6]] == [44, 45, 46, 47, 44, 46]
    assert all("out_of_range" in n["tags"] for n in notes[:6] if n["pitch"] < 47)
    assert notes[3]["tags"] == ["below_range", "not_sax"]  # within a bend of the low note


def test_notes_where_the_sax_lays_out_are_skipped():
    bass = note(30, tags=["not_sax"])
    ranges.apply([bass], HORNS["alto"])
    assert bass["pitch"] == 30 and bass["tags"] == ["not_sax"]


def test_notes_outside_the_range_show_red_on_the_score():
    from music21 import note as m21note, stream
    part = stream.Part([m21note.Note(midi=60 + 9), m21note.Note(midi=40 + 9)])  # written for alto
    assert ranges.mark_unplayable(part, HORNS["alto"], 9) == 1
    colours = [n.style.color for n in part.notes]
    assert colours == [None, ranges.UNPLAYABLE_COLOR]


def test_the_fixture_passes_the_range_rules_untouched(take):
    data = json.loads(take.notes.read_text())
    assert not any("detected_pitch" in n for n in data["notes"])
    assert not any(set(n["tags"]) & {"overtone", "out_of_range", "octave_up", "octave_down"}
                   for n in data["notes"])
    assert take.read_manifest()["layers"]["notes"]["range"]["mode"] == "out"


@pytest.mark.parametrize("mode", ranges.MODES)
def test_cli_takes_every_range_mode(fixture_wav, tmp_path, mode):
    from saxscribe.__main__ import main
    out = tmp_path / mode
    assert main(["transcribe", str(fixture_wav), "-o", str(out), "--range-rules", mode,
                 "--notes-tool", "contour", "--contour-tool", "pyin"]) == 0
    assert (out / "notes.json").exists()


def test_crepe_never_searches_near_its_top_bins():
    # A band reaching CREPE's top bins made it lock there with confidence 0 (Omnibook, 2026-11-04).
    from saxscribe.horns import CREPE_MAX_HZ
    assert CREPE_MAX_HZ <= 1600
    assert hz(HORNS["tenor"].altissimo) <= CREPE_MAX_HZ  # tenor altissimo still on the pitch line
