"""The vocal review mark (layers/vocals.py, rule V) and the Mega separator's plumbing (mega.py)."""
from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf

from saxscribe import mega
from saxscribe.layers import notes as notes_layer
from saxscribe.layers import vocals
from saxscribe.take import Take

RATE = vocals.CQT_RATE


def tone(midi: float, seconds: float, level: float = 0.3) -> np.ndarray:
    t = np.arange(int(seconds * RATE)) / RATE
    return level * np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t)


def hiss(seconds: float, seed: int) -> np.ndarray:
    return 1e-3 * np.random.default_rng(seed).standard_normal(int(seconds * RATE))


def write(path, y):
    sf.write(str(path), y.astype(np.float32), RATE)
    return path


def setup(tmp_path):
    """12 s: the sax plays A4 for 6 s; then a singer sings A4 louder than what leaks into the sax stem."""
    sax = np.concatenate([tone(69, 6), tone(69, 6, 0.05)]) + hiss(12, 1)
    voc = np.concatenate([np.zeros(6 * RATE), tone(69, 6)]) + hiss(12, 2)
    notes = [{"onset": float(t), "offset": float(t) + 0.8, "pitch": 69, "tags": []} for t in range(12)]
    return write(tmp_path / "stem.wav", sax), write(tmp_path / "mega_vocal.wav", voc), notes


def test_notes_under_a_louder_singer_are_marked_and_kept(tmp_path):
    sax, voc, notes = setup(tmp_path)
    out = vocals.mark(notes, sax, voc)
    marked = [n["onset"] for n in notes if vocals.MAYBE_VOCALS in n["tags"]]
    assert out["marked"] == len(marked) >= 5
    assert all(t >= 6 for t in marked)  # never the sax's own notes
    assert all(vocals.MAYBE_NOT_SAX in n["tags"] for n in notes if vocals.MAYBE_VOCALS in n["tags"])
    assert len(notes) == 12 and not any("not_sax" in n["tags"] for n in notes)  # marked, never hidden


def test_a_singer_on_another_pitch_does_not_mark(tmp_path):
    """The sax plays D4 the whole time; the singer's A4 says nothing about the sax's notes."""
    sax = write(tmp_path / "stem.wav", tone(62, 12) + hiss(12, 1))
    voc = write(tmp_path / "voc.wav", np.concatenate([np.zeros(6 * RATE), tone(69, 6)]) + hiss(12, 2))
    notes = [{"onset": float(t), "offset": float(t) + 0.8, "pitch": 62, "tags": []} for t in range(12)]
    assert vocals.mark(notes, sax, voc)["marked"] == 0


def test_notes_already_left_off_the_score_are_not_marked():
    c = np.ones((84, 200))
    sax, voc = (c * 0.1, np.full(84, 0.1)), (c * 10, np.full(84, 1.0))
    notes = [{"onset": 0.5, "offset": 1.0, "pitch": 69, "tags": ["not_sax"]},
             {"onset": 0.5, "offset": 1.0, "pitch": 69, "tags": []},
             {"onset": 0.5, "offset": 1.0, "pitch": 200, "tags": []}]  # off the CQT: no evidence
    assert vocals.mark_with(notes, sax, voc)["marked"] == 1
    assert notes[1]["tags"] == [vocals.MAYBE_VOCALS, vocals.MAYBE_NOT_SAX]


def test_mega_config_allows_tuples_but_no_python_objects(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text("model:\n  freqs_per_bands: !!python/tuple\n  - 2\n  - 4\n")
    assert mega.load_config(good)["model"]["freqs_per_bands"] == (2, 4)
    bad = tmp_path / "bad.yaml"
    bad.write_text("x: !!python/object/apply:os.system ['true']\n")
    with pytest.raises(Exception):
        mega.load_config(bad)


class Echo:
    """Stands in for Mega: every stem asked for is the input itself."""
    def __call__(self, x, active_stem_ids):
        return x[:, None].repeat(1, len(active_stem_ids), 1, 1)


@pytest.mark.parametrize("length", [500, 2_345, 10_001])
def test_demix_overlap_add_gives_back_the_input(length):
    mix = np.random.default_rng(0).standard_normal((2, length)).astype(np.float32)
    out = mega.demix(Echo(), mix, [0, 1], chunk=1000, overlap=2)
    assert out.shape == (2, 2, length)
    assert np.allclose(out[0], mix, atol=1e-5) and np.allclose(out[1], mix, atol=1e-5)


def band_take(tmp_path, separator: str) -> Take:
    take = Take(tmp_path / "take")
    take.folder.mkdir()
    take.manifest.write_text(json.dumps({"mix": True, "layers": {"isolate": {"separator": separator}}}))
    return take


def test_vocal_check_runs_only_on_the_filosax_stem(tmp_path):
    out = notes_layer.vocal_marks(band_take(tmp_path, "demucs"), [])
    assert out["marked"] == 0 and "Filosax" in out["why"]


def test_vocal_check_is_skipped_without_mega(tmp_path, monkeypatch):
    monkeypatch.setenv("SAXSCRIBE_MODELS", str(tmp_path / "no-models"))
    out = notes_layer.vocal_marks(band_take(tmp_path, "filosax"), [])
    assert out == {"marked": 0, "why": "Mega not installed"}


def test_vocal_check_uses_a_vocal_stem_already_made(tmp_path, monkeypatch):
    take = band_take(tmp_path, "filosax")
    sax, voc, notes = setup(tmp_path)
    take.stems.mkdir()
    sax.rename(take.stem)
    voc.rename(take.stems / "mega_vocal.wav")
    monkeypatch.setattr(mega, "separate", lambda *a, **k: pytest.fail("separated again"))
    out = notes_layer.vocal_marks(take, notes)
    assert out["marked"] >= 5 and out["vocal_stem"] == "mega_vocal.wav"
