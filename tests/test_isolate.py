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


def long_horn(seconds, rate, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(rate * seconds)) / rate
    midi = np.repeat(rng.integers(56, 80, size=int(seconds * 4) + 1), rate // 4)[: len(t)]
    phase = 2 * np.pi * np.cumsum(fixture.hz(midi)) / rate
    return 0.3 * sum(np.sin(k * phase) / k for k in range(1, 7))


def long_chords(seconds, rate):
    t = np.arange(int(rate * seconds)) / rate
    out = np.zeros_like(t)
    for i, start in enumerate(np.arange(0, seconds, 0.5)):
        span = (t >= start) & (t < start + 0.45)
        for m in ([48, 55, 64, 70], [50, 57, 65, 72], [53, 60, 69])[i % 3]:
            out[span] += np.sin(2 * np.pi * fixture.hz(m) * t[span]) * np.exp(-3 * (t[span] - start))
    return 0.3 * out / 3


def test_a_piano_solo_in_the_middle_is_cut_and_the_horn_kept(tmp_path):
    rate, seconds = 16000, 60
    t = np.arange(rate * seconds) / rate
    horn = long_horn(seconds, rate) * ((t < 20) | (t >= 40))
    piano = long_chords(seconds, rate) * (1 + 3 * ((t >= 20) & (t < 40)))
    stem = horn + 0.02 * piano          # Demucs leaves a little piano in the sax stem
    sf.write(str(tmp_path / "stem.wav"), stem, rate)
    sf.write(str(tmp_path / "mix.wav"), np.clip(horn + piano, -1, 1), rate)
    keep, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert len(cuts) == 1
    a, b = cuts[0]
    assert 20 <= a <= 25 and 35 <= b <= 40          # inside the piano solo, never into the horn
    assert keep[0][0] == 0 and keep[-1][1] >= 59


def test_a_short_rest_is_not_cut(tmp_path):
    rate, seconds = 16000, 40
    t = np.arange(rate * seconds) / rate
    horn = long_horn(seconds, rate) * ((t < 18) | (t >= 23))   # 5 s rest
    piano = long_chords(seconds, rate)
    sf.write(str(tmp_path / "stem.wav"), horn + 0.02 * piano, rate)
    sf.write(str(tmp_path / "mix.wav"), np.clip(horn + piano, -1, 1), rate)
    keep, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert cuts == []


def test_no_cut_where_the_horn_moved_into_another_stem(tmp_path):
    # Demucs moved Getz into "guitar" for a few seconds of Blues for Mary Jane;
    # the sax stem goes quiet there, but the horn is still playing.
    rate, seconds = 16000, 50
    t = np.arange(rate * seconds) / rate
    horn = long_horn(seconds, rate)
    moved = (t >= 20) & (t < 32)
    piano = long_chords(seconds, rate)
    stem, guitar = horn * ~moved + 0.02 * piano, horn * moved
    for name, y in (("stem", stem), ("guitar", guitar), ("mix", np.clip(horn + piano, -1, 1))):
        sf.write(str(tmp_path / f"{name}.wav"), y, rate)
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert cuts                                       # the sax stem alone would lose him
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", [tmp_path / "guitar.wav"])
    assert cuts == []


def test_a_sax_mixed_low_all_through_is_not_cut(tmp_path):
    # Walker's Theme: the sax sits about 8 dB under the band for the whole
    # record, so a fixed -6 dB bar called the whole track "sax rests".
    rate, seconds = 16000, 40
    horn = long_horn(seconds, rate)
    band = 8 * long_chords(seconds, rate)           # the sax stem holds about -8 dB of the mix
    stem, mix = horn + 0.02 * band, horn + band
    peak = np.abs(mix).max()
    sf.write(str(tmp_path / "stem.wav"), stem / peak, rate)
    sf.write(str(tmp_path / "mix.wav"), mix / peak, rate)
    keep, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert cuts == []


def test_the_share_bar_follows_the_take_but_never_drops_too_far():
    assert isolate.share_bar(np.full(50, -1.0)) == isolate.SPAN_SHARE_DB      # a loud sax: the usual bar
    assert isolate.share_bar(np.full(50, -8.0)) == -11.0                      # mixed low: 3 dB under its loud windows
    assert isolate.share_bar(np.full(50, -30.0)) == isolate.SPAN_SHARE_FLOOR  # never below the floor


def test_a_record_is_never_cut_almost_whole(tmp_path):
    # If the check finds "no sax" over nearly the whole record, the check failed:
    # keep everything rather than hide every note.
    rate, seconds = 16000, 40
    horn = long_horn(seconds, rate)
    band = 40 * long_chords(seconds, rate)          # far below even the lowest bar
    stem, mix = horn + 0.02 * band, horn + band
    peak = np.abs(mix).max()
    sf.write(str(tmp_path / "stem.wav"), stem / peak, rate)
    sf.write(str(tmp_path / "mix.wav"), mix / peak, rate)
    keep, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert cuts == [] and keep[0][0] == 0


def drums_and_bass(seconds, rate, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(int(rate * seconds)) / rate
    hits = np.zeros_like(t)
    for start in np.arange(0, seconds, 0.25):
        k = (t >= start) & (t < start + 0.08)
        hits[k] = rng.standard_normal(k.sum()) * np.exp(-40 * (t[k] - start))
    bass = np.sin(2 * np.pi * 55 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t))
    return hits, bass


def test_loud_drums_and_bass_under_a_sax_trio_dont_cut_the_sax(tmp_path):
    # Potter, Item 1: no piano; once the band digs in, bass and drums sit
    # 3-7 dB over the sax, and the sax looked like it had stopped.
    rate, seconds = 16000, 50
    t = np.arange(rate * seconds) / rate
    horn = long_horn(seconds, rate)
    drums, bass = drums_and_bass(seconds, rate)
    loud = 0.3 + 2.7 * (t >= 15)
    drums, bass = loud * drums, 0.6 * loud * bass
    mix = horn + drums + bass
    peak = np.abs(mix).max()
    for name, y in (("stem", horn), ("drums", drums), ("bass", bass), ("mix", mix)):
        sf.write(str(tmp_path / f"{name}.wav"), y / peak, rate)
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    assert cuts                                       # judged against the whole mix, the sax looks gone
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", [],
                                [tmp_path / "drums.wav", tmp_path / "bass.wav"])
    assert cuts == []


def test_a_piano_solo_over_drums_and_bass_is_still_cut(tmp_path):
    # Demucs spreads a piano solo over "piano", "guitar" and "other". Summed,
    # those stems pass as a split sax once drums and bass are left out; the
    # piano stem holding a fair part of the whole mix, while no stem passes
    # the old whole-mix test, settles it.
    rate, seconds = 16000, 60
    t = np.arange(rate * seconds) / rate
    solo = (t >= 20) & (t < 40)
    horn = long_horn(seconds, rate) * ~solo
    piano = long_horn(seconds, rate, seed=5) * solo + 0.2 * long_chords(seconds, rate)
    drums, bass = drums_and_bass(seconds, rate)
    drums = 0.2 * drums
    mix = horn + piano + drums + 0.5 * bass
    peak = np.abs(mix).max()
    stems = {"stem": horn + 0.05 * piano, "guitar": 0.25 * piano, "other": 0.25 * piano,
             "piano": 0.6 * piano, "drums": drums, "bass": 0.5 * bass, "mix": mix}
    for name, y in stems.items():
        sf.write(str(tmp_path / f"{name}.wav"), y / peak, rate)
    others = [tmp_path / "guitar.wav", tmp_path / "other.wav"]
    rhythm = [tmp_path / "drums.wav", tmp_path / "bass.wav"]
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", others, rhythm)
    assert cuts == []                                  # the summed piano passes as sax
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", others, rhythm, [tmp_path / "piano.wav"])
    assert len(cuts) == 1 and 20 <= cuts[0][0] <= 25 and 35 <= cuts[0][1] <= 40


def test_a_sax_split_across_two_stems_is_found_in_their_sum(tmp_path):
    # Coltrane, Impressions: for a stretch the horn is shared between
    # "vocals" and "other", neither loud enough alone.
    rate, seconds = 16000, 50
    t = np.arange(rate * seconds) / rate
    horn = long_horn(seconds, rate)
    split = (t >= 15) & (t < 40)
    piano = long_chords(seconds, rate)
    mix = horn + piano
    peak = np.abs(mix).max()
    stem = horn * np.where(split, 0.5, 1.0) + 0.02 * piano
    vocals = horn * np.where(split, 0.5, 0.0)
    for name, y in (("stem", stem), ("vocals", vocals), ("mix", mix)):
        sf.write(str(tmp_path / f"{name}.wav"), y / peak, rate)
    _, alone = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav")
    _, summed = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", [tmp_path / "vocals.wav"])
    assert alone and summed == []


def test_a_bass_solo_is_cut_but_a_trios_loud_bass_is_not(tmp_path):
    # Blues for Mary Jane 341-368 s: a bass solo. With drums and bass left out
    # of the share, the sax stem's leftovers passed; the bass sitting far over
    # every sax stem marks the rest. Under the sax, a trio's bass stays closer.
    rate, seconds = 16000, 60
    t = np.arange(rate * seconds) / rate
    solo = (t >= 20) & (t < 40)
    horn = long_horn(seconds, rate) * ~solo
    bass_line = 0.6 * long_horn(seconds, rate, seed=7) * np.where(solo, 1.0, 0.5)
    drums, _ = drums_and_bass(seconds, rate)
    mix = horn + bass_line + 0.3 * drums
    peak = np.abs(mix).max()
    stems = {"stem": horn + 0.08 * bass_line * solo, "bass": bass_line, "drums": 0.3 * drums, "mix": mix}
    for name, y in stems.items():
        sf.write(str(tmp_path / f"{name}.wav"), y / peak, rate)
    rhythm = [tmp_path / "drums.wav", tmp_path / "bass.wav"]
    _, cuts = isolate.sax_spans(tmp_path / "stem.wav", tmp_path / "mix.wav", [], rhythm, [tmp_path / "bass.wav"])
    assert len(cuts) == 1 and 20 <= cuts[0][0] <= 25 and 35 <= cuts[0][1] <= 40
