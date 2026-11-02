"""Answer keys: a recording plus the notes really played in it.

Sets:
  pairs     any folder of audio files, each with a MIDI file of the same name
            (your aligned etude takes end up like this; see align.py)
  omnibook  the Charlie Parker Aligned Omnibook (Riley & Dixon, Zenodo
            14628467): separated alto stems with performance-aligned MIDI
  omnibook-mix  the same solos, from the full records (separated by Demucs first)
  filosax   Filosax (Foster & Dixon, ISMIR 2021), through mirdata's loader.
            Solo sax over Aebersold backing tracks, five players.
  urmp      URMP (Li et al., Rochester 2018; Dryad doi:10.5061/dryad.ng3r749, CC0):
            the 11 sax parts from 10 classical ensemble pieces, each recorded
            alone, with hand-checked notes
  urmp-mix  the same sax parts, scored from the whole ensemble's mix
  choralebricks  ChoraleBricks (Balke et al., AudioLabs Erlangen; Zenodo 20849469,
            CC BY): 20 alto and 18 baritone sax parts of 10 chorales, each
            recorded alone, with hand-checked notes

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
DEFAULT_DIRS = {"omnibook": "CharlieParkerOmnibook", "omnibook-mix": "CharlieParkerOmnibook", "filosax": "Filosax", "urmp": "URMP", "urmp-mix": "URMP", "choralebricks": "ChoraleBricks", "pairs": "saxscribe-etudes"}
# Words in file names that say what kind of file it is, not which tune.
NOISE = {"fine", "sax", "saxophone", "alto", "stem", "stems", "separated", "aligned", "alignment", "midi",
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


def omnibook_root(folder: Path) -> Path:
    """The folder holding audio_stems/, even with the zip's wrapping folder in between."""
    for cand in (folder, *sorted(p for p in folder.iterdir() if p.is_dir() and not p.name.startswith("__"))):
        if (cand / "audio_stems").is_dir():
            return cand
    raise SystemExit(f"No audio_stems/ folder in {folder} or just inside it.")


def load_omnibook(folder: Path, mix: bool = False) -> list[Reference]:
    """The Charlie Parker Aligned Omnibook, by its file IDs.

    Layout: audio_stems/<id>.wav (separated sax, tuned to A=440),
    audio_untuned_mixes/<id>.mp3 (the records), and
    midi_performance_aligned/<id>-fine-aligned.mid (the answer key, in
    performance time). midi_original/ is the score, not the performance, so it
    is not used. The 4 solos without aligned MIDI are skipped.

    mix=True scores the full records instead of the stems (set
    omnibook-mix). The records keep their original tuning, so a pitch tool
    that does not allow for tuning may lose notes that sit near a quarter tone.
    """
    root = omnibook_root(folder)
    refs = []
    for midi in sorted((root / "midi_performance_aligned").glob("*-fine-aligned.mid")):
        rid = midi.name.removesuffix("-fine-aligned.mid")
        audio = (root / "audio_untuned_mixes" / f"{rid}.mp3") if mix else (root / "audio_stems" / f"{rid}.wav")
        if not audio.exists():
            continue
        refs.append(Reference(id=rid, audio=audio, notes=read_midi_notes(midi), tune=rid,
                              player="Charlie Parker", is_mix=mix, extra={"midi": str(midi)}))
    return refs


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


# ---------------------------------------------------------------- URMP

def hz_to_midi(hz: float) -> int:
    import math
    return int(round(69 + 12 * math.log2(hz / 440.0)))


def read_urmp_notes(path: Path) -> list[dict]:
    """URMP Notes_*.txt: one note per line, onset (s), frequency (Hz), duration (s)."""
    notes = []
    for line in path.read_text().splitlines():
        cols = line.replace(",", " ").split()
        try:
            onset, hz, dur = (float(c) for c in cols[:3])
        except ValueError:
            continue  # a header line
        if hz > 0 and dur > 0:
            notes.append({"onset": onset, "offset": onset + dur, "pitch": hz_to_midi(hz)})
    return sorted(notes, key=lambda n: n["onset"])


def urmp_root(folder: Path) -> Path:
    """The folder holding the numbered piece folders (the tar wraps them in Dataset/)."""
    for cand in (folder, folder / "Dataset", *sorted(p for p in folder.iterdir() if p.is_dir())):
        if cand.is_dir() and any(cand.glob("[0-9][0-9]_*")):
            return cand
    raise SystemExit(f"No URMP piece folders (01_Jupiter_vn_vc ...) in {folder}.")


def load_urmp(folder: Path, mix: bool = False) -> list[Reference]:
    """URMP sax parts. Layout per piece folder <NN>_<Piece>_<inst>_<inst>...:
    AuSep_<n>_sax_<NN>_<Piece>.wav (that player alone), Notes_<n>_sax_... .txt
    (the answer key) and F0s_<n>_sax_... .txt (pitch line, kept in extra),
    plus AuMix_<NN>_<Piece>.wav, the whole ensemble.

    mix=True scores the ensemble mix instead (set urmp-mix). The other parts
    are often winds too (flute, oboe, clarinet, trumpet), which a stem
    splitter lumps in with the sax, so expect lower scores there.
    """
    root = urmp_root(folder)
    refs = []
    for piece in sorted(p for p in root.iterdir() if p.is_dir() and re.match(r"\d\d_", p.name)):
        for notes_file in sorted(piece.glob("Notes_*_sax_*.txt")):
            tag = notes_file.stem.removeprefix("Notes_")           # 1_sax_06_Entertainer
            stem = piece / f"AuSep_{tag}.wav"
            mix_file = piece / f"AuMix_{piece.name}.wav"
            audio = mix_file if mix else stem
            if not audio.exists():
                continue
            f0 = piece / f"F0s_{tag}.txt"
            refs.append(Reference(id=f"{piece.name}__{tag.split('_')[0]}", audio=audio,
                                  notes=read_urmp_notes(notes_file), tune=piece.name.split("_")[1],
                                  is_mix=mix, extra={"notes": str(notes_file),
                                                     "f0": str(f0) if f0.exists() else None}))
    return refs


# ---------------------------------------------------------------- ChoraleBricks

SAX_CODES = {"as": "alto", "bs": "baritone", "ts": "tenor", "ss": "soprano"}


def read_choralebricks_notes(path: Path) -> list[dict]:
    """annotations/NN_inst_notes.csv: start_sec;end_sec;...;pitch;... with pitch the
    sounding (concert) MIDI note. pitch_written is the score's note, never used."""
    import csv
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    notes = [{"onset": float(r["start_sec"]), "offset": float(r["end_sec"]), "pitch": int(round(float(r["pitch"])))}
             for r in rows if r.get("pitch") not in (None, "")]
    return sorted((n for n in notes if n["offset"] > n["onset"]), key=lambda n: n["onset"])


def choralebricks_root(folder: Path) -> Path:
    for cand in (folder, folder / "01_AudioAndAnnotations", *sorted(p for p in folder.iterdir() if p.is_dir())):
        if cand.is_dir() and any(cand.glob("*/annotations")):
            return cand
    raise SystemExit(f"No ChoraleBricks chorale folders (<Composer>_<Title>/annotations) in {folder}.")


def load_choralebricks(folder: Path) -> list[Reference]:
    """Sax parts of ChoraleBricks. Layout per chorale <Composer>_<Title>/:
    tracks/NN_inst.wav (real recording of one part; NN = 01 soprano .. 04 bass voice)
    and annotations/NN_inst_notes.csv (the answer key). Only sax codes are used
    (as alto, bs baritone; ts and ss if a later version adds them). The raw
    recordings in tracks/ are used, not tracks_normalized/.
    """
    root = choralebricks_root(folder)
    refs = []
    for song in sorted(p for p in root.iterdir() if (p / "annotations").is_dir()):
        for notes_file in sorted((song / "annotations").glob("*_notes.csv")):
            tag = notes_file.name.removesuffix("_notes.csv")      # 01_as
            code = tag.split("_", 1)[-1]
            if code not in SAX_CODES:
                continue
            audio = song / "tracks" / f"{tag}.wav"
            if not audio.exists():
                continue
            f0 = song / "annotations" / f"{tag}_f0_filled.csv"
            refs.append(Reference(id=f"{song.name}__{tag}", audio=audio, notes=read_choralebricks_notes(notes_file),
                                  tune=song.name, extra={"horn": SAX_CODES[code], "notes": str(notes_file),
                                                         "f0": str(f0) if f0.exists() else None}))
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
    loaders = {"pairs": load_pairs, "omnibook": load_omnibook, "filosax": load_filosax,
               "omnibook-mix": lambda f: load_omnibook(f, mix=True),
               "urmp": load_urmp, "urmp-mix": lambda f: load_urmp(f, mix=True),
               "choralebricks": load_choralebricks}
    refs = loaders[set_name](folder)
    if split != "all":
        refs = [r for r in refs if split_of(r) == split]
    return refs
