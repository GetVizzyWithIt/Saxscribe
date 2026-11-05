"""Riley and Dixon's Filosax separator and transcriber (opt-in): the vendored
decoder, the weight checks, and both wired through the pipeline and the app.

The real weights are not downloaded here; the pipeline tests stand in for the
two models and check what the layers do with their output."""
from __future__ import annotations

import json
import shutil

import numpy as np
import pytest
import soundfile as sf

from saxscribe import filosax, frontend
from saxscribe.pipeline import transcribe

from . import fixture

torch = pytest.importorskip("torch")
pytest.importorskip("torchlibrosa")

from saxscribe.vendor import kong  # noqa: E402


def peaks(frames: int, at: dict[int, list[int]]) -> np.ndarray:
    """Regression targets as the model writes them: a peak at each listed frame, per pitch class."""
    x = np.zeros((frames, kong.CLASSES), dtype=np.float32)
    for k, where in at.items():
        for f in where:
            for d, v in zip(range(-4, 5), (0.1, 0.2, 0.4, 0.7, 1.0, 0.7, 0.4, 0.2, 0.1)):
                x[f + d, k] = max(x[f + d, k], v)
    return x


def test_decoder_finds_each_note_with_its_pitch_and_times():
    frames = 300
    k = 66 - kong.BEGIN_NOTE  # concert F#4
    frame = np.zeros((frames, kong.CLASSES), dtype=np.float32)
    frame[50:120, k] = 0.9
    frame[150:200, k] = 0.9
    out = {"reg_onset_output": peaks(frames, {k: [50, 150]}), "reg_offset_output": peaks(frames, {k: [120, 200]}),
           "frame_output": frame, "velocity_output": np.full((frames, kong.CLASSES), 0.5, dtype=np.float32)}
    notes = sorted(kong.decode(out, 0.3, 0.3, 0.1), key=lambda n: n["onset"])
    assert [n["pitch"] for n in notes] == [66, 66]
    assert [round(n["onset"], 2) for n in notes] == [0.5, 1.5]
    assert [round(n["offset"], 2) for n in notes] == [1.2, 2.0]
    assert notes[0]["velocity"] == 64


def test_a_flat_topped_peak_does_not_give_a_missing_time():
    x = np.zeros((40, kong.CLASSES), dtype=np.float32)
    x[18:23, 0] = [0.5, 0.8, 0.8, 0.5, 0.2]  # two equal frames at the top
    binary, shift = kong.binarize(x, 0.3, 2)
    assert np.isfinite(shift).all()


def test_model_runs_on_the_fixture_and_keeps_its_length(fixture_wav):
    torch.manual_seed(0)
    model = kong.Regress_onset_offset_frame_velocity_CRNN()
    audio = frontend.load_mono(fixture_wav, sr=kong.SAMPLE_RATE)
    out = kong.run_model(model, audio)
    assert set(out) == {"reg_onset_output", "reg_offset_output", "frame_output", "velocity_output"}
    frames = out["frame_output"].shape[0]
    assert out["frame_output"].shape[1] == 88
    assert abs(frames - len(audio) / kong.SAMPLE_RATE * kong.FRAMES_PER_SECOND) < 2


def test_transcriber_weights_load_with_the_safe_loader(tmp_path):
    torch.manual_seed(0)
    model = kong.Regress_onset_offset_frame_velocity_CRNN()
    path = tmp_path / "ckpt.pth"
    # The real file carries numpy arrays in its sampler state, which the safe loader must accept.
    torch.save({"model": model.state_dict(), "iteration": 25000, "sampler": {"order": np.arange(5)}}, path)
    loaded = filosax.load_transcriber(path)
    a, b = model.state_dict(), loaded.state_dict()
    assert all(torch.equal(a[k], b[k]) for k in a)


def test_a_checkpoint_that_is_not_the_tested_one_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("SAXSCRIBE_MODELS", str(tmp_path))
    (tmp_path / filosax.WEIGHTS["transcriber"]["file"]).write_bytes(b"not the weights")
    with pytest.raises(SystemExit, match="sha256"):
        filosax.weights("transcriber")


def fake_models(monkeypatch, fixture_wav, notes):
    def separate(wav, out_dir, device="cpu"):
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture_wav, out_dir / "saxophone.wav")
        y, rate = sf.read(str(fixture_wav))
        sf.write(str(out_dir / "backing.wav"), np.zeros_like(y), rate)
        return {"saxophone": out_dir / "saxophone.wav", "backing": out_dir / "backing.wav"}
    monkeypatch.setattr(filosax, "separate", separate)
    monkeypatch.setattr(filosax, "transcribe", lambda stem, model=None: [dict(n) for n in notes])
    monkeypatch.setattr(frontend, "demucs_available", lambda: True)


def test_band_record_through_both_filosax_models(tmp_path, monkeypatch, fixture_wav):
    truth = [dict(n, amp=0.6) for n in fixture.truth()]
    fake_models(monkeypatch, fixture_wav, truth)
    take = transcribe(fixture_wav, tmp_path / "take", mix=True, separator="filosax", notes_tool="filosax")
    manifest = take.read_manifest()
    iso, nl = manifest["layers"]["isolate"], manifest["layers"]["notes"]
    assert iso["separator"] == "filosax" and iso["stem"] == "saxophone"
    assert (take.folder / "stems-filosax" / "backing.wav").exists()
    assert nl["tool"] == "filosax" and nl["sax_spans"].startswith("skipped")
    data = json.loads(take.notes.read_text())
    assert len(data["notes"]) == len(truth)  # every note the transcriber found is kept
    assert [n["pitch"] for n in data["notes"]] == [n["pitch"] for n in truth]
    assert not any("not_sax" in n["tags"] for n in data["notes"])
    assert take.has("notation")


def test_switching_separator_remakes_every_layer(tmp_path, monkeypatch, fixture_wav):
    fake_models(monkeypatch, fixture_wav, [dict(n, amp=0.6) for n in fixture.truth()])
    monkeypatch.setattr(frontend, "separate_stems", lambda wav, out: pytest.fail("Demucs should not run"))
    out = tmp_path / "take"
    transcribe(fixture_wav, out, mix=True, separator="filosax", notes_tool="filosax")
    calls = []
    monkeypatch.setattr(filosax, "separate", lambda *a, **k: calls.append(a))
    transcribe(fixture_wav, out, mix=True, separator="filosax", notes_tool="filosax")
    assert calls == []  # same separator: nothing remade

    def demucs(wav, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture_wav, out_dir / "other.wav")
        return {"other": out_dir / "other.wav"}
    monkeypatch.setattr(frontend, "separate_stems", demucs)
    take = transcribe(fixture_wav, out, mix=True, notes_tool="contour", contour_tool="pyin")
    assert take.read_manifest()["layers"]["isolate"]["tool"].startswith("demucs")


def test_app_passes_the_filosax_choice_to_the_command(tmp_path, fixture_wav):
    pytest.importorskip("fastapi")
    from saxscribe.app.library import Library
    lib = Library(tmp_path / "lib")
    lib._enqueue = lambda take_id: None  # don't run it
    band = lib.add("phrase.wav", fixture_wav.read_bytes(), mix=True, engine="filosax")
    solo = lib.add("phrase.wav", fixture_wav.read_bytes(), mix=False, engine="filosax")
    plain = lib.add("phrase.wav", fixture_wav.read_bytes(), mix=True)
    assert lib.command(band)[-5:] == ["--mix", "--notes-tool", "filosax", "--separator", "filosax"]
    assert lib.command(solo)[-2:] == ["--notes-tool", "filosax"]
    assert "filosax" not in lib.command(plain)
    with pytest.raises(ValueError):
        lib.add("phrase.wav", fixture_wav.read_bytes(), engine="nope")


def test_separator_loads_a_demucs_package_safely_and_writes_two_stems(tmp_path, monkeypatch, fixture_wav):
    pytest.importorskip("demucs")
    from demucs.hdemucs import HDemucs
    torch.manual_seed(0)
    model = HDemucs(sources=["Sax", "BackingMono"], channels=4)
    path = tmp_path / "sep.th"
    args, kwargs = model._init_args_kwargs  # the layout of the real file: klass, args, kwargs, state, ...
    torch.save({"klass": HDemucs, "args": args, "kwargs": kwargs, "state": model.state_dict(),
                "metrics": {}, "training_args": {}}, path)
    monkeypatch.setattr(filosax, "weights", lambda name: path)
    stems = filosax.separate(fixture_wav, tmp_path / "stems")
    assert set(stems) == {"saxophone", "backing"}
    y, rate = sf.read(str(stems["saxophone"]))
    assert rate == model.samplerate and y.ndim == 2 and abs(len(y) / rate - fixture.SECONDS) < 0.1
