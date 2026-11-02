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
    t.add_argument("--notes-tool", choices=("auto", "basic_pitch", "contour"), default="auto")
    t.add_argument("--swing", default="auto", type=swing_arg,
                   help="auto (detect), straight, or a long:short ratio such as 2 or 1.5")
    sub.add_parser("check", help="which tools are installed")
    args = ap.parse_args(argv)

    if args.cmd == "check":
        return check()
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
