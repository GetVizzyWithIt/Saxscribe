"""One test group per layer, on the 10-second synthetic phrase (see fixture.py).

The thresholds are loose on purpose: these check that each layer is wired up
and roughly right, not how good the models are. That is the scorecard's job.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import mir_eval
import mido
import numpy as np
import soundfile as sf

from saxscribe.layers import contour, notes
from saxscribe.pipeline import transcribe

from . import fixture


def note_arrays(ns):
    intervals = np.array([[n["onset"], n["offset"]] for n in ns])
    pitches = np.array([fixture.hz(n["pitch"]) for n in ns])
    return intervals, pitches


# ---------------------------------------------------------------- layer 1

def test_isolate_passes_a_solo_take_through(take, fixture_wav):
    y, rate = sf.read(str(take.stem))
    assert rate == 44100
    assert abs(len(y) / rate - fixture.SECONDS) < 0.05
    assert take.source.exists()
    assert not take.accompaniment.exists()
    assert take.read_manifest()["layers"]["isolate"]["tool"] == "passthrough"


# ---------------------------------------------------------------- layer 2

def test_contour_is_every_10_ms_with_confidence(take):
    line = contour.read(take.contour)
    assert np.allclose(np.diff(line["time"]), 0.01)
    assert abs(line["time"][-1] - fixture.SECONDS) < 0.05
    assert np.all((line["confidence"] >= 0) & (line["confidence"] <= 1))


def test_contour_pitch_is_within_50_cents(take):
    line = contour.read(take.contour)
    ref_t, ref_hz = [], []
    for n in fixture.truth():  # steady middles of the notes, skipping vibrato wobble
        t = np.arange(n["onset"] + 0.05, n["offset"] - 0.05, 0.01)
        ref_t += list(t)
        ref_hz += [fixture.hz(n["pitch"])] * len(t)
    ref_t, ref_hz = np.array(ref_t), np.array(ref_hz)
    est_hz = np.where(line["voiced"], np.nan_to_num(line["f0_hz"]), 0.0)
    scores = mir_eval.melody.evaluate(ref_t, ref_hz, line["time"], est_hz)
    assert scores["Raw Pitch Accuracy"] >= 0.9, scores


# ---------------------------------------------------------------- layer 3

def test_notes_find_the_phrase(take):
    data = notes.read(take)
    assert data["pitch"] == "concert" and data["horn"] == "alto"
    ref_i, ref_p = note_arrays(fixture.truth())
    est_i, est_p = note_arrays(data["notes"])
    onset_f1 = mir_eval.onset.f_measure(ref_i[:, 0], est_i[:, 0], window=0.05)[0]
    assert onset_f1 >= 0.8, onset_f1
    p, r, f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
        ref_i, ref_p, est_i, est_p, offset_ratio=None)
    assert f1 >= 0.7, (p, r, f1)


def test_notes_are_one_line_with_cents_and_tags(take):
    ns = notes.read(take)["notes"]
    for a, b in zip(ns, ns[1:]):
        assert a["offset"] <= b["onset"] + 1e-6
    for n in ns:
        assert n["tags"] == []
        assert n["cents"] is None or abs(n["cents"]) <= 60


def test_notes_have_beats(take):
    data = notes.read(take)
    assert len(data["beats"]) >= 4
    assert data["tempo_bpm"] is not None


def test_one_line_keeps_the_louder_double_and_cuts_overlaps():
    raw = [{"onset": 1.0, "offset": 1.6, "pitch": 60, "amp": 0.9},
           {"onset": 1.01, "offset": 1.5, "pitch": 72, "amp": 0.3},
           {"onset": 1.5, "offset": 2.0, "pitch": 62, "amp": 0.8}]
    out = notes.one_line(raw)
    assert [n["pitch"] for n in out] == [60, 62]
    assert out[0]["offset"] == 1.5


# ---------------------------------------------------------------- layer 4

def test_midi_matches_the_notes(take):
    ns = notes.read(take)["notes"]
    mid = mido.MidiFile(str(take.midi))
    ons, now = [], 0.0
    for msg in mid:
        now += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            ons.append((round(now, 3), msg.note))
    assert len(ons) == len(ns)
    assert all(abs(t - n["onset"]) < 0.002 and p == n["pitch"] for (t, p), n in zip(ons, ns))


# ---------------------------------------------------------------- re-running

def test_rerun_skips_layers_and_redo_keeps_lower_ones(fixture_wav, tmp_path):
    t = transcribe(fixture_wav, tmp_path, contour_tool="pyin", notes_tool="contour")
    data = json.loads(t.notes.read_text())
    data["notes"][0]["pitch"] += 1  # a hand fix
    t.notes.write_text(json.dumps(data))
    before = {p: p.stat().st_mtime_ns for p in (t.stem, t.contour, t.notes, t.midi)}

    transcribe(fixture_wav, tmp_path)  # everything is there: nothing runs
    assert {p: p.stat().st_mtime_ns for p in before} == before

    transcribe(fixture_wav, tmp_path, redo="notation")
    assert t.midi.stat().st_mtime_ns != before[t.midi]
    for p in (t.stem, t.contour, t.notes):
        assert p.stat().st_mtime_ns == before[p]
    assert json.loads(t.notes.read_text())["notes"][0]["pitch"] == data["notes"][0]["pitch"]


def test_cli_runs_end_to_end(fixture_wav, tmp_path):
    out = tmp_path / "cli"
    env = {**os.environ, "PYTHONPATH": os.getcwd()}
    result = subprocess.run([sys.executable, "-m", "saxscribe", "transcribe", str(fixture_wav),
                             "-o", str(out), "--contour-tool", "pyin", "--notes-tool", "contour"],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert (out / "score.mid").exists()


def test_notes_tagged_not_sax_stay_in_notes_json_but_leave_the_score(fixture_wav, tmp_path):
    t = transcribe(fixture_wav, tmp_path, contour_tool="pyin", notes_tool="contour")
    data = json.loads(t.notes.read_text())
    data["notes"][0]["tags"] = ["not_sax"]
    t.notes.write_text(json.dumps(data))
    transcribe(fixture_wav, tmp_path, redo="notation")
    written = json.loads(t.notation.read_text())["notes"]
    indices = [n["index"] for n in written]
    assert 0 not in indices and len(json.loads(t.notes.read_text())["notes"]) == len(data["notes"])
    assert all(data["notes"][i].get("tags") != ["not_sax"] for i in indices)
    assert max(indices) == len(data["notes"]) - 1   # indices still point into notes.json


def test_note_spacing_is_the_median_gap_between_starts():
    from saxscribe import frontend
    assert frontend.note_spacing([0, 0.25, 0.5, 0.75, 1.0, 1.005, 1.5]) == 0.25
    assert frontend.note_spacing([0, 1.0]) == 0.0      # too few notes to say


def test_basic_pitch_shortest_note_follows_the_take(monkeypatch, tmp_path):
    """The network runs once; its output is read at 50 ms, then again with the
    shortest note at 0.4 of the take's note spacing, melodia off."""
    import sys
    import types

    from saxscribe import frontend
    reads = []
    runs = []
    starts = [i * 0.3 for i in range(10)]          # notes 300 ms apart -> shortest 120 ms

    def fake_notes(output, onset_thresh, frame_thresh, min_note_len, min_freq, max_freq, melodia_trick):
        reads.append((min_note_len, melodia_trick))
        return None, [(s, s + 0.25, 65, 0.8, None) for s in starts]

    fakes = {
        "basic_pitch": types.SimpleNamespace(ICASSP_2022_MODEL_PATH="model"),
        "basic_pitch.constants": types.SimpleNamespace(AUDIO_SAMPLE_RATE=22050, FFT_HOP=256),
        "basic_pitch.inference": types.SimpleNamespace(run_inference=lambda *a: runs.append(a) or {}),
        "basic_pitch.note_creation": types.SimpleNamespace(model_output_to_notes=fake_notes),
    }
    for name, mod in fakes.items():
        monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.setattr(frontend, "load_mono", lambda path: None)
    monkeypatch.setattr(frontend, "detect_onsets", lambda y: [])
    info = {}
    notes = frontend.basic_pitch_notes(tmp_path / "x.wav", 100, 1000, info=info)
    assert len(runs) == 1 and len(notes) == 10
    frames = lambda ms: int(round(ms / 1000 * 22050 / 256))
    assert reads == [(frames(50), True), (frames(120), False)]
    assert info == {"spacing_ms": 300.0, "shortest_ms": 120.0, "restored": 0}   # slow line: no restore
    reads.clear()
    frontend.basic_pitch_notes(tmp_path / "x.wav", 100, 1000, by_spacing=False)
    assert reads == [(frames(50), True)]


def test_short_notes_come_back_when_the_recording_confirms_them():
    """A fast real note (own attack, a new pitch) dropped by the longer
    shortest-note read is put back; a split note or a ghost is not."""
    from saxscribe import frontend
    kept = [{"onset": 1.0, "offset": 1.2, "pitch": 60}, {"onset": 1.3, "offset": 1.5, "pitch": 64}]
    short = kept + [
        {"onset": 1.22, "offset": 1.27, "pitch": 62},   # passing note, own attack: back
        {"onset": 1.51, "offset": 1.55, "pitch": 64},   # same pitch as its neighbour: a split, stays out
        {"onset": 2.00, "offset": 2.05, "pitch": 67},   # no attack there: a ghost, stays out
    ]
    back = frontend.restore_short(short, kept, attacks=[1.0, 1.21, 1.3, 1.52])
    assert [n["onset"] for n in back] == [1.22]
