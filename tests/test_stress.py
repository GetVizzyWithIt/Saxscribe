"""Guard metrics and the stress scorecard."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from saxscribe.score import card, metrics, refs, stress

from . import fixture

KEY = [{"onset": 0.0, "offset": 0.5, "pitch": 60}, {"onset": 0.5, "offset": 0.6, "pitch": 62},
       {"onset": 0.6, "offset": 0.7, "pitch": 64, "ghost": True}, {"onset": 2.0, "offset": 2.5, "pitch": 65}]


def test_guards_see_dropped_short_and_ghost_notes():
    # Ours keeps the long notes, drops the short ones, and adds one note in the 1.3 s rest.
    ours = [KEY[0], KEY[3], {"onset": 1.2, "offset": 1.4, "pitch": 50}]
    g = metrics.guard_scores(KEY, ours)
    assert g["short_found"] == 0.0 and g["short_notes"] == 2
    assert g["ghost_found"] == 0.0 and g["ghost_notes"] == 1
    assert abs(g["rest_seconds"] - 1.3) < 1e-9
    assert abs(g["extras_in_rests_per_min"] - 60 / 1.3) < 1e-6


def test_guards_are_perfect_on_the_key_itself():
    g = metrics.guard_scores(KEY, KEY)
    assert g["short_found"] == g["ghost_found"] == 1.0
    assert g["extras_in_rests_per_min"] == 0.0
    assert g["onset_f1_100ms"] == g["note_f1_100ms"] == 1.0


def test_100ms_forgives_late_notes_that_50ms_does_not():
    late = [{**n, "onset": n["onset"] + 0.07, "offset": n["offset"] + 0.07} for n in KEY]
    s = metrics.note_scores(KEY, late)
    assert s["note_f1_no_offset"] == 0.0 and s["note_f1_100ms"] == 1.0


def test_no_ghost_score_when_the_key_marks_none():
    plain = [{k: v for k, v in n.items() if k != "ghost"} for n in KEY]
    assert "ghost_found" not in metrics.guard_scores(plain, plain)


def test_card_shows_the_guard_table():
    c = {"set": "x", "split": "all", "settings": "default", "items": 1, "made": "now",
         "mean": {"note_f1": 0.5, "short_found": 0.8, "extras_in_rests_per_min": 2.4}, "rows": []}
    md = card.markdown(c, is_mix=True)
    assert "Short notes found" in md and "| 80.0% |" in md and "| 2.4 |" in md


def test_detune_moves_pitch_and_time_together(tmp_path):
    sr = 22050
    t = np.arange(sr) / sr
    y = 0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    up = stress.degrade(y, sr, "detune+50")
    assert abs(len(up) - len(y) / 2 ** (50 / 1200)) < 3
    spec = np.abs(np.fft.rfft(up * np.hanning(len(up))))
    peak = np.argmax(spec) * sr / len(up)
    assert abs(1200 * np.log2(peak / 440) - 50) < 5
    notes, beats = stress.shift_key([{"onset": 1.0, "offset": 2.0, "pitch": 69}], [1.0], "detune+50")
    speed = 2 ** (50 / 1200)
    assert abs(notes[0]["onset"] - 1 / speed) < 1e-9 and abs(notes[0]["pitch"] - 69.5) < 1e-9
    assert abs(beats[0] - 1 / speed) < 1e-9


def test_reverb_and_lofi_keep_length_and_key(tmp_path):
    y = fixture.make()
    for c in ("reverb", "lofi"):
        out = stress.degrade(y, fixture.RATE, c)
        assert out.shape == y.shape and np.max(np.abs(out)) <= 0.99 + 1e-6
        assert not np.allclose(out, y)
        assert stress.shift_key(fixture.truth(), None, c)[0] == fixture.truth()


def test_stressed_ref_writes_audio_once(tmp_path):
    src = tmp_path / "take.wav"
    sf.write(str(src), fixture.make(), fixture.RATE)
    ref = refs.Reference(id="fx", audio=src, notes=fixture.truth(), extra={"tags": ["vibrato"]})
    s = stress.stressed_ref(ref, "detune-25", tmp_path / "audio")
    assert s.audio.exists() and s.audio != src and s.notes[0]["pitch"] < ref.notes[0]["pitch"]
    assert stress.stressed_ref(ref, "clean", tmp_path / "audio") is ref
    rows = [{"id": "fx", "note_f1_no_offset": 0.7, "sax_found": 0.9}]
    assert stress.by_tag([ref], rows)["vibrato"]["items"] == 1
