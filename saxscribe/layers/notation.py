"""Layer 4: notation a sax player can read, plus MIDI that lines up with the audio.

Files:
  score.mid             every note at its exact time (no quantizing), so it
                        lines up with source.wav for loop practice
  score.musicxml        quantized notation at concert pitch
  score-alto.musicxml   the same, written for the horn (E-flat for alto)
  notation.json         what was decided: key, swing, and each note's place
                        in the bar, with its index back into notes.json

How a note gets its place:
  1. Seconds become beats along the beat tracker's grid, so tempo drift and
     rubato follow the band instead of a fixed metronome. Where the tracker
     left gaps (common on a horn with no band), the gaps are filled at the
     tracked beat spacing, and the grid is extended to cover every note.
  2. Swing: the off-beat eighths' average position in the beat gives the
     swing ratio (0.5 is straight, 0.67 is a hard 2:1 triplet swing). Swung
     eighths are written as plain eighths, the way a lead sheet does.
  3. Each beat snaps to sixteenths, or to triplets when they fit clearly better.
  4. Short gaps before the next note (under a third of a beat) are closed,
     so tongued eighths read as eighths, not sixteenths and rests.
  5. No note is ever dropped: two notes that snap to the same spot are
     written a thirty-second apart, and the count is kept in notation.json.
  6. Key comes from the notes (music21's key finder); spelling follows the key,
     with flats for chromatic notes in flat keys and C, sharps in sharp keys.
"""
from __future__ import annotations

import json
from fractions import Fraction

import numpy as np

from .. import frontend
from ..horns import Horn
from ..take import Take
from . import notes as notes_layer

TICKS = 960   # MIDI ticks per beat
BPM = 120.0   # fixed MIDI tempo, so a tick is an exact slice of a second (1/1920 s)

STRAIGHT = (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1))
TRIPLET = (Fraction(0), Fraction(1, 3), Fraction(2, 3), Fraction(1))
TRIPLET_PENALTY = 0.03  # beats of extra error per note before triplets win
CLOSE_GAP = 1 / 3       # beats: shorter gaps before the next note are closed
SWING_MIN_NOTES = 6     # off-beat notes needed before trusting a swing estimate
BEATS_PER_BAR = 4       # 4/4 for now
GAP_FILL = 1.5          # a gap between tracked beats over this many beat spacings is filled
MIN_STEP = Fraction(1, 8)  # beats: two notes on one grid slot are written this far apart


def run(take: Take, horn: Horn, swing: str = "auto") -> None:
    frontend.log("Layer 4/4: notation")
    data = notes_layer.read(take)
    notes = data["notes"]
    write_midi(take.midi, notes)
    result = quantize(notes, data.get("beats") or [], data.get("downbeats") or [],
                      data.get("tempo_bpm"), swing)
    concert = build_score(result, horn, written=False)
    concert.write("musicxml", fp=str(take.musicxml))
    build_score(result, horn, written=True).write("musicxml", fp=str(take.written_musicxml(horn.name)))
    take.notation.write_text(json.dumps(result_json(result), indent=1) + "\n")
    from . import engrave
    pdfs = [pdf.name for xml, pdf in ((take.musicxml, take.pdf),
                                      (take.written_musicxml(horn.name), take.written_pdf(horn.name)))
            if engrave.to_pdf(xml, pdf)]
    if not pdfs and engrave.find_musescore() is None:
        frontend.log("  No PDF: MuseScore is not installed (brew install --cask musescore). MusicXML is written.")
    elif len(pdfs) < 2:
        frontend.log("  Some PDFs were not made (see the MuseScore message above). MusicXML is written.")
    take.record("notation", tool="music21", key=result["key"], swing=result["swing"],
                swing_source=result["swing_source"], pdf=pdfs)
    if result.get("squeezed") or result.get("grid", "tracked") != "tracked":
        frontend.log(f"  beat grid: {result.get('grid')}; {result.get('squeezed', 0)} notes moved off a shared slot")
    frontend.log(f"  {len(result['notes'])} of {len(notes)} notes written in {result['key']}, swing {result['swing']:.2f} "
                 f"({result['swing_source']}); wrote {take.musicxml.name} and "
                 f"{take.written_musicxml(horn.name).name}")


# ---------------------------------------------------------------- time to beats

def repair_grid(beats: list[float], notes: list[dict], tempo_bpm: float | None) -> tuple[list[float], str]:
    """A beat grid that covers every note, with the tracker's gaps filled.

    The beat spacing comes from the tracker's own beats where they sit close
    together (0.25-1.5 s apart); failing that, from tempo_bpm; failing that,
    from the notes (a jazz line is mostly eighths, two to a beat). Tracked
    beats are kept as they are. Returns the grid and a note on what was done.
    """
    b = sorted(float(x) for x in beats)
    diffs = np.diff(b) if len(b) > 1 else np.array([])
    close = diffs[(diffs >= 0.25) & (diffs <= 1.5)]
    if len(close) >= 3:
        spb, source = float(np.median(close)), "tracked"
    elif tempo_bpm and 40 <= tempo_bpm <= 240:
        spb, source = 60.0 / tempo_bpm, "tempo"
    else:
        ioi = np.diff(sorted(n["onset"] for n in notes)) if len(notes) > 2 else np.array([])
        ioi = ioi[(ioi > 0.06) & (ioi < 1.0)]
        spb, source = (float(np.clip(2 * np.median(ioi), 0.3, 1.2)) if len(ioi) else 0.5), "notes"
    if not notes:
        return b, "tracked"
    first, last = min(n["onset"] for n in notes), max(n["offset"] for n in notes)
    if not b:
        b = [first]
    filled, added = [b[0]], 0
    for x in b[1:]:
        gap = x - filled[-1]
        if gap > GAP_FILL * spb:
            k = int(round(gap / spb))
            filled += [filled[-1] + gap * j / k for j in range(1, k)]
            added += k - 1
        filled.append(x)
    while filled[0] > first - spb:
        filled.insert(0, filled[0] - spb)
        added += 1
    while filled[-1] < last + spb:
        filled.append(filled[-1] + spb)
        added += 1
    note = "tracked" if added <= max(2, 0.1 * len(b)) else f"filled {added} beats at {spb:.3f} s ({source})"
    return filled, note


def beat_map(beats: list[float], tempo_bpm: float | None):
    """A function from seconds to beats along the tracked grid, extended past both ends."""
    if len(beats) < 2:
        spb = 60.0 / (tempo_bpm or 120.0)
        return lambda t: np.asarray(t, dtype=float) / spb
    b = np.asarray(beats, dtype=float)
    idx = np.arange(len(b), dtype=float)
    first, last = b[1] - b[0], b[-1] - b[-2]

    def f(t):
        t = np.asarray(t, dtype=float)
        out = np.interp(t, b, idx)
        out = np.where(t < b[0], (t - b[0]) / first, out)
        return np.where(t > b[-1], idx[-1] + (t - b[-1]) / last, out)
    return f


# ---------------------------------------------------------------- swing

def detect_swing(positions: np.ndarray) -> float | None:
    """Where off-beat eighths fall inside the beat (0.5 straight, 0.67 triplet swing).

    Looks at onsets between 40% and 80% of the way through a beat and takes
    their median. Returns None when there are too few to tell.
    """
    frac = positions - np.floor(positions)
    off = frac[(frac > 0.4) & (frac < 0.8)]
    if len(off) < SWING_MIN_NOTES:
        return None
    return float(np.median(off))


def unswing(pos: float, s: float) -> float:
    """Moves a swung off-beat (at s) back to the middle of the beat, stretching the rest to fit."""
    whole = np.floor(pos)
    f = pos - whole
    f = f * 0.5 / s if f < s else 0.5 + (f - s) * 0.5 / (1 - s)
    return float(whole + f)


def swing_setting(swing: str, positions: np.ndarray) -> tuple[float, str]:
    if swing == "straight":
        return 0.5, "set"
    if swing != "auto":
        ratio = float(swing)  # long:short, e.g. 2 for triplet swing
        return ratio / (ratio + 1), "set"
    s = detect_swing(positions)
    if s is None:
        return 0.5, "too few off-beats; straight"
    if s < 0.54:  # within the wobble of straight playing
        return 0.5, "detected straight"
    return min(s, 0.75), "detected"


# ---------------------------------------------------------------- quantizing

def snap_beat(fracs: list[float]) -> tuple[tuple[Fraction, ...], list[Fraction]]:
    """Snaps positions inside one beat to sixteenths, or triplets if clearly better."""
    def fit(grid):
        g = np.array([float(x) for x in grid])
        picks = [grid[int(np.argmin(np.abs(g - f)))] for f in fracs]
        return picks, sum(abs(float(p) - f) for p, f in zip(picks, fracs))
    s_picks, s_err = fit(STRAIGHT)
    t_picks, t_err = fit(TRIPLET)
    if t_err + TRIPLET_PENALTY * len(fracs) < s_err:
        return TRIPLET, t_picks
    return STRAIGHT, s_picks


def quantize(notes: list[dict], beats: list[float], downbeats: list[float],
             tempo_bpm: float | None, swing: str = "auto") -> dict:
    """Notes placed in bars: {key, swing, swing_source, pad, notes: [{index, start, length, pitch}]}.

    start and length are in beats (Fractions) from the start of the first bar.
    """
    beats, grid_note = repair_grid(beats, notes, tempo_bpm)
    if len(beats) >= 2:
        tempo_bpm = round(60.0 / float(np.median(np.diff(beats))), 2)
    to_beat = beat_map(beats, tempo_bpm)
    on = to_beat([n["onset"] for n in notes]) if notes else np.array([])
    off = to_beat([n["offset"] for n in notes]) if notes else np.array([])
    s, source = swing_setting(swing, on)
    if s != 0.5:
        on = np.array([unswing(p, s) for p in on])
        off = np.array([unswing(p, s) for p in off])
    # Close short gaps so tongued notes keep their written length.
    off = off.copy()
    for i in range(len(notes) - 1):
        if on[i + 1] - off[i] < CLOSE_GAP:
            off[i] = on[i + 1]

    # Snap every onset and offset beat by beat, so each beat picks one grid.
    events: dict[int, list[tuple[int, str, float]]] = {}
    for i, (a, b) in enumerate(zip(on, off)):
        for kind, pos in (("on", a), ("off", b)):
            events.setdefault(int(np.floor(pos)), []).append((i, kind, float(pos - np.floor(pos))))
    q_on, q_off = [Fraction(0)] * len(notes), [Fraction(0)] * len(notes)
    for beat, evs in events.items():
        _, picks = snap_beat([f for _, _, f in evs])
        for (i, kind, _), p in zip(evs, picks):
            (q_on if kind == "on" else q_off)[i] = beat + p
    # Every note keeps a place: an onset that landed on or before the previous
    # one moves a thirty-second later (fidelity over tidiness).
    squeezed = 0
    for i in range(1, len(notes)):
        if q_on[i] <= q_on[i - 1]:
            step = Fraction(1, 3) if (q_on[i - 1] % 1).denominator == 3 else MIN_STEP
            q_on[i] = q_on[i - 1] + step
            squeezed += 1
    placed = []
    for i in range(len(notes)):
        start, end = q_on[i], max(q_off[i], q_on[i] + MIN_STEP)
        if end - start < Fraction(1, 4):
            end = start + Fraction(1, 4)  # the smallest value we write by default is a sixteenth
        if i + 1 < len(notes):
            end = min(end, q_on[i + 1])
        placed.append({"index": i, "start": start, "length": end - start, "pitch": notes[i]["pitch"]})
    placed = one_grid_per_beat(placed)

    # Line the bars up with the first downbeat, and start at bar 1.
    first_down = round(float(to_beat([downbeats[0]])[0])) if downbeats else 0
    pad = (-first_down) % BEATS_PER_BAR
    earliest = min((p["start"] for p in placed), default=Fraction(0)) + pad
    shift = pad - BEATS_PER_BAR * (int(np.floor(float(earliest))) // BEATS_PER_BAR)
    for p in placed:
        p["start"] += shift
    return {"key": find_key([n["pitch"] for n in notes]), "swing": s, "swing_source": source,
            "shift": shift, "tempo_bpm": tempo_bpm, "squeezed": squeezed, "grid": grid_note,
            "notes": placed}


def is_triplet(x: Fraction) -> bool:
    return (x % 1).denominator == 3


def one_grid_per_beat(placed: list[dict]) -> list[dict]:
    """Each beat is written in one grid: triplets, or sixteenths and thirty-seconds.

    A beat that mixes the two (from a squeezed note, or a long note that started
    on a triplet) cannot be written cleanly, so its triplet points move to the
    nearest thirty-second. Order is kept and no note is dropped.
    """
    for _ in range(4):
        points: dict[int, list[Fraction]] = {}
        for p in placed:
            for x in (p["start"], p["start"] + p["length"]):
                if x % 1:
                    points.setdefault(int(x // 1), []).append(x)
        mixed = {b for b, xs in points.items()
                 if any(is_triplet(x) for x in xs) and any(not is_triplet(x) for x in xs)}
        if not mixed:
            return placed

        def fix(x: Fraction) -> Fraction:
            if int(x // 1) in mixed and is_triplet(x):
                return Fraction(round(x * 8), 8)
            return x
        ends = [fix(p["start"] + p["length"]) for p in placed]
        starts = [fix(p["start"]) for p in placed]
        for i in range(1, len(starts)):
            if starts[i] <= starts[i - 1]:
                starts[i] = starts[i - 1] + MIN_STEP
        for i, p in enumerate(placed):
            end = max(ends[i], starts[i] + MIN_STEP)
            if i + 1 < len(placed):
                end = min(end, starts[i + 1])
            p["start"], p["length"] = starts[i], end - starts[i]
    return placed


def pieces(start: Fraction, end: Fraction) -> list[tuple[Fraction, Fraction]]:
    """(start, length) pieces of a span, cut at beat lines so no written value
    straddles a beat (a triplet never spills into the next beat). Whole beats
    in a row stay one piece, so a half note is still a half note."""
    cuts = [start]
    b = int(start // 1) + 1
    while b < end:
        cuts.append(Fraction(b))
        b += 1
    cuts.append(end)
    # Join whole-beat runs back up (a half note stays a half note), keep the partial edges.
    out: list[tuple[Fraction, Fraction]] = []
    for a, z in zip(cuts, cuts[1:]):
        whole = a % 1 == 0 and z % 1 == 0
        if out and whole and out[-1][0] % 1 == 0 and (out[-1][0] + out[-1][1]) == a and out[-1][1] % 1 == 0:
            out[-1] = (out[-1][0], out[-1][1] + (z - a))
        else:
            out.append((a, z - a))
    return out


# ---------------------------------------------------------------- key and spelling

def find_key(pitches: list[int]) -> str:
    """music21's key finder on the notes, e.g. "B- major". C major when there is nothing to go on."""
    from music21 import note, stream
    if len(pitches) < 4:
        return "C major"
    s = stream.Stream([note.Note(p, quarterLength=1) for p in pitches])
    k = s.analyze("key")
    return f"{k.tonic.name} {k.mode}"


def spell(midi: int, key_name: str):
    """A music21 Pitch for a MIDI number, spelled to suit the key."""
    from music21 import key as m21key, pitch
    k = m21key.Key(*key_name.split())
    pc = midi % 12
    for sp in k.getPitches():
        if sp.pitchClass == pc:
            p = pitch.Pitch(sp.name)
            break
    else:
        p = pitch.Pitch(midi)
        if k.sharps <= 0 and p.accidental is not None and p.accidental.name == "sharp":
            p = p.getEnharmonic()
        elif k.sharps > 0 and p.accidental is not None and p.accidental.name == "flat":
            p = p.getEnharmonic()
    p.octave = 4
    p.octave += (midi - p.midi) // 12  # B#, Cb and friends sit across an octave line
    assert p.midi == midi, (midi, p)
    return p


# ---------------------------------------------------------------- score

def build_score(result: dict, horn: Horn, written: bool):
    from music21 import interval, key as m21key, meter, metadata, note, stream, tempo
    part = stream.Part()
    part.partName = f"{horn.name.capitalize()} Sax"
    part.insert(0, meter.TimeSignature(f"{BEATS_PER_BAR}/4"))
    part.insert(0, m21key.Key(*result["key"].split()))
    if result.get("tempo_bpm"):
        part.insert(0, tempo.MetronomeMark(number=round(result["tempo_bpm"])))
    # Lay out the whole timeline ourselves, notes and rests, cut at beats, so
    # every written value is a plain note, a dotted note, or a 3:2 triplet.
    from music21 import tie
    t = Fraction(0)
    spans: list[tuple[Fraction, Fraction, int | None]] = []
    for p in result["notes"]:
        if p["start"] > t:
            spans.append((t, p["start"], None))
        spans.append((p["start"], p["start"] + p["length"], p["pitch"]))
        t = p["start"] + p["length"]
    bar_end = Fraction(BEATS_PER_BAR * max(1, -(-t // BEATS_PER_BAR)))
    if t < bar_end:
        spans.append((t, bar_end, None))
    for a, z, pitch in spans:
        bits = pieces(a, z)
        for k, (s, length) in enumerate(bits):
            if pitch is None:
                el = note.Rest(quarterLength=length)
            else:
                el = note.Note(spell(pitch, result["key"]), quarterLength=length)
                if len(bits) > 1:
                    el.tie = tie.Tie("start" if k == 0 else "stop" if k == len(bits) - 1 else "continue")
            part.insert(s, el)
    part = part.makeNotation()
    if written:
        part = part.transpose(interval.Interval(horn.written_interval))
        part.partName = f"{horn.name.capitalize()} Sax in {horn.key}"
    score = stream.Score()
    score.metadata = metadata.Metadata(title="Transcription", composer="saxscribe")
    score.insert(0, part)
    return score



def result_json(result: dict) -> dict:
    return {
        "key": result["key"], "swing": round(result["swing"], 3), "swing_source": result["swing_source"],
        "time_signature": f"{BEATS_PER_BAR}/4", "tempo_bpm": result["tempo_bpm"],
        "beat_shift": str(result["shift"]), "grid": result.get("grid", "tracked"),
        "squeezed": result.get("squeezed", 0),
        "notes": [{"index": p["index"], "bar": int(p["start"] // BEATS_PER_BAR) + 1,
                   "beat": str(p["start"] % BEATS_PER_BAR + 1), "length_beats": str(p["length"]),
                   "pitch": p["pitch"]} for p in result["notes"]],
    }


# ---------------------------------------------------------------- MIDI

def write_midi(path, notes: list[dict]) -> None:
    import mido
    per_second = TICKS * BPM / 60.0
    events = []
    for n in notes:
        vel = int(max(1, min(127, round(40 + 87 * float(n.get("amp", 0.5))))))
        events.append((round(n["onset"] * per_second), 1, n["pitch"], vel))
        events.append((round(n["offset"] * per_second), 0, n["pitch"], 0))
    events.sort(key=lambda e: (e[0], e[1]))  # note-offs before note-ons at the same tick
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    track.append(mido.Message("program_change", program=65, time=0))  # alto sax
    now = 0
    for tick, on, pitch, vel in events:
        track.append(mido.Message("note_on" if on else "note_off", note=pitch, velocity=vel,
                                  time=tick - now))
        now = tick
    mid = mido.MidiFile(ticks_per_beat=TICKS)
    mid.tracks.append(track)
    mid.save(str(path))
