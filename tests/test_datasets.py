"""The dataset fetcher (saxscribe/datasets.py), on local files only."""
from __future__ import annotations

import hashlib
import json
import zipfile

import pytest

from saxscribe import datasets


def make_manifest(tmp_path, md5=None):
    src = tmp_path / "src"
    src.mkdir()
    with zipfile.ZipFile(src / "toy.zip", "w") as z:
        z.writestr("Toy/notes.csv", "onset,offset,pitch\n0.5,1.0,70\n")
    good = hashlib.md5((src / "toy.zip").read_bytes()).hexdigest()
    manifest = {"datasets": [
        {"name": "Toy Set", "folder": "Toy", "access": "open", "page": "https://example.org",
         "archives": [{"file": "toy.zip", "url": (src / "toy.zip").as_uri(), "size": 1, "md5": md5 or good}]},
        {"name": "Locked Set", "folder": "Locked", "access": "manual", "access_note": "request access",
         "page": "https://example.org/locked", "archives": []},
    ]}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def test_fetch_downloads_checks_and_unpacks(tmp_path):
    m = make_manifest(tmp_path)
    root = tmp_path / "data"
    assert datasets.run(["toy"], manifest=str(m), root=str(root)) == 0
    assert (root / "Toy" / "_zips" / "toy.zip").exists()
    assert (root / "Toy" / "Toy" / "notes.csv").read_text().startswith("onset")
    assert datasets.run([], check=True, manifest=str(m), root=str(root)) == 0
    assert datasets.run(["toy"], manifest=str(m), root=str(root)) == 0  # a second run downloads nothing


def test_a_bad_checksum_is_never_kept(tmp_path):
    m = make_manifest(tmp_path, md5="0" * 32)
    root = tmp_path / "data"
    assert datasets.run(["toy"], manifest=str(m), root=str(root)) == 1
    assert not list((root / "Toy" / "_zips").glob("toy.zip*"))


def test_manual_datasets_are_listed_not_fetched(tmp_path, capsys):
    m = make_manifest(tmp_path)
    assert datasets.run(["locked"], manifest=str(m), root=str(tmp_path / "data")) == 0
    assert "request access" in capsys.readouterr().out


def test_unpacking_refuses_paths_outside_the_folder(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("../escape.txt", "x")
    with pytest.raises(RuntimeError):
        datasets.unpack(bad, tmp_path / "into")
    assert not (tmp_path / "escape.txt").exists()


def test_the_repo_manifest_reads_and_names_every_dataset():
    m = datasets.load_manifest(datasets.REPO_MANIFEST, datasets.default_root())
    assert len(m["datasets"]) == 20
    assert len(datasets.pick(m, ["orchideasol"], False)) == 2  # metadata (open) and audio (manual) share a folder
    for ds in m["datasets"]:
        for a in ds["archives"]:
            assert a["url"] is None or a["url"].startswith("https://")
            assert ds["access"] == "manual" or a["url"]
