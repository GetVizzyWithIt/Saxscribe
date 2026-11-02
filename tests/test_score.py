"""The scorecard: answer-key loading, metrics, the scorecard run, and etude alignment."""
from __future__ import annotations

import json

import mido
import numpy as np
import soundfile as sf

from saxscribe.score import align, card, metrics, refs

from . import fixture


def test_midi_round_trip(tmp_path):
    notes = [{"onset": 0.5, "offset": 1.0, "pitch": 65}, {"onset": 1.0, "offset": 1.75, "pitch": 67}]
    refs.write_midi_notes(tmp_path / "a.mid", notes)
    back = refs.read_midi_notes(tmp_path / "a.mid")
    assert [(round(n["onset"], 3), round(n["offset"], 3), n["pitch"]) for n in back] == \
        [(0.5, 1.0, 65), (1.0, 1.75, 67)]


def test_midi_reader_takes_the_busiest_track_and_follows_tempo_changes(tmp_path):
    mid = mido.MidiFile(ticks_per_beat=480)
    tempo = mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=500000, time=0),
                            mido.MetaMessage("set_tempo", tempo=1000000, time=960)])  # 120 -> 60 BPM at beat 2
    sax = mido.MidiTrack()
    for _ in range(4):  # quarter notes from beat 0
        sax += [mido.Message("note_on", note=70, velocity=90, time=0),
                mido.Message("note_off", note=70, velocity=0, time=480)]
    other = mido.MidiTrack([mido.Message("note_on", note=40, velocity=90, time=0),
                            mido.Message("note_off", note=40, velocity=0, time=1920)])
    mid.tracks += [tempo, sax, other]
    mid.save(str(tmp_path / "t.mid"))
    notes = refs.read_midi_notes(tmp_path / "t.mid")
    assert [n["pitch"] for n in notes] == [70] * 4
    assert [round(n["onset"], 3) for n in notes] == [0.0, 0.5, 1.0, 2.0]


def test_pairs_match_by_name(tmp_path):
    (tmp_path / "audio").mkdir()
    (tmp_path / "midi").mkdir()
    (tmp_path / "solo").mkdir()
    for p in ("audio/Confirmation_sax_stem.wav", "midi/Confirmation_aligned.mid",
              "audio/Donna Lee.wav", "audio/Donna Lee.mid",
              "solo/take3.flac", "solo/answer.mid"):
        (tmp_path / p).write_bytes(b"")
    pairs = {(a.name, m.name) for a, m in refs.find_pairs(tmp_path)}
    assert pairs == {("Confirmation_sax_stem.wav", "Confirmation_aligned.mid"),
                     ("Donna Lee.wav", "Donna Lee.mid"), ("take3.flac", "answer.mid")}


def test_split_is_by_tune():
    a = refs.Reference("x1", None, [], tune="confirmation", player="1")
    b = refs.Reference("x2", None, [], tune="confirmation", player="2")
    assert refs.split_of(a) == refs.split_of(b)
    tunes = [refs.split_of(refs.Reference(str(i), None, [], tune=f"tune{i}")) for i in range(200)]
    assert 0.1 < tunes.count("test") / len(tunes) < 0.3


def test_perfect_notes_score_perfectly():
    notes = fixture.truth()
    s = metrics.note_scores(notes, notes)
    assert s["onset_f1"] == 1.0 and s["note_f1"] == 1.0


def test_scorecard_on_a_pairs_folder(fixture_wav, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    sf.write(str(data / "phrase.wav"), sf.read(str(fixture_wav))[0], fixture.RATE)
    refs.write_midi_notes(data / "phrase.mid", fixture.truth())
    result = card.run("pairs", data=str(data), runs=str(tmp_path / "runs"),
                      contour_tool="pyin", notes_tool="contour")
    assert result["items"] == 1
    assert result["mean"]["onset_f1"] >= 0.8
    assert result["mean"]["pitch_accuracy"] >= 0.85
    out = tmp_path / "runs" / "pairs" / "contour-pyin-notes-contour"
    assert (out / "scorecard.md").read_text().startswith("# Scorecard: pairs")
    assert json.loads((out / "scorecard.json").read_text())["rows"][0]["id"] == "phrase"


def written_score(path):
    """The fixture phrase as an alto part, written in E-flat, starting on beat 1 of bar 1."""
    from music21 import meter, note, stream
    part = stream.Part()
    part.insert(0, meter.TimeSignature("4/4"))
    for b, length, pitch, _ in fixture.PHRASE:
        part.insert(b, note.Note(pitch + 9, quarterLength=length))
    part.makeRests(fillGaps=True, inPlace=True)
    part.makeNotation().write("musicxml", fp=str(path))


def test_answer_key_lines_a_written_etude_up_with_the_take(fixture_wav, tmp_path):
    written_score(tmp_path / "etude.musicxml")
    notes = align.align(fixture_wav, tmp_path / "etude.musicxml", "alto", written=True)
    truth = fixture.truth()
    assert [n["pitch"] for n in notes] == [n["pitch"] for n in truth]
    errors = np.abs([a["onset"] - b["onset"] for a, b in zip(notes, truth)])
    assert np.mean(errors <= 0.05) >= 0.85, errors


def test_omnibook_layout(tmp_path):
    root = tmp_path / "CharlieParkerOmnibook" / "CharlieParkerAlignedOmnibookPublication"
    for sub in ("audio_stems", "audio_untuned_mixes", "midi_original", "midi_performance_aligned"):
        (root / sub).mkdir(parents=True)
    (tmp_path / "CharlieParkerOmnibook" / "__MACOSX").mkdir()
    notes = [{"onset": 1.0, "offset": 1.5, "pitch": 70}]
    for rid in ("1p64c", "2RfYc", "3zn4c"):
        (root / "audio_stems" / f"{rid}.wav").write_bytes(b"")
        (root / "audio_untuned_mixes" / f"{rid}.mp3").write_bytes(b"")
        refs.write_midi_notes(root / "midi_original" / f"{rid}.mid", notes)
    for rid in ("1p64c", "2RfYc"):  # 3zn4c has no aligned MIDI
        refs.write_midi_notes(root / "midi_performance_aligned" / f"{rid}-fine-aligned.mid", notes)
    stems = refs.load_omnibook(tmp_path / "CharlieParkerOmnibook")
    assert [(r.id, r.audio.name, r.is_mix) for r in stems] == [("1p64c", "1p64c.wav", False),
                                                               ("2RfYc", "2RfYc.wav", False)]
    assert stems[0].extra["midi"].endswith("1p64c-fine-aligned.mid")
    mixes = refs.load_omnibook(tmp_path / "CharlieParkerOmnibook", mix=True)
    assert [(r.audio.name, r.is_mix) for r in mixes] == [("1p64c.mp3", True), ("2RfYc.mp3", True)]


def test_urmp_layout(tmp_path):
    piece = tmp_path / "URMP" / "Dataset" / "06_Entertainer_sax_sax"
    piece.mkdir(parents=True)
    other = tmp_path / "URMP" / "Dataset" / "01_Jupiter_vn_vc"
    other.mkdir()
    (other / "Notes_1_vn_01_Jupiter.txt").write_text("0.5\t440.0\t0.5\n")
    (piece / "AuMix_06_Entertainer_sax_sax.wav").write_bytes(b"")
    for n in (1, 2):
        (piece / f"AuSep_{n}_sax_06_Entertainer.wav").write_bytes(b"")
        (piece / f"F0s_{n}_sax_06_Entertainer.txt").write_text("0.0 0\n")
    (piece / "Notes_1_sax_06_Entertainer.txt").write_text(
        "onset\tfreq\tdur\n0.500\t293.66\t0.250\n0.750\t311.13\t0.500\n")
    (piece / "Notes_2_sax_06_Entertainer.txt").write_text("1.0 440.0 1.0\n")
    stems = refs.load_urmp(tmp_path / "URMP")
    assert [(r.id, r.audio.name, r.is_mix, r.tune) for r in stems] == [
        ("06_Entertainer_sax_sax__1", "AuSep_1_sax_06_Entertainer.wav", False, "Entertainer"),
        ("06_Entertainer_sax_sax__2", "AuSep_2_sax_06_Entertainer.wav", False, "Entertainer")]
    assert [(n["onset"], n["offset"], n["pitch"]) for n in stems[0].notes] == [(0.5, 0.75, 62), (0.75, 1.25, 63)]
    assert stems[1].notes[0]["pitch"] == 69
    mixes = refs.load_urmp(tmp_path / "URMP", mix=True)
    assert {r.audio.name for r in mixes} == {"AuMix_06_Entertainer_sax_sax.wav"} and all(r.is_mix for r in mixes)


def test_choralebricks_layout(tmp_path):
    song = tmp_path / "ChoraleBricks" / "01_AudioAndAnnotations" / "Bach_IchStehAnDeinerKrippe"
    (song / "tracks").mkdir(parents=True)
    (song / "annotations").mkdir()
    header = "start_sec;end_sec;dur_sec;pitch;pitch_name;pitch_written;pitch_written_name;pitch_dev_cents;midi_velocity\n"
    for tag, rows in (("01_as", "0.267;0.789;0.522;67;G4;67;G4;25;100\n0.819;1.678;0.859;67;G4;67;G4;22;100\n"),
                      ("04_bs", "1.0;2.0;1.0;43;G2;55;G3;0;100\n"),
                      ("01_tp", "0.5;1.0;0.5;72;C5;72;C5;0;100\n")):
        (song / "tracks" / f"{tag}.wav").write_bytes(b"")
        (song / "annotations" / f"{tag}_notes.csv").write_text(header + rows)
    (song / "annotations" / "01_as_f0_filled.csv").write_text("t;f0\n0.0;0.0\n")
    items = refs.load_choralebricks(tmp_path / "ChoraleBricks")
    assert [(r.id, r.extra["horn"]) for r in items] == [("Bach_IchStehAnDeinerKrippe__01_as", "alto"),
                                                        ("Bach_IchStehAnDeinerKrippe__04_bs", "baritone")]
    assert [(n["onset"], n["offset"], n["pitch"]) for n in items[0].notes] == [(0.267, 0.789, 67), (0.819, 1.678, 67)]
    assert items[1].notes[0]["pitch"] == 43  # sounding pitch, not the written one
    assert items[0].extra["f0"].endswith("01_as_f0_filled.csv") and items[1].extra["f0"] is None


def test_bach10_layout(tmp_path):
    from scipy.io import savemat
    piece = tmp_path / "Bach10" / "Bach10_v1.1" / "01-AchGottundHerr"
    piece.mkdir(parents=True)
    for name in ("01-AchGottundHerr.wav", "01-AchGottundHerr-saxphone.wav"):
        (piece / name).write_bytes(b"")
    parts = np.empty((4, 1), dtype=object)
    for i in range(4):
        notes = np.empty((2, 1), dtype=object)
        notes[0, 0] = np.array([[1, 2, 3], [60 + i, 60.2 + i, 59.9 + i]])   # frames 1-3
        notes[1, 0] = np.array([[11, 12], [62 + i, 62 + i]])               # frames 11-12
        parts[i, 0] = notes
    savemat(str(piece / "01-AchGottundHerr-GTNotes.mat"), {"GTNotes": parts})
    stems = refs.load_bach10(tmp_path / "Bach10")
    assert [(r.id, r.audio.name, r.is_mix) for r in stems] == [("01-AchGottundHerr", "01-AchGottundHerr-saxphone.wav", False)]
    assert [(n["onset"], n["offset"], n["pitch"]) for n in stems[0].notes] == [(0.023, 0.053, 62), (0.123, 0.143, 64)]
    mixes = refs.load_bach10(tmp_path / "Bach10", mix=True)
    assert mixes[0].audio.name == "01-AchGottundHerr.wav" and mixes[0].is_mix


def test_partial_keys_score_only_inside_their_span():
    from types import SimpleNamespace
    key = [{"onset": 10.0, "offset": 10.5, "pitch": 70}, {"onset": 11.0, "offset": 11.5, "pitch": 72}]
    found = key + [{"onset": 40.0, "offset": 40.5, "pitch": 65}]  # playing the key leaves out
    span = metrics.span_of(key)
    assert metrics.inside(found, span) == key
    assert metrics.note_scores(key, metrics.inside(found, span))["note_f1"] == 1.0
    assert metrics.note_scores(key, found)["note_f1"] < 1.0
    assert refs.Reference("x", None, key, partial=True).partial


def test_omnibook_keys_are_partial_and_skip_excluded(tmp_path):
    root = tmp_path / "CharlieParkerOmnibook" / "Pub"
    for sub in ("audio_stems", "midi_performance_aligned"):
        (root / sub).mkdir(parents=True)
    notes = [{"onset": 1.0, "offset": 1.5, "pitch": 70}]
    for rid in ("lTXyc", "2RfYc"):
        (root / "audio_stems" / f"{rid}.wav").write_bytes(b"")
        refs.write_midi_notes(root / "midi_performance_aligned" / f"{rid}-fine-aligned.mid", notes)
    loaded = refs.load_omnibook(tmp_path / "CharlieParkerOmnibook")
    assert [(r.id, r.partial) for r in loaded] == [("2RfYc", True)]


def test_a_key_an_octave_off_shows_as_octave_errors_and_is_flagged():
    """Omnibook BRfYc and 7RfYc: passages of the key sit an octave above the sax."""
    key = [{"onset": 0.5 * i, "offset": 0.5 * i + 0.45, "pitch": 60 + i % 5} for i in range(20)]
    t = np.arange(0, 10.5, 0.01)
    f0 = np.zeros_like(t)
    for i, n in enumerate(key):
        sounding = (t >= n["onset"]) & (t < n["offset"])
        f0[sounding] = metrics.hz(n["pitch"] - (12 if i < 10 else 0))  # first half of the key an octave high
    s = metrics.pitch_scores(key, {"time": t, "f0_hz": f0, "voiced": f0 > 0})
    assert 0.45 < s["pitch_accuracy"] < 0.55
    assert s["chroma_accuracy"] > 0.95
    assert 0.4 < s["octave_errors"] < 0.55
    from saxscribe.score import card
    md = card.markdown({"set": "omnibook", "split": "all", "settings": "default", "items": 1, "made": "now",
                        "partial": True, "mean": {"pitch_accuracy": s["pitch_accuracy"]},
                        "rows": [{"id": "BRfYc", **s, "est_notes": 20, "ref_notes": 20}]}, True)
    assert "(check)" in md and "Octave check: BRfYc" in md
