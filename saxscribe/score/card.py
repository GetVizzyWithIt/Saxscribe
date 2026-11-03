"""Runs the pipeline over a whole answer-key set and writes the scorecard.

  python -m saxscribe score omnibook
  python -m saxscribe score filosax --split test
  python -m saxscribe score pairs --data ~/Music/Etudes --notes-tool contour

Each run's take folders are kept under ~/saxscribe-runs/<set>/<settings>/, so
changing a setting re-runs only what it touches, and comparing two settings
is two commands. Writes scorecard.md and scorecard.json there.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from .. import frontend
from ..pipeline import transcribe
from ..take import Take
from . import metrics, refs

# v1 targets from the requirements doc: (solo recording, full mix).
TARGETS = {"pitch_accuracy": (0.97, 0.90), "onset_f1": (0.90, 0.75), "note_f1": (0.80, 0.60),
           "beat_f1": (0.95, 0.95), "seconds_per_minute": (15.0, 60.0)}
COLUMNS = ("pitch_accuracy", "chroma_accuracy", "octave_errors", "onset_f1", "note_f1", "note_f1_no_offset", "beat_f1", "seconds_per_minute")
# The Omnibook's audio is already separated from the records, so it is held to the full-mix targets.
MIX_SETS = {"omnibook", "omnibook-mix", "urmp-mix", "bach10-mix"}


def settings_name(contour_tool: str, notes_tool: str) -> str:
    parts = [f"contour-{contour_tool}" if contour_tool != "auto" else "",
             f"notes-{notes_tool}" if notes_tool != "auto" else ""]
    return "-".join(p for p in parts if p) or "default"


def run(set_name: str, data: str | None = None, split: str = "all", limit: int | None = None,
        runs: str | None = None, contour_tool: str = "auto", notes_tool: str = "auto",
        redo: str | None = None) -> dict:
    items = refs.load(set_name, data, split)
    if limit:
        items = items[:limit]
    if not items:
        raise SystemExit(f"No answer keys found for {set_name}.")
    name = settings_name(contour_tool, notes_tool)
    base = Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs"
    out_dir = base / set_name / name
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, ref in enumerate(items, 1):
        frontend.log(f"[{i}/{len(items)}] {ref.id}")
        folder = out_dir / ref.id
        fresh = not Take(folder).has("notation") or redo is not None
        t0 = time.time()
        take = transcribe(ref.audio, folder, mix=ref.is_mix, horn=ref.extra.get("horn", "alto"),
                          contour_tool=contour_tool, notes_tool=notes_tool, redo=redo)
        row = {"id": ref.id, "tune": ref.tune, "player": ref.player, "horn": ref.extra.get("horn", "alto"),
               "split": refs.split_of(ref)}
        row.update(metrics.score_take(ref, take))
        minutes = max(n["offset"] for n in ref.notes) / 60 if ref.notes else 0
        timing = take.read_manifest().get("seconds_per_minute")
        if fresh and minutes:
            timing = round((time.time() - t0) / minutes, 1)
            m = take.read_manifest()
            m["seconds_per_minute"] = timing
            take.write_manifest(m)
        row["seconds_per_minute"] = timing
        rows.append(row)
    card = {"set": set_name, "split": split, "settings": name, "items": len(rows),
            "partial": any(getattr(r, "partial", False) for r in items),
            "made": time.strftime("%Y-%m-%d %H:%M"), "mean": means(rows), "rows": rows}
    (out_dir / "scorecard.json").write_text(json.dumps(card, indent=1) + "\n")
    md = markdown(card, set_name in MIX_SETS or any(r.is_mix for r in items))
    (out_dir / "scorecard.md").write_text(md)
    print(md)
    frontend.log(f"Scorecard: {out_dir / 'scorecard.md'}")
    return card


def means(rows: list[dict]) -> dict:
    out = {}
    for col in COLUMNS:
        vals = [r[col] for r in rows if r.get(col) is not None]
        if vals:
            out[col] = round(float(np.mean(vals)), 4)
    return out


def markdown(card: dict, is_mix: bool) -> str:
    which = 1 if is_mix else 0
    lines = [f"# Scorecard: {card['set']} ({card['split']}, {card['settings']})", "",
             f"{card['items']} recordings, {card['made']}. Targets are the v1 "
             f"{'full-mix' if is_mix else 'solo-recording'} targets."
             + (" Answer keys cover part of each recording; only notes inside each key's span are scored."
                if card.get("partial") else ""), "",
             "| Measure | Mean | Target | |", "| --- | --- | --- | --- |"]
    for col in COLUMNS:
        if col not in card["mean"]:
            continue
        v = card["mean"][col]
        target = TARGETS.get(col, (None, None))[which]
        if target is None:
            lines.append(f"| {col} | {fmt(col, v)} | | |")
            continue
        ok = v <= target if col == "seconds_per_minute" else v >= target
        lines.append(f"| {col} | {fmt(col, v)} | {fmt(col, target)} | {'met' if ok else 'not yet'} |")
    lines += ["", "| Recording | Pitch | Octave errors | Onset F1 | Note F1 | Notes (ours / key) |",
              "| --- | --- | --- | --- | --- | --- |"]
    flagged = []
    for r in card["rows"]:
        octave = r.get("octave_errors")
        flag = octave is not None and octave > metrics.OCTAVE_FLAG
        if flag:
            flagged.append(r["id"])
        lines.append(f"| {r['id']} | {fmt('p', r.get('pitch_accuracy'))} | "
                     f"{fmt('x', octave)}{' (check)' if flag else ''} | {fmt('o', r.get('onset_f1'))} | "
                     f"{fmt('n', r.get('note_f1'))} | {r.get('est_notes')} / {r.get('ref_notes')} |")
    if flagged:
        lines += ["", f"Octave check: {', '.join(flagged)} have over {metrics.OCTAVE_FLAG:.0%} of frames right "
                  "except for the octave. Either the answer key is in the wrong octave there or the pitch "
                  "line dropped an octave; chroma_accuracy shows the score with octaves forgiven."]
    return "\n".join(lines) + "\n"


def fmt(col: str, v) -> str:
    if v is None:
        return "-"
    if col == "seconds_per_minute":
        return f"{v:.0f} s"
    return f"{100 * v:.1f}%"
