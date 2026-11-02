"""The CREPE Notes style note cutter (saxscribe/layers/segment.py)."""
from __future__ import annotations

import numpy as np

from saxscribe.layers import notes, segment
from saxscribe.pipeline import transcribe
from saxscribe.score import metrics

from . import fixture


def test_segment_finds_the_phrase(fixture_wav, tmp_path):
    take = transcribe(fixture_wav, tmp_path, contour_tool="pyin", notes_tool="segment")
    est = notes.read(take)["notes"]
    s = metrics.note_scores(fixture.truth(), est)
    assert s["onset_f1"] >= 0.9 and s["note_f1"] >= 0.9, s
    assert take.read_manifest()["layers"]["notes"]["tool"] == "segment"


def line_from(midi, confidence=None):
    n = len(midi)
    midi = np.asarray(midi, dtype=float)
    return {"time": np.arange(n) * 0.01, "midi": midi, "f0_hz": 440 * 2 ** ((midi - 69) / 12),
            "confidence": np.full(n, 0.95) if confidence is None else np.asarray(confidence, dtype=float),
            "voiced": np.isfinite(midi)}


def test_slur_without_an_attack_is_two_notes():
    midi = [70.0] * 30 + [70.5, 71.0, 71.5] + [72.0] * 30  # a slurred step up, no new attack
    conf = [0.95] * 30 + [0.4, 0.3, 0.4] + [0.95] * 30
    found = segment.segment(line_from(midi, conf), np.ones(63), np.zeros(63))
    assert [n["pitch"] for n in found] == [70, 72]
    assert abs(found[1]["onset"] - 0.31) <= 0.02


def test_vibrato_is_one_note():
    t = np.arange(100) * 0.01
    midi = 70 + 0.3 * np.sin(2 * np.pi * 5.5 * t)  # +-30 cents
    found = segment.segment(line_from(midi, np.full(100, 0.9)), np.ones(100), np.zeros(100))
    assert [n["pitch"] for n in found] == [70]


def test_a_sharp_horn_keeps_its_note_names():
    midi = [70.4] * 30 + [72.4] * 30 + [69.4] * 30  # 40 cents sharp throughout
    conf = [0.95] * 29 + [0.3] + [0.95] * 29 + [0.3] + [0.95] * 30
    found = segment.segment(line_from(midi, conf), np.ones(90), np.zeros(90))
    assert [n["pitch"] for n in found] == [70, 72, 69]
    assert abs(segment.tuning_offset(np.array(midi)) - 0.4) < 0.01


def test_tongued_repeat_splits_at_the_level_dip():
    level = np.ones(60)
    level[28:32] = [0.6, 0.3, 0.3, 0.6]
    found = segment.segment(line_from([70.0] * 60), level, np.zeros(60))
    assert [n["pitch"] for n in found] == [70, 70]
