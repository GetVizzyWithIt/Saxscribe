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
