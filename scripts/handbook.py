"""Rebuild the generated blocks of HANDBOOK.md from the repo's own records.

    python3 scripts/handbook.py           # rewrite HANDBOOK.md in place
    python3 scripts/handbook.py --check   # exit 1 if HANDBOOK.md is out of date

Each block sits between <!-- auto:NAME --> and <!-- /auto:NAME --> markers.
Everything outside the markers is hand-written and left alone.

Sources:
- status, results: benchmark rows in docs/evaluation/experiments.jsonl
  (set "benchmark") and the E-entry headings in docs/evaluation/log.md
- next: docs/product/next.json (the docs thread keeps it current)

tests/test_handbook.py runs --check, so CI fails when a results or plan
change lands without the handbook being rebuilt.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDBOOK = ROOT / "HANDBOOK.md"
EXPERIMENTS = ROOT / "docs" / "evaluation" / "experiments.jsonl"
LOG = ROOT / "docs" / "evaluation" / "log.md"
NEXT = ROOT / "docs" / "product" / "next.json"

# Benchmark versions, oldest first. A milestone is an older main re-scored by
# commit; "standard" and "sax-model" are today's two paths (ADR-0041).
MILESTONES = [
    ("b3aa715", "#9 (2026-11-02)"),
    ("e01aeef", "#35 write only where the sax plays"),
    ("50b729a", "#57 restore re-tongued repeats"),
    ("80cba98", "#81 nothing below the low note"),
]
SAX_MODEL_SEPARATOR = "rd-filosax-demucs"  # the band-record default since ADR-0041
GROUPS = [("e80", "Austin's 6 tunes"), ("transcribed", "Transcribed songs"), ("parker", "Parker test")]
LATEST_EXPERIMENTS = 10


def version_of(row: dict) -> str:
    s = row["setup"]
    if s.get("variant"):
        return s["variant"]
    return "sax-model" if s.get("separator") == SAX_MODEL_SEPARATOR else "standard"


def label_of(version: str, commit: str) -> str:
    names = dict(MILESTONES)
    if version in names:
        return names[version]
    if version == "sax-model":
        return f"**Our sax model ({commit}, default on band records)**"
    return f"Standard path ({commit})"


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def benchmark() -> dict[str, list[dict]]:
    by_version: dict[str, list[dict]] = defaultdict(list)
    for line in EXPERIMENTS.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("set") == "benchmark":
                by_version[version_of(row)].append(row)
    return by_version


def mean(rows: list[dict], metric: str) -> float:
    return statistics.mean(r["metrics"][metric] for r in rows)


def latest_entry(rows: list[dict]) -> str:
    return max((r.get("entry", "") for r in rows), key=lambda e: int(e[1:] or 0))


def block_status(bench: dict[str, list[dict]]) -> str:
    d, a = bench["sax-model"], bench["standard"]
    n = len(d)
    entry = latest_entry(d)
    a_by_song = {r["record"]: r["metrics"]["note_f1"] for r in a}
    wins = sum(r["metrics"]["note_f1"] > a_by_song.get(r["record"], 1) for r in d)
    at60 = sum(r["metrics"]["note_f1"] >= 0.6 for r in d)
    weakest = sorted(d, key=lambda r: r["metrics"]["note_f1"])[:6]
    weak = ", ".join(f"{r['title'].split(' (')[0]} {pct(r['metrics']['note_f1'])}" for r in weakest)
    kinds = defaultdict(int)
    for r in d:
        for k, v in r.get("key_notes", {}).items():
            kinds[k] += v
    total = sum(kinds.values()) or 1
    share = lambda k: f"{round(100 * kinds[k] / total)}%"
    ends = mean(d, "note_f1_no_offset") - mean(d, "note_f1")
    return "\n".join([
        "| | |",
        "| --- | --- |",
        "| Default on band records (app) | **Our sax model**: the Filosax sax separator plus our fine-tuned note finder (E77), \"D\" in the scorecards ([ADR-0041](docs/decisions/0041-band-records-default-to-our-sax-model.md)) |",
        "| Default on solo takes and the CLI | **Standard path**: Basic Pitch notes, CREPE pitch line; Demucs first when `--mix` |",
        f"| Benchmark score ({entry}, {n} trusted songs) | Note F1 **{pct(mean(d, 'note_f1'))}** with our sax model, against {pct(mean(a, 'note_f1'))} for the standard path. Onset F1 {pct(mean(d, 'onset_f1'))} against {pct(mean(a, 'onset_f1'))}. Note F1 without note ends: {pct(mean(d, 'note_f1_no_offset'))} |",
        f"| How the {n} songs break down | {at60} of {n} at note F1 60 or above. Our sax model beats the standard path on {wins} of {n} |",
        f"| Weakest songs (our sax model) | {weak} |",
        f"| Where the notes go wrong (key notes, {entry}) | {share('right')} right, {share('missed')} missed, {share('timing')} start off, {share('wrong_pitch')} wrong pitch, {share('merged')} merged. Note ends cost about {round(100 * ends)} points of note F1 on average |",
    ])


def block_next() -> str:
    plan = json.loads(NEXT.read_text())
    out = [plan["intro"], "", "| Step | What | Status |", "| --- | --- | --- |"]
    for s in plan["steps"]:
        out.append(f"| {s['step']} | **{s['title']}**: {s['what']} | {s['status']} |")
    if plan.get("running"):
        out += ["", f"**Running on the Mac now:** {plan['running']}"]
    if plan.get("waiting"):
        out += ["", "**Waiting on Austin:**"] + [f"- {w}" for w in plan["waiting"]]
    out += ["", f"_Plan last changed {plan['updated']}._"]
    return "\n".join(out)


def log_entries() -> list[tuple[int, str, str, str]]:
    """(number, date, title, outcome) per log entry, newest first.

    The outcome is the entry's "- **Headline**:" line, else the heading's parenthetical.
    """
    heads = re.findall(r"^### E(\d+) — (\d{4}-\d{2}-\d{2}) — (.+)\n(?:- \*\*Headline\*\*: (.+)\n)?",
                       LOG.read_text(), flags=re.M)
    out = []
    for num, date, title, headline in heads:
        m = re.match(r"(.*?)\s*\(([^()]*)\)\s*$", title)
        out.append((int(num), date, m.group(1) if m else title, headline or (m.group(2) if m else "")))
    return sorted(out, reverse=True)


def block_results(bench: dict[str, list[dict]]) -> str:
    d = bench["sax-model"]
    entry, n = latest_entry(d), len(d)
    out = [f"**How we got here** ({entry}, mean on the {n}-song benchmark):", "",
           "| Version | Note F1 | Onset F1 |", "| --- | --- | --- |"]
    for v in [c for c, _ in MILESTONES] + ["standard", "sax-model"]:
        rows = bench.get(v)
        if rows:
            out.append(f"| {label_of(v, rows[0]['commit'])} | {pct(mean(rows, 'note_f1'))} | {pct(mean(rows, 'onset_f1'))} |")
    out += ["", "Note F1 by group:", "", "| Group | Standard path | Our sax model |", "| --- | --- | --- |"]
    for kind, name in GROUPS:
        a = [r for r in bench["standard"] if r["key"].get("kind") == kind]
        s = [r for r in d if r["key"].get("kind") == kind]
        if a and s:
            out.append(f"| {name} ({len(s)}) | {pct(mean(a, 'note_f1'))} | {pct(mean(s, 'note_f1'))} |")
    out += ["", "**Latest experiments:**", "",
            "| E | Date | What | Outcome |", "| --- | --- | --- | --- |"]
    for num, date, title, verdict in log_entries()[:LATEST_EXPERIMENTS]:
        out.append(f"| E{num} | {date} | {title} | {verdict} |")
    out += ["", "Full record: [evaluation log](docs/evaluation/log.md). Live charts: the app's Results page (`/results`)."]
    return "\n".join(out)


def render(text: str) -> str:
    bench = benchmark()
    blocks = {"status": block_status(bench), "next": block_next(), "results": block_results(bench)}
    for name, body in blocks.items():
        pattern = re.compile(rf"(<!-- auto:{name} -->\n).*?(\n<!-- /auto:{name} -->)", re.S)
        if not pattern.search(text):
            raise SystemExit(f"HANDBOOK.md has no auto:{name} block")
        text = pattern.sub(lambda m: m.group(1) + body + m.group(2), text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if HANDBOOK.md is out of date")
    args = ap.parse_args()
    old = HANDBOOK.read_text()
    new = render(old)
    if args.check:
        if new != old:
            print("HANDBOOK.md is out of date: run python3 scripts/handbook.py")
            return 1
        print("HANDBOOK.md is up to date")
        return 0
    HANDBOOK.write_text(new)
    print("HANDBOOK.md", "updated" if new != old else "already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
