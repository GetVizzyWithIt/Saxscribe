"""Stress scorecard: the same answer-key set, scored again under the conditions
that break transcription on real records.

  python -m saxscribe stress grfia-alto --limit 40
  python -m saxscribe stress omnibook-mix --conditions clean,detune+25,detune-50,reverb

Each condition changes the audio and, where it must, the answer key with it:
  clean        the recording as it is (the baseline)
  detune+25 / detune-25 / detune+50 / detune-50
               played faster or slower, as an old record or tape transfer that
               runs off speed: pitch moves by that many cents and every time
               shrinks or stretches by the same factor. The key moves with it.
               Off-speed transfers are common on old jazz records (the Weimar
               Jazz Database's tuning runs 428-453 Hz), and a tenth of a
               semitone cost an unaugmented piano model 10-19 points of F1
               (Edwards et al. 2024, arXiv 2402.01424)
  reverb       a 1.2 s synthetic hall (decaying noise, fixed seed), 35% wet
  lofi         80 Hz-5 kHz band limit plus hiss at 20 dB below the music,
               like an old transfer or a phone recording

The synthetic reverb and hiss are made here with their own seeds, so a model
later trained with reverb or noise augmentation is not tested on the same
sounds it trained on.

Writes stress.md and stress.json under <runs>/stress/<set>/ and adds one line
per condition to results.jsonl. Recordings with technique tags (GRFIA:
altissimo, bend, growl ...) also get a table of the clean scores by tag.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from .. import frontend
from . import card, history, refs

CONDITIONS = ("clean", "detune+25", "detune-25", "detune+50", "detune-50", "reverb", "lofi")
SHOWN = ("note_f1_no_offset", "onset_f1", "sax_found", "sax_purity", "short_found", "extras_in_rests_per_min")


def cents_of(condition: str) -> float | None:
    if condition.startswith("detune"):
        return float(condition[len("detune"):])
    return None


def degrade(y: np.ndarray, sr: int, condition: str) -> np.ndarray:
    """The recording under one condition. y is (samples,) or (samples, channels)."""
    if condition == "clean":
        return y
    two_d = y.ndim == 2
    chans = y if two_d else y[:, None]
    out = np.stack([degrade_mono(chans[:, c], sr, condition) for c in range(chans.shape[1])], axis=1)
    peak = np.max(np.abs(out)) or 1.0
    if peak > 0.99:
        out = out * (0.99 / peak)
    return out if two_d else out[:, 0]


def degrade_mono(x: np.ndarray, sr: int, condition: str) -> np.ndarray:
    from scipy import signal
    cents = cents_of(condition)
    if cents is not None:
        import librosa
        speed = 2 ** (cents / 1200)  # > 1: faster and higher
        return librosa.resample(x.astype(np.float64), orig_sr=sr * speed, target_sr=sr).astype(np.float32)
    if condition == "reverb":
        rng = np.random.default_rng(1201)
        n = int(1.2 * sr)
        ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)  # -60 dB at 1.2 s
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = signal.fftconvolve(x, ir)[: len(x)]
        return (0.65 * x + 0.35 * wet).astype(np.float32)
    if condition == "lofi":
        sos = signal.butter(4, [80, 5000], btype="band", fs=sr, output="sos")
        band = signal.sosfilt(sos, x)
        rng = np.random.default_rng(2020)
        rms = np.sqrt(np.mean(band ** 2)) or 1e-4
        return (band + rng.standard_normal(len(x)) * rms * 10 ** (-20 / 20)).astype(np.float32)
    raise ValueError(f"unknown condition {condition!r}; choose from {', '.join(CONDITIONS)}")


def shift_key(notes: list[dict], beats: list[float] | None, condition: str):
    """The answer key as it sounds under the condition: only speed changes move it."""
    cents = cents_of(condition)
    if cents is None:
        return notes, beats
    speed = 2 ** (cents / 1200)
    moved = [{**n, "onset": n["onset"] / speed, "offset": n["offset"] / speed, "pitch": n["pitch"] + cents / 100}
             for n in notes]
    return moved, ([b / speed for b in beats] if beats else beats)


def stressed_ref(ref: refs.Reference, condition: str, audio_dir: Path) -> refs.Reference:
    if condition == "clean":
        return ref
    path = audio_dir / f"{ref.id}.wav"
    if not path.exists():
        y, sr = sf.read(str(ref.audio), dtype="float32", always_2d=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), degrade(y, sr, condition), sr)
    notes, beats = shift_key(ref.notes, ref.beats, condition)
    return dataclasses.replace(ref, audio=path, notes=notes, beats=beats)


def run(set_name: str, data: str | None = None, split: str = "all", limit: int | None = None,
        runs: str | None = None, conditions: str | None = None, note: str | None = None) -> dict:
    wanted = [c.strip() for c in conditions.split(",")] if conditions else list(CONDITIONS)
    for c in wanted:
        if c not in CONDITIONS:
            raise SystemExit(f"Unknown condition {c!r}. Choose from: {', '.join(CONDITIONS)}")
    if "clean" not in wanted:
        wanted.insert(0, "clean")
    items = refs.load(set_name, data, split)[:limit] if limit else refs.load(set_name, data, split)
    if not items:
        raise SystemExit(f"No answer keys found for {set_name}.")
    base = Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs"
    out_dir = base / "stress" / set_name
    results = {}
    for c in wanted:
        frontend.log(f"Stress condition: {c}")
        stressed = [stressed_ref(r, c, out_dir / "audio" / c) for r in items]
        rows = card.score_items(stressed, out_dir / c, "auto", "auto", None)
        results[c] = {"mean": card.means(rows), "rows": rows}
        history.append(history.record({"set": set_name, "split": split, "settings": f"stress-{c}",
                                       "items": len(rows), "mean": results[c]["mean"]}, note), base)
    report = {"set": set_name, "split": split, "items": len(items), "made": time.strftime("%Y-%m-%d %H:%M"),
              "conditions": results, "by_tag": by_tag(items, results["clean"]["rows"])}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stress.json").write_text(json.dumps(report, indent=1) + "\n")
    md = markdown(report)
    (out_dir / "stress.md").write_text(md)
    print(md)
    frontend.log(f"Stress scorecard: {out_dir / 'stress.md'}")
    return report


def by_tag(items: list[refs.Reference], rows: list[dict]) -> dict:
    """Clean scores grouped by technique tag, for sets whose keys carry tags."""
    tags_of = {r.id: r.extra.get("tags") or [] for r in items}
    groups: dict[str, list[dict]] = {}
    for row in rows:
        for t in tags_of.get(row["id"], []):
            groups.setdefault(t, []).append(row)
    return {t: {"items": len(g), "mean": card.means(g)} for t, g in sorted(groups.items())}


def markdown(report: dict) -> str:
    conds = report["conditions"]
    clean = conds["clean"]["mean"]
    lines = [f"# Stress scorecard: {report['set']} ({report['split']})", "",
             f"{report['items']} recordings, {report['made']}. Each row is the same set under one "
             "condition; the change column is note F1 (ends ignored) against clean.", "",
             "| Condition | " + " | ".join(SHOWN) + " | Change |", "| --- |" + " --- |" * (len(SHOWN) + 1)]
    worst = None
    for c, res in conds.items():
        m = res["mean"]
        change = None
        if c != "clean" and "note_f1_no_offset" in m and "note_f1_no_offset" in clean:
            change = m["note_f1_no_offset"] - clean["note_f1_no_offset"]
            if worst is None or change < worst[1]:
                worst = (c, change)
        cells = [card.fmt(k, m.get(k)) for k in SHOWN]
        lines.append(f"| {c} | " + " | ".join(cells) + f" | {'' if change is None else f'{100 * change:+.1f}'} |")
    if worst:
        lines += ["", f"Worst condition: {worst[0]} ({100 * worst[1]:+.1f} points of note F1)."]
    if report["by_tag"]:
        lines += ["", "Clean scores by technique tag:", "", "| Tag | Recordings | Note F1 (ends ignored) | Sax found |",
                  "| --- | --- | --- | --- |"]
        for t, g in report["by_tag"].items():
            m = g["mean"]
            lines.append(f"| {t} | {g['items']} | {card.fmt('n', m.get('note_f1_no_offset'))} | "
                         f"{card.fmt('n', m.get('sax_found'))} |")
    return "\n".join(lines) + "\n"
