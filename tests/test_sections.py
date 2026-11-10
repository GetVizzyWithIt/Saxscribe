"""Sax sections typed at upload: parsing, tagging notes outside them, and the CLI/app plumbing."""
from __future__ import annotations

import json

import pytest

from saxscribe import sections
from saxscribe.app.library import Library


def test_parse_reads_minutes_and_seconds_and_merges_overlaps():
    assert sections.parse("3:45-4:21, 5:10 – 5:40") == [[225.0, 261.0], [310.0, 340.0]]
    assert sections.parse("10-20; 15-30") == [[10.0, 30.0]]
    assert sections.parse("1:02:03 to 1:03:00") == [[3723.0, 3780.0]]
    assert sections.parse("") == [] and sections.parse(None) == []


@pytest.mark.parametrize("bad", ["4:21-3:45", "3:75-4:00", "abc", "3:45", "3:45-"])
def test_parse_rejects_what_is_not_a_section(bad):
    with pytest.raises(ValueError):
        sections.parse(bad)


def test_text_round_trips():
    secs = [[225.0, 261.0], [310.0, 340.0]]
    assert sections.parse(sections.text(secs)) == secs


def test_notes_outside_every_section_are_tagged_not_deleted():
    notes = [{"onset": t, "tags": []} for t in (1.0, 8.5, 12.0, 21.5, 30.0)]
    n = sections.tag(notes, [[10.0, 20.0]], "not_sax")
    assert n == 2  # 1.0 and 30.0; 8.5 and 21.5 sit inside the 2 s padding
    assert [("not_sax" in x["tags"]) for x in notes] == [True, False, False, False, True]
    assert all(sections.OUTSIDE in x["tags"] for x in notes if "not_sax" in x["tags"])
    assert len(notes) == 5


def test_the_app_passes_sections_to_the_transcriber(tmp_path):
    lib = Library(tmp_path, inline=False)
    lib._enqueue = lambda take_id: None  # don't run it
    take_id = lib.add("song.wav", b"RIFF", horn="tenor", mix=True, sections=[[225.0, 261.0]])
    job = json.loads((tmp_path / take_id / "job.json").read_text())
    assert job["sections"] == [[225.0, 261.0]]
    cmd = lib.command(take_id)
    assert cmd[cmd.index("--sections") + 1] == "3:45-4:21"


def test_a_take_with_sections_hides_only_the_notes_outside_them(tmp_path, fixture_wav):
    from saxscribe.pipeline import transcribe
    take = transcribe(fixture_wav, tmp_path / "take", horn="alto")
    before = json.loads(take.notes.read_text())["notes"]
    shown = [n for n in before if "not_sax" not in n["tags"]]
    assert len(shown) >= 6
    mid = shown[len(shown) // 2]["onset"]
    keep = [[mid, mid + 0.5]]
    take = transcribe(fixture_wav, tmp_path / "take", horn="alto", sections=keep)  # only the notes layer redone
    after = json.loads(take.notes.read_text())
    assert len(after["notes"]) == len(before)  # nothing deleted
    for n in after["notes"]:
        outside = not sections.inside(n["onset"], keep)
        assert (sections.OUTSIDE in n["tags"]) == outside
    manifest = take.read_manifest()
    assert manifest["sax_sections"] == keep
    assert manifest["layers"]["notes"]["sax_sections"]["sections"] == keep
