"""Rebuild ~/mir_datasets on any machine from its manifest.

  python -m saxscribe fetch --list            what the manifest holds, and what is here
  python -m saxscribe fetch urmp bach10       download, check and unpack these
  python -m saxscribe fetch --all             every dataset that can be downloaded directly
  python -m saxscribe fetch --check           only check the files already here

The manifest (MANIFEST.json) lists each dataset with its folder, page,
license, access ("open" = direct download, "manual" = needs a login, form or
approval) and archives [{file, url, size, md5}]. Layout on disk:
<root>/<folder>/_zips/<file> for each download, unpacked beside _zips/.

Which manifest: --manifest, else datasets/manifest.json in this repo, else
<root>/MANIFEST.json. Which root: --root, else config.local.toml
[data] root, else ~/mir_datasets.

A download is checked against its md5 before it is kept, so a cut-off
transfer is never unpacked. Manual datasets are listed with their page and
what to do; nothing here signs in for you.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path

REPO_MANIFEST = Path(__file__).resolve().parents[1] / "datasets" / "manifest.json"
CHUNK = 1 << 20
# Files kept in the dataset folder itself rather than _zips/, as the manifest's notes say.
IN_ROOT = {"IowaMIS": None, "WeimarJazzDatabase": {"wjazzd.db"}}  # None: every file


def default_root() -> Path:
    from .score.refs import config
    configured = config().get("data", {}).get("root")
    return Path(configured).expanduser() if configured else Path.home() / "mir_datasets"


def load_manifest(path: Path | None, root: Path) -> dict:
    for cand in ([path] if path else [REPO_MANIFEST, root / "MANIFEST.json"]):
        if cand and Path(cand).expanduser().exists():
            return json.loads(Path(cand).expanduser().read_text())
    raise SystemExit("No manifest found: pass --manifest, or add datasets/manifest.json.")


def key(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum())


def pick(manifest: dict, names: list[str], every: bool) -> list[dict]:
    sets = manifest.get("datasets", [])
    if every:
        return sets
    found = []
    for name in names:
        hits = [d for d in sets if key(name) in (key(d["name"]), key(d.get("folder", "")))]
        if not hits:
            hits = [d for d in sets if key(name) in key(d["name"])]
        if len({d.get("folder") or d["name"] for d in hits}) != 1:  # one folder can hold two entries
            options = ", ".join(d.get("folder") or d["name"] for d in sets)
            raise SystemExit(f"'{name}' matches {len(hits)} datasets. Use a folder name: {options}")
        found += hits
    return found


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def folder_of(root: Path, ds: dict) -> Path:
    return root / (ds.get("folder") or ds["name"])


def dest_of(root: Path, ds: dict, archive: dict) -> Path:
    """Where a download lives: <folder>/_zips/<file>, or the folder itself for the exceptions."""
    keep = IN_ROOT.get(ds.get("folder"), set())
    if keep is None or archive["file"] in keep:
        return folder_of(root, ds) / archive["file"]
    return folder_of(root, ds) / "_zips" / archive["file"]


def find(root: Path, ds: dict, archive: dict) -> Path:
    """Where a download already is: its usual place, or loose in the dataset folder
    (some small files, such as a metadata CSV or a README, were saved beside _zips/)."""
    usual = dest_of(root, ds, archive)
    loose = folder_of(root, ds) / archive["file"]
    return usual if usual.exists() or not loose.exists() else loose


def unpacks(ds: dict) -> bool:
    return not str(ds.get("extract", "")).lower().startswith("none")


def unstable(archive: dict) -> bool:
    """A zip the server builds on request (Dataverse): its md5 can change between downloads."""
    return "may change" in str(archive.get("checksum_source", ""))


def status(root: Path, ds: dict, verify: bool = False) -> tuple[int, int]:
    """(archives present and good, archives listed)."""
    good = 0
    for a in ds.get("archives", []):
        p = find(root, ds, a)
        if p.exists() and (not verify or not a.get("md5") or unstable(a) or md5_of(p) == a["md5"]):
            good += 1
    return good, len(ds.get("archives", []))


def download(url: str, dest: Path, md5: str | None, strict: bool = True) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url) as r, open(part, "wb") as out:
        shutil.copyfileobj(r, out, CHUNK)
    if md5 and md5_of(part) != md5 and not strict:
        print(f"  note    {dest.name}: md5 differs from the manifest, as expected for a zip built on request")
    elif md5 and md5_of(part) != md5:
        part.unlink()
        raise RuntimeError(f"{dest.name}: checksum does not match the manifest (download cut off or changed)")
    part.replace(dest)


def unpack(archive: Path, into: Path) -> bool:
    """Unpack a zip or tar beside _zips/. Refuses paths that would land outside it."""
    into = into.resolve()

    def safe(name: str) -> bool:
        return (into / name).resolve().is_relative_to(into)

    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            if not all(safe(n) for n in z.namelist()):
                raise RuntimeError(f"{archive.name}: has paths outside its folder, not unpacked")
            z.extractall(into)
        return True
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as t:
            if not all(safe(m.name) and not (m.issym() or m.islnk()) for m in t.getmembers()):
                raise RuntimeError(f"{archive.name}: has paths or links outside its folder, not unpacked")
            t.extractall(into)
        return True
    return False  # a plain file (a CSV, a single WAV): kept as downloaded


def fetch(root: Path, ds: dict, extract: bool = True) -> list[str]:
    """Download, check and unpack one dataset. Returns problems found, if any."""
    name = ds["name"]
    if ds.get("access") == "manual":
        note = ds.get("access_note", "needs a login, form or approval")
        return [f"{name}: manual ({note}). Page: {ds.get('page', '?')}"]
    if ds.get("skipped"):
        return [f"{name}: skipped in the manifest ({ds['skipped']})"]
    problems = []
    for a in ds.get("archives", []):
        dest = find(root, ds, a)
        try:
            if dest.exists() and (not a.get("md5") or unstable(a) or md5_of(dest) == a["md5"]):
                print(f"  ok      {name}/{a['file']}")
            elif not a.get("url"):
                problems.append(f"{name}/{a['file']}: no download link; get it from {ds.get('page', '?')}")
                continue
            else:
                print(f"  fetch   {name}/{a['file']} ({a.get('size', '?')} bytes)")
                download(a["url"], dest, a.get("md5"), strict=not unstable(a))
            marker = dest.with_name(f".{dest.name}.unpacked")
            if extract and unpacks(ds) and not marker.exists() and dest.parent.name == "_zips":
                if unpack(dest, folder_of(root, ds)):
                    print(f"  unpack  {name}/{a['file']}")
                marker.write_text("")
        except Exception as exc:  # keep going: one bad link should not stop the rest
            problems.append(f"{name}/{a['file']}: {exc}")
    if extract and ds.get("extract"):
        print(f"  note    {name}: {ds['extract']}")
    return problems


def run(names: list[str], every: bool = False, listing: bool = False, check: bool = False,
        manifest: str | None = None, root: str | None = None, extract: bool = True) -> int:
    base = Path(root).expanduser() if root else default_root()
    m = load_manifest(Path(manifest) if manifest else None, base)
    if listing or (not names and not every and not check):
        print(f"Manifest: {len(m.get('datasets', []))} datasets. Root: {base}")
        for ds in m.get("datasets", []):
            good, total = status(base, ds)
            print(f"  {ds.get('folder') or ds['name']:<34} {ds.get('access', '?'):<7} {good}/{total} archives here"
                  f"   {ds.get('sax', '')[:70]}")
        return 0
    chosen = pick(m, names, every or check)
    if check:
        bad = 0
        for ds in chosen:
            good, total = status(base, ds, verify=True)
            if good < total:
                bad += 1
            print(f"  {'ok ' if good == total else '-- '} {ds['name']}: {good}/{total} archives present and matching")
        return 1 if bad else 0
    problems = []
    for ds in chosen:
        problems += fetch(base, ds, extract)
    for p in problems:
        print(f"  !! {p}")
    return 1 if any("manual" not in p for p in problems) else 0
