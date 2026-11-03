"""Layer 1 on a full mix: which Demucs stem holds the sax.

Demucs' six stems have no sax. On Parker records the alto landed in "guitar"
(7XTyc), in "other" (3RfYc), or about half in each (BRfYc). These stand-in
stems check that the lead score finds a horn line and passes over chords."""
from __future__ import annotations

import numpy as np
import soundfile as sf

from saxscribe.layers import isolate
from saxscribe.take import Take

from . import fixture

RATE = 44100
SECONDS = 6.0
T = np.arange(int(RATE * SECONDS)) / RATE


def horn_line(level=0.3, seed=0):
    """A sax-like line: one pitch at a time, rich in harmonics, a new note every 0.25 s."""
    rng = np.random.default_rng(seed)
    midi = np.repeat(rng.integers(56, 80, size=int(SECONDS * 4) + 1), RATE // 4)[: len(T)]
    phase = 2 * np.pi * np.cumsum(fixture.hz(midi)) / RATE
    return level * sum(np.sin(k * phase) / k for k in range(1, 7))


def chords(level=0.3):
    """Piano-like comping: three or four notes at once, changing every beat."""
    out = np.zeros_like(T)
    for i, start in enumerate(np.arange(0, SECONDS, 0.5)):
        span = (T >= start) & (T < start + 0.45)
        for m in ([48, 55, 64, 70], [50, 57, 65, 72], [53, 60, 69])[i % 3]:
            out[span] += np.sin(2 * np.pi * fixture.hz(m) * T[span]) * np.exp(-3 * (T[span] - start))
    return level * out / 3


def noise(level=0.2, seed=1):
    return level * np.random.default_rng(seed).standard_normal(len(T)) * (np.sin(2 * np.pi * 2 * T) > 0.6)


def make_take(tmp_path, stems: dict[str, np.ndarray]) -> tuple[Take, object]:
    take = Take(tmp_path / "take")
    take.stems.mkdir(parents=True)
    full = sum(stems.values())
    for name, y in stems.items():
        sf.write(str(take.stems / f"{name}.wav"), y, RATE)
    src = tmp_path / "mix.wav"
    sf.write(str(src), np.clip(full, -1, 1), RATE)
    return take, src


def test_the_horn_is_found_in_whichever_stem_it_landed_in(tmp_path):
    take, src = make_take(tmp_path, {"guitar": horn_line(), "other": 0.05 * noise(), "piano": chords(),
                                     "drums": noise(), "bass": 0.2 * np.sin(2 * np.pi * 55 * T),
                                     "vocals": 0.01 * noise(seed=2)})
    isolate.run(take, src, mix=True, stem=None)
    rec = take.read_manifest()["layers"]["isolate"]
    assert rec["stem"] == "guitar"
    assert rec["lead_share"]["guitar"] > 0.8
    assert rec["lead_share"]["piano"] < 0.2  # chords score low though as loud


def test_a_horn_split_between_two_stems_is_added_back_together(tmp_path):
    line = horn_line()
    take, src = make_take(tmp_path, {"other": 0.55 * line, "guitar": 0.45 * line, "piano": 0.3 * chords(),
                                     "drums": noise(), "bass": 0.2 * np.sin(2 * np.pi * 55 * T),
                                     "vocals": 0.01 * noise(seed=2)})
    isolate.run(take, src, mix=True, stem=None)
    assert take.read_manifest()["layers"]["isolate"]["stem"] == "other+guitar"
    y, _ = sf.read(str(take.stem))
    assert np.corrcoef(y[: len(line)], line)[0, 1] > 0.99


def test_a_named_stem_or_sum_is_used_as_asked(tmp_path):
    take, src = make_take(tmp_path, {"other": horn_line(), "guitar": chords(), "drums": noise()})
    isolate.run(take, src, mix=True, stem="guitar")
    assert take.read_manifest()["layers"]["isolate"]["stem"] == "guitar"
    isolate.run(take, src, mix=True, stem="other+guitar")
    assert take.read_manifest()["layers"]["isolate"]["stem"] == "other+guitar"


def test_choose_rules():
    assert isolate.choose({"other": 9.0, "guitar": 1.0}) == ["other"]
    assert isolate.choose({"other": 4.0, "guitar": 5.0, "piano": 1.0}) == ["guitar", "other"]
    assert isolate.choose({}) == []


def test_loud_comping_does_not_beat_a_quieter_horn(tmp_path):
    take, src = make_take(tmp_path, {"other": 0.5 * horn_line(), "piano": 3 * chords(), "guitar": 2 * chords(),
                                     "drums": noise()})
    isolate.run(take, src, mix=True, stem=None)
    assert take.read_manifest()["layers"]["isolate"]["stem"] == "other"
