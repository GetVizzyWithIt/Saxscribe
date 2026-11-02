"""Answer keys: a recording plus the notes really played in it.

Sets:
  pairs     any folder of audio files, each with a MIDI file of the same name
            (your aligned etude takes end up like this; see align.py)
  omnibook  the Charlie Parker Aligned Omnibook (Riley & Dixon, Zenodo
            14628467): separated alto stems with aligned MIDI. Read as pairs,
            with looser name matching, since its folder layout is not fixed here.
  filosax   Filosax (Foster & Dixon, ISMIR 2021), through mirdata's loader.
            Solo sax over Aebersold backing tracks, five players.

Dataset folders come from --data, else config.local.toml, else ~/mir_datasets/<Name>.
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

AUDIO = {".wav", ".flac", ".mp3", ".m4a", ".aif", ".aiff", ".ogg"}
MIDI = {".mid", ".midi"}
DEFAULT_DIRS = {"omnibook": "CharlieParkerOmnibook", "filosax": "Filosax", "pairs": "saxscribe-etudes"}
# Words in file names that say what kind of file it is, not which tune.
NOISE = {"sax", "saxophone", "alto", "stem", "stems", "separated", "aligned", "alignment", "midi",
         "audio", "mix", "other", "vocals", "solo", "pitch", "corrected", "440", "a440", "track"}


@dataclass
class Reference:
    id: str
    audio: Path
    notes: list[dict]                      # [{onset, offset, pitch}] in seconds, concert MIDI
    beats: list[float] | None = None
    tune: str = ""
    player: str = ""
    is_mix: bool = False                   # True: the audio still has a band in it
    extra: dict = field(default_factory=dict)


def config() -> dict:
    path = Path(__file__).resolve().parents[2] / "config.local.toml"
    if path.exists():
        return tomllib.loads(path.read_text())
    return {}


def data_dir(set_name: str, override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    configured = config().get("data", {}).get(set_name)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "mir_datasets" / DEFAULT_DIRS[set_name]


# ---------------------------------------------------------------- MIDI

def read_midi_notes(path: Path) -> list[dict]:
    """Notes from a MIDI file, in seconds. With several tracks, the busiest one."""
    import mido
    mid = mido.MidiFile(str(path))
    changes = []  # (tick, tempo) from every track
    for track in mid.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "set_tempo":
                changes.append((tick, msg.tempo))
    changes.sort()

    def seconds(tick: int) -> float:
        t, last, tempo = 0.0, 0, 500000
        for at, new in changes:
            if at >= tick:
                break
            t += mido.tick2second(at - last, mid.ticks_per_beat, tempo)
            last, tempo = at, new
        return t + mido.tick2second(tick - last, mid.ticks_per_beat, tempo)

    best: list[dict] = []
    for track in mid.tracks:
        tick, found, open_notes = 0, [], {}
        for msg in track:
            tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                open_notes[(msg.channel, msg.note)] = tick
            elif msg.type in ("note_off", "note_on"):
                start = open_notes.pop((msg.channel, msg.note), None)
                if start is not None and tick > start:
                    found.append({"onset": seconds(start), "offset": seconds(tick), "pitch": msg.note})
        if len(found) > len(best):
            best = found
    return sorted(best, key=lambda n: n["onset"])


def write_midi_notes(path: Path, notes: list[dict]) -> None:
    from ..layers.notation import write_midi
    write_midi(path, notes)


# ---------------------------------------------------------------- pairs

def key_of(path: Path) -> str:
    words = re.findall(r"[a-z]+|\d+", path.stem.lower())
    return "".join(w for w in words if w not in NOISE)


def find_pairs(folder: Path) -> list[tuple[Path, Path]]:
    """(audio, midi) pairs anywhere under folder, matched by name.

    Exact file names first; then names with words like "sax", "stem" or
    "aligned" taken out; then, within one subfolder, a lone audio file and a
    lone MIDI file.
    """
    files = [p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".")]
    audio = [p for p in files if p.suffix.lower() in AUDIO]
    midi = [p for p in files if p.suffix.lower() in MIDI]
    pairs, used = [], set()
    by_stem = {(m.parent, m.stem): m for m in midi}
    for a in audio:
        m = by_stem.get((a.parent, a.stem))
        if m:
            pairs.append((a, m))
            used |= {a, m}
    by_key: dict[str, list[Path]] = {}
    for m in midi:
        if m not in used:
            by_key.setdefault(key_of(m), []).append(m)
    for a in audio:
        if a in used:
            continue
        cands = by_key.get(key_of(a), [])
        if len(cands) == 1 and cands[0] not in used:
            pairs.append((a, cands[0]))
            used |= {a, cands[0]}
    for d in {p.parent for p in files}:
        la = [a for a in audio if a.parent == d and a not in used]
        lm = [m for m in midi if m.parent == d and m not in used]
        if len(la) == 1 and len(lm) == 1:
            pairs.append((la[0], lm[0]))
    return sorted(pairs)


def load_pairs(folder: Path, is_mix: bool = False) -> list[Reference]:
    refs = []
    for a, m in find_pairs(folder):
        rid = str(a.relative_to(folder).with_suffix("")).replace("/", "__")
        refs.append(Reference(id=rid, audio=a, notes=read_midi_notes(m), tune=key_of(a),
                              is_mix=is_mix, extra={"midi": str(m)}))
    return refs


def load_omnibook(folder: Path) -> list[Reference]:
    """Prefers the separated sax stems: they hold the most even, comparable answer keys."""
    refs = load_pairs(folder)
    stems = [r for r in refs if re.search(r"sax|stem|separated", str(r.audio).lower())]
    chosen = stems or refs
    for r in chosen:
        r.player = "Charlie Parker"
    return chosen


# ---------------------------------------------------------------- Filosax

def load_filosax(folder: Path) -> list[Reference]:
    try:
        import mirdata
    except ImportError as exc:
        raise SystemExit("Filosax needs mirdata: pip install mirdata") from exc
    full = (folder / "Participant_1").exists() or folder.name == "Filosax"
    version = "full_sax" if full else "lite_sax"
    ds = mirdata.initialize("filosax", data_home=str(folder), version=version)
    refs = []
    for tid, track in ds.load_tracks().items():
        if not track.audio_path or not Path(track.audio_path).exists() or not track.notes:
            continue
        notes = [{"onset": float(n.a_start_time), "offset": float(n.a_end_time), "pitch": int(n.midi_pitch)}
                 for n in track.notes if n.midi_pitch and n.a_end_time > n.a_start_time]
        tune = re.sub(r"_?sax.*$", "", tid)
        player = re.search(r"sax_?(\d)", tid)
        refs.append(Reference(id=tid, audio=Path(track.audio_path), notes=notes, tune=tune,
                              player=player.group(1) if player else ""))
    return refs


# ---------------------------------------------------------------- splits

def split_of(ref: Reference) -> str:
    """test for about one tune in five, train otherwise. By tune, never by take,
    so the same tune is never on both sides."""
    h = int(hashlib.md5(ref.tune.encode()).hexdigest(), 16)
    return "test" if h % 5 == 0 else "train"


def load(set_name: str, data: str | None = None, split: str = "all") -> list[Reference]:
    folder = data_dir(set_name, data)
    if not folder.exists():
        raise SystemExit(f"No {set_name} data at {folder}. Pass --data, or set it in config.local.toml.")
    refs = {"pairs": load_pairs, "omnibook": load_omnibook, "filosax": load_filosax}[set_name](folder)
    if split != "all":
        refs = [r for r in refs if split_of(r) == split]
    return refs
