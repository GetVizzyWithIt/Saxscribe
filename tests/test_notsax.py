"""The review mark for notes that may be another instrument (layers/notsax.py)."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from saxscribe.layers import notsax

RATE = notsax.RATE


def tone(midi: float, seconds: float, level: float = 0.3) -> np.ndarray:
    t = np.arange(int(seconds * RATE)) / RATE
    return level * np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t)


def write(path, y):
    sf.write(str(path), y.astype(np.float32), RATE)
    return path


def setup(tmp_path):
    """20 s: sax plays A4 for 10 s, then the sax stops and a piano plays C5 for 10 s."""
    sax = np.concatenate([tone(69, 10), np.zeros(10 * RATE)])
    piano = np.concatenate([np.zeros(10 * RATE), tone(72, 10)])
    paths = {"mix": write(tmp_path / "mix.wav", sax + piano), "sax": write(tmp_path / "other.wav", sax),
             "piano": write(tmp_path / "piano.wav", piano)}
    notes = [{"onset": float(t), "offset": float(t) + 0.8, "pitch": 69, "tags": []} for t in range(0, 10, 1)]
    notes += [{"onset": float(t), "offset": float(t) + 0.8, "pitch": 72, "tags": []} for t in range(10, 20, 1)]
    return paths, notes


def test_a_piano_solo_with_the_sax_stem_silent_is_marked_and_kept(tmp_path):
    paths, notes = setup(tmp_path)
    out = notsax.mark(notes, paths["mix"], paths["sax"], {"piano": paths["piano"]}, "filosax")
    marked = [n["onset"] for n in notes if notsax.MAYBE_NOT_SAX in n["tags"]]
    assert out["marked"] == len(marked) >= 8
    assert all(t >= 10 for t in marked)          # never on the sax's own notes
    assert len(notes) == 20 and not any("not_sax" in n["tags"] for n in notes)  # marked, never hidden


def test_a_rival_on_another_pitch_does_not_mark(tmp_path):
    paths, notes = setup(tmp_path)
    for n in notes[10:]:
        n["pitch"] = 60  # the piano plays C5, these notes say C4: no pitch evidence
    notsax.mark(notes, paths["mix"], paths["sax"], {"piano": paths["piano"]}, "filosax")
    assert not any(notsax.MAYBE_NOT_SAX in n["tags"] for n in notes)


def test_a_short_dropout_does_not_mark(tmp_path):
    sax = np.concatenate([tone(69, 10), np.zeros(2 * RATE), tone(69, 8)])
    piano = np.concatenate([np.zeros(10 * RATE), tone(72, 2), np.zeros(8 * RATE)])
    mix = write(tmp_path / "mix.wav", sax + piano)
    notes = [{"onset": 10.5, "offset": 11.3, "pitch": 72, "tags": []}]
    notsax.mark(notes, mix, write(tmp_path / "other.wav", sax), {"piano": write(tmp_path / "p.wav", piano)}, "filosax")
    assert notes[0]["tags"] == []  # 2 s is shorter than RUN
