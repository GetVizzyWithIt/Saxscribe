"""Experiment cards and benchmark song tags (docs/evaluation) stay in step with the log and the benchmark rows."""
import json
import re
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "docs" / "evaluation"
FIELDS = {"entry", "date", "title", "stage", "problem", "hypothesis", "changed", "measure", "result", "learned",
          "decision", "revisit"}


def test_cards_have_every_field_and_match_the_log():
    cards = json.loads((EVAL / "cards.json").read_text())["cards"]
    log = (EVAL / "log.md").read_text()
    entries = set(re.findall(r"^### (E\d+) — (\d{4}-\d\d-\d\d)", log, flags=re.M))
    for c in cards:
        assert set(c) == FIELDS, c["entry"]
        assert (c["entry"], c["date"]) in entries, c["entry"]
        assert c["result"] and c["decision"], c["entry"]
    assert len({c["entry"] for c in cards}) == len(cards)


def test_every_benchmark_song_is_tagged():
    tags = json.loads((EVAL / "benchmark_tags.json").read_text())
    rows = [json.loads(line) for line in (EVAL / "experiments.jsonl").read_text().splitlines() if line.strip()]
    songs = {r["record"] for r in rows if r.get("set") == "benchmark"}
    assert songs and songs <= set(tags["songs"])
    for k, t in tags["songs"].items():
        assert t["horn"] in {"soprano", "alto", "tenor", "baritone"}, k
        assert t["style"] in tags["styles"], k
