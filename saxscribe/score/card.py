"""Runs the pipeline over a whole answer-key set and writes the scorecard.

  python -m saxscribe score omnibook
  python -m saxscribe score filosax --split test
  python -m saxscribe score pairs --data ~/Music/Etudes --notes-tool contour

Each run's take folders are kept under ~/saxscribe-runs/<set>/<settings>/, so
changing a setting re-runs only what it touches, and comparing two settings
is two commands. Writes scorecard.md and scorecard.json there, and adds the
run to <runs>/results.jsonl, which the app's Results page plots (history.py).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from .. import frontend
from ..pipeline import transcribe
from ..take import Take
from . import history, metrics, refs

# v1 targets from the requirements doc: (solo recording, full mix).
TARGETS = {"pitch_accuracy": (0.97, 0.90), "onset_f1": (0.90, 0.75), "note_f1": (0.80, 0.60),
           "beat_f1": (0.95, 0.95), "seconds_per_minute": (15.0, 60.0)}
COLUMNS = ("pitch_accuracy", "chroma_accuracy", "octave_errors", "onset_f1", "note_f1", "note_f1_no_offset", "sax_found", "sax_purity", "beat_f1", "seconds_per_minute")
# The Omnibook's audio is already separated from the records, so it is held to the full-mix targets.
MIX_SETS = {"omnibook", "omnibook-mix", "urmp-mix", "bach10-mix"}


def settings_name(contour_tool: str, notes_tool: str, range_rules: str = "out", separator: str = "demucs") -> str:
    parts = [f"sep-{separator}" if separator != "demucs" else "",
             f"contour-{contour_tool}" if contour_tool != "auto" else "",
             f"notes-{notes_tool}" if notes_tool != "auto" else "",
             f"range-{range_rules}" if range_rules != "out" else ""]
    return "-".join(p for p in parts if p) or "default"


def run(set_name: str, data: str | None = None, split: str = "all", limit: int | None = None,
        runs: str | None = None, contour_tool: str = "auto", notes_tool: str = "auto",
        redo: str | None = None, note: str | None = None, range_rules: str = "out",
        tag: str | None = None, separator: str = "demucs") -> dict:
    items = refs.load(set_name, data, split)
    if tag:  # e.g. only GRFIA's takes tagged altissimo
        items = [r for r in items if tag.lower() in (r.extra.get("tags") or [])]
    if limit:
        items = items[:limit]
    if not items:
        raise SystemExit(f"No answer keys found for {set_name}.")
    name = settings_name(contour_tool, notes_tool, range_rules, separator)
    if tag:
        name = f"{name}-tag-{tag.lower()}"
    base = Path(runs).expanduser() if runs else Path.home() / "saxscribe-runs"
    out_dir = base / set_name / name
    out_dir.mkdir(parents=True, exist_ok=True)
    # A scorecard never needs PDFs: rendering one per take opens MuseScore
    # hundreds of times (its window flashes on a Mac) and slows the run.
    pdfs_before = os.environ.get("SAXSCRIBE_MUSESCORE")
    os.environ["SAXSCRIBE_MUSESCORE"] = "off"
    try:
        rows = score_items(items, out_dir, contour_tool, notes_tool, redo, range_rules, separator)
    finally:
        if pdfs_before is None:
            os.environ.pop("SAXSCRIBE_MUSESCORE", None)
        else:
            os.environ["SAXSCRIBE_MUSESCORE"] = pdfs_before
    card = {"set": set_name, "split": split, "settings": name, "items": len(rows),
            "partial": any(getattr(r, "partial", False) for r in items),
            "made": time.strftime("%Y-%m-%d %H:%M"), "mean": means(rows), "rows": rows}
    (out_dir / "scorecard.json").write_text(json.dumps(card, indent=1) + "\n")
    md = markdown(card, set_name in MIX_SETS or any(r.is_mix for r in items))
    (out_dir / "scorecard.md").write_text(md)
    print(md)
    frontend.log(f"Scorecard: {out_dir / 'scorecard.md'}")
    history.append(history.record(card, note), base)
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
                     f"{fmt('n', r.get('note_f1'))} | {r.get('est_notes')} / {r.get('ref_notes')}"
                     f"{' (' + str(r['key_notes_cut']) + ' in cut stretches)' if r.get('key_notes_cut') else ''} |")
    hidden = sum(r.get("key_notes_cut") or 0 for r in card["rows"])
    if any("key_notes_cut" in r for r in card["rows"]):
        lines += ["", f"Sax-span check: {hidden} answer-key notes fall where the sax was judged to lay out "
                  "(left off the score and the sheet music). Above zero means a cut hid real sax notes."]
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


def score_items(items, out_dir, contour_tool, notes_tool, redo, range_rules="out", separator="demucs") -> list[dict]:
    rows = []
    for i, ref in enumerate(items, 1):
        frontend.log(f"[{i}/{len(items)}] {ref.id}")
        folder = out_dir / ref.id
        fresh = not Take(folder).has("notation") or redo is not None
        t0 = time.time()
        take = transcribe(ref.audio, folder, mix=ref.is_mix, horn=ref.extra.get("horn", "alto"),
                          contour_tool=contour_tool, notes_tool=notes_tool, redo=redo,
                          range_rules=range_rules, separator=separator)
        row = {"id": ref.id, "tune": ref.tune, "player": ref.player, "horn": ref.extra.get("horn", "alto"),
               "split": refs.split_of(ref)}
        try:
            row.update(metrics.score_take(ref, take))
        except ValueError as exc:  # one bad answer key must not stop a long run
            frontend.log(f"  could not score {ref.id}: {exc}; left out of the card")
            continue
        minutes = max(n["offset"] for n in ref.notes) / 60 if ref.notes else 0
        timing = take.read_manifest().get("seconds_per_minute")
        if fresh and minutes:
            timing = round((time.time() - t0) / minutes, 1)
            m = take.read_manifest()
            m["seconds_per_minute"] = timing
            take.write_manifest(m)
        row["seconds_per_minute"] = timing
        rows.append(row)
    return rows
