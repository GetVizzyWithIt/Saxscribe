"""Band-record bleed: notes the sax's pitch line does not back up are tagged, never removed."""
from __future__ import annotations

import numpy as np

from saxscribe.layers import bleed


def line(segments, total=20.0):
    """A pitch line: [(start, end, midi)] voiced, silent elsewhere, every 10 ms."""
    t = np.arange(0, total, 0.01)
    midi = np.full(len(t), np.nan)
    for a, b, m in segments:
        midi[(t >= a) & (t < b)] = m
    return {"time": t, "midi": midi, "voiced": np.isfinite(midi), "f0_hz": midi, "confidence": np.isfinite(midi) * 0.9}


def note(onset, offset, pitch, tags=None):
    return {"onset": onset, "offset": offset, "pitch": pitch, "tags": list(tags or [])}


def test_notes_where_the_pitch_line_is_silent_for_long_are_another_instrument():
    ln = line([(0, 2, 60), (12, 14, 62)])          # sax out from 2 s to 12 s
    piano, sax = note(5.0, 5.5, 64), note(12.2, 12.8, 62)
    counts = bleed.tag([piano, sax], ln)
    assert piano["tags"] == ["no_pitch_line", "not_sax"] and sax["tags"] == []
    assert counts["no_pitch_line"] == 1 and counts["silent_spans"] == [[2.0, 12.0]]


def test_a_note_under_a_held_sax_note_at_another_pitch_is_bleed():
    ln = line([(0, 4, 67)])                         # sax holds G4
    under, octave, held = note(1.0, 1.6, 62), note(2.0, 2.5, 55), note(0.0, 4.0, 67)
    bleed.tag([under, octave, held], ln)
    assert under["tags"] == ["off_line", "not_sax"]
    assert octave["tags"] == [] and held["tags"] == []   # an octave off is the sax's octave, not bleed


def test_short_silences_and_already_cut_notes_are_left_alone():
    ln = line([(0, 3, 60), (5, 8, 60)])             # a 2 s rest is just a rest
    rest, cut = note(3.5, 4.0, 60), note(1.0, 1.5, 40, tags=["not_sax"])
    bleed.tag([rest, cut], ln)
    assert rest["tags"] == [] and cut["tags"] == ["not_sax"]
