"""Command line.

  Transcribe a solo take (results go in take.saxscribe/ next to the file):
    python -m saxscribe transcribe take.wav

  A sax part inside a full band recording (separates stems first):
    python -m saxscribe transcribe record.mp3 --mix
    python -m saxscribe transcribe record.mp3 --mix --stem piano --redo isolate

  A whole folder of recordings:
    python -m saxscribe transcribe ~/Music/Takes/

  Swung eighths (detected by default; set it if the guess is off):
    python -m saxscribe transcribe solo.mp3 --mix --swing 2 --redo notation

  Remake one layer and everything above it, keeping the ones below:
    python -m saxscribe transcribe take.wav --redo notes

  Score the tool on recordings with known answers (see saxscribe/score):
    python -m saxscribe score omnibook
    python -m saxscribe score omnibook-mix      (the same solos from the full records)
    python -m saxscribe score filosax --split test
    python -m saxscribe score urmp             (classical sax parts, each recorded alone)
    python -m saxscribe score choralebricks    (alto and baritone sax chorale parts)
    python -m saxscribe score bach10           (the sax part of 10 Bach chorales)
    python -m saxscribe score pairs --data ~/Music/Etudes

  Make an answer key for your take of a written etude:
    python -m saxscribe answer-key take.wav etude.musicxml

  Download the datasets in the manifest (see saxscribe/datasets.py):
    python -m saxscribe fetch --list
    python -m saxscribe fetch urmp bach10

  See which tools are installed:
    python -m saxscribe check
"""
from __future__ import annotations

# Load PyTorch before librosa: on some Macs, importing it after numba fails
# halfway (seen in the game analyzer).
try:
    import torch  # noqa: F401
except Exception:
    pass

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

from . import LAYERS
from .horns import HORNS

AUDIO = {".wav", ".aif", ".aiff", ".flac", ".mp3", ".m4a", ".ogg", ".opus"}


def inputs(paths: list[str]) -> list[Path]:
    files = []
    for p in map(lambda s: Path(s).expanduser(), paths):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in AUDIO)
        else:
            files.append(p)
    return files


def swing_arg(text: str) -> str:
    if text in ("auto", "straight"):
        return text
    try:
        if 1.0 <= float(text) <= 4.0:
            return text
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("use auto, straight, or a ratio from 1 to 4 (2 = triplet swing)")


def check() -> int:
    rows = [("ffmpeg", shutil.which("ffmpeg") is not None, "decoding (required)")]
    for mod, use in (("librosa", "audio analysis (required)"), ("mido", "MIDI out (required)"),
                     ("music21", "notation and MusicXML (required)"),
                     ("torch", "runs the neural models"), ("torchcrepe", "pitch contour (else pYIN)"),
                     ("basic_pitch", "note events (else cut from the contour)"),
                     ("beat_this", "beats (else librosa)"), ("demucs", "stems for full mixes")):
        rows.append((mod, importlib.util.find_spec(mod) is not None, use))
    for name, ok, use in rows:
        print(f"  {'ok ' if ok else '-- '} {name:<12} {use}")
    return 0 if all(ok for name, ok, use in rows if "required" in use) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="saxscribe", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe", help="audio in, four layers out")
    t.add_argument("paths", nargs="+", help="audio files or folders of them")
    t.add_argument("-o", "--out", help="output folder (one file only); default: <file>.saxscribe/ next to it")
    t.add_argument("--mix", action="store_true", help="the sax is inside a full band: separate stems first")
    t.add_argument("--stem", help="which Demucs stem holds the sax (default: other)")
    t.add_argument("--horn", choices=sorted(HORNS), default="alto")
    t.add_argument("--redo", choices=LAYERS, help="remake this layer and the ones above it")
    t.add_argument("--contour-tool", choices=("auto", "crepe", "pyin"), default="auto")
    t.add_argument("--notes-tool", choices=("auto", "basic_pitch", "basic_pitch_raw", "segment", "contour"), default="auto")
    t.add_argument("--swing", default="auto", type=swing_arg,
                   help="auto (detect), straight, or a long:short ratio such as 2 or 1.5")
    sub.add_parser("check", help="which tools are installed")

    sc = sub.add_parser("score", help="run a set of recordings with known answers and score each layer")
    sc.add_argument("set", choices=("omnibook", "omnibook-mix", "filosax", "urmp", "urmp-mix", "choralebricks", "bach10", "bach10-mix", "pairs"))
    sc.add_argument("--data", help="dataset folder (default: config.local.toml, then ~/mir_datasets/)")
    sc.add_argument("--split", choices=("all", "train", "test"), default="all")
    sc.add_argument("--limit", type=int, help="only the first N recordings")
    sc.add_argument("--runs", help="where take folders and the scorecard go (default ~/saxscribe-runs)")
    sc.add_argument("--redo", choices=LAYERS)
    sc.add_argument("--contour-tool", choices=("auto", "crepe", "pyin"), default="auto")
    sc.add_argument("--notes-tool", choices=("auto", "basic_pitch", "basic_pitch_raw", "segment", "contour"), default="auto")

    ak = sub.add_parser("answer-key", help="line a written score up with your take of it")
    ak.add_argument("audio")
    ak.add_argument("score", help="MusicXML (or anything music21 reads)")
    ak.add_argument("-o", "--out", help="MIDI file to write (default: next to the audio)")
    ak.add_argument("--horn", choices=sorted(HORNS), default="alto")
    ak.add_argument("--score-pitch", choices=("written", "concert"), default="written",
                    help="is the score written for the horn (default) or at concert pitch")
    fe = sub.add_parser("fetch", help="download, check and unpack datasets from the manifest")
    fe.add_argument("names", nargs="*", help="dataset folders or names (none: list them)")
    fe.add_argument("--all", action="store_true", help="every dataset that can be downloaded directly")
    fe.add_argument("--list", action="store_true", help="what the manifest holds, and what is here")
    fe.add_argument("--check", action="store_true", help="only check files already here against their md5")
    fe.add_argument("--no-extract", action="store_true", help="download only")
    fe.add_argument("--manifest", help="manifest file (default: datasets/manifest.json, then <root>/MANIFEST.json)")
    fe.add_argument("--root", help="where datasets live (default: config.local.toml [data] root, else ~/mir_datasets)")
    args = ap.parse_args(argv)

    if args.cmd == "check":
        return check()
    if args.cmd == "fetch":
        from . import datasets
        return datasets.run(args.names, args.all, args.list, args.check, args.manifest, args.root,
                            not args.no_extract)
    if args.cmd == "score":
        from .score import card
        card.run(args.set, args.data, args.split, args.limit, args.runs, args.contour_tool,
                 args.notes_tool, args.redo)
        return 0
    if args.cmd == "answer-key":
        from .score import align
        align.run(Path(args.audio).expanduser(), Path(args.score).expanduser(),
                  Path(args.out).expanduser() if args.out else None, args.horn,
                  args.score_pitch == "written")
        return 0
    from .pipeline import transcribe
    files = inputs(args.paths)
    if args.out and len(files) != 1:
        ap.error("--out works with one file only")
    failed = 0
    for f in files:
        try:
            transcribe(f, args.out, mix=args.mix, stem=args.stem, horn=args.horn, redo=args.redo,
                       contour_tool=args.contour_tool, notes_tool=args.notes_tool,
                       swing=args.swing)
        except (Exception, SystemExit) as exc:  # keep going through a batch
            if len(files) == 1:
                raise
            print(f"[saxscribe] {f.name} failed: {exc}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
