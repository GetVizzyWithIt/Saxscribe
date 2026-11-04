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
  3. Each beat snaps to the plainest grid that fits: eighths first, then
     eighth-note triplets or sixteenths when they fit clearly better. A grid
     that would put two notes on one spot loses. In swing, triplets are read
     from the swung timing and sixteenths cost more, so a swung line reads as
     eighths and triplets, not dotted sixteenths and thirty-seconds.
  4. Short gaps before the next note (under a third of a beat) are closed,
     so tongued eighths read as eighths, not sixteenths and rests.
  5. No note is ever dropped: two notes that snap to the same spot are
     written a thirty-second apart, and the count is kept in notation.json.
  6. Key comes from the notes (music21's key finder). Each part is spelled in
     its own key (the written part in the horn's key, never more than six
     sharps or flats). A note outside the key is spelled the way the line
     moves: sharp going up, flat coming down (F F# G, G Gb F), as
     transcribers write chromatic runs. A note that goes nowhere new (the
     last, or a repeat) keeps the way it came; with neither, the key decides
     (flats in flat keys and C, sharps in sharp keys).
  7. Two or more empty bars in a row are written as one multi-bar rest.
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

EIGHTH = (Fraction(0), Fraction(1, 2), Fraction(1))
STRAIGHT = (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1))
TRIPLET = (Fraction(0), Fraction(1, 3), Fraction(2, 3), Fraction(1))
# Finer grids for slow tunes and ballads, where four to eight notes share a beat:
# sixteenth-note sextuplets and thirty-seconds. Without them a busy beat puts two
# notes on one spot and the later one is pushed into the next slot, so whole runs
# were written late (log E31).
SEXTUPLET = tuple(Fraction(k, 6) for k in range(7))
THIRTY_SECOND = tuple(Fraction(k, 8) for k in range(9))
TRIPLET_FAMILY = (TRIPLET, SEXTUPLET)   # fitted to the time as played, never unswung
FINE = (SEXTUPLET, THIRTY_SECOND)
# The fine grids are offered only on a long beat or a crowded one. At up tempo
# they wrote triplets where the Weimar transcriptions have sixteenths.
FINE_BEAT_SECONDS = 0.6   # a beat this long or longer (100 BPM or slower)
FINE_ONSETS = 5           # or this many notes starting in one beat
PHRASE_SWITCH = 0.4        # beats of cost to change between triplet and plain feel inside a phrase,
PHRASE_SLOW_SECONDS = 0.45  # on beats shorter than this; a slow beat changes feel freely (rubato)
# Beats of extra error per event a grid must save before it wins over eighths.
# Straight playing: sixteenths before triplets. Swing: triplets before sixteenths.
PENALTY = {False: {EIGHTH: 0.0, STRAIGHT: 0.02, TRIPLET: 0.05, SEXTUPLET: 0.07, THIRTY_SECOND: 0.07},
           True: {EIGHTH: 0.0, TRIPLET: 0.02, STRAIGHT: 0.08, SEXTUPLET: 0.07, THIRTY_SECOND: 0.1}}
COLLIDE = 0.25          # beats of cost when a grid puts two onsets on one spot
OFFSET_WEIGHT = 0.5     # note ends matter less than starts when choosing a grid
CLOSE_GAP = 1 / 3       # beats: shorter gaps before the next note are closed
SWING_MIN_NOTES = 6     # off-beat notes needed before trusting a swing estimate
BEATS_PER_BAR = 4       # 4/4 for now
GAP_FILL = 1.5          # a gap between tracked beats over this many beat spacings is filled
NOTES_FOR_TEMPO = 16      # notes needed before the notes may set the beat
PERIOD_STRENGTH = 0.25    # how clearly the notes must repeat once a beat (autocorrelation)
MIN_STEP = Fraction(1, 8)  # beats: two notes on one grid slot are written this far apart
# Krumhansl's major profile from the home note up, with the flat third and
# flat seventh raised and the major seventh lowered: how a blues sounds.
BLUES_PROFILE = np.array([6.35, 2.23, 3.48, 4.0, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 4.0, 2.3])
BLUES_HOME = ["C", "D-", "D", "E-", "E", "F", "G-", "G", "A-", "A", "B-", "B"]  # flat names, as blues charts use


def run(take: Take, horn: Horn, swing: str = "auto") -> None:
    frontend.log("Layer 4/4: notation")
    data = notes_layer.read(take)
    places, notes = notes_layer.played(data["notes"])
    write_midi(take.midi, notes)
    result = quantize(notes, data.get("beats") or [], data.get("downbeats") or [],
                      data.get("tempo_bpm"), swing)
    for p in result["notes"]:
        p["index"] = places[p["index"]]  # back to its place in notes.json
    concert = build_score(result, horn, written=False)
    concert.write("musicxml", fp=str(take.musicxml))
    build_score(result, horn, written=True).write("musicxml", fp=str(take.written_musicxml(horn.name)))
    take.notation.write_text(json.dumps(result_json(result), indent=1) + "\n")
    from . import engrave
    pdfs = [pdf.name for xml, pdf in ((take.musicxml, take.pdf),
                                      (take.written_musicxml(horn.name), take.written_pdf(horn.name)))
            if engrave.to_pdf(xml, pdf)]
    if engrave.turned_off():
        frontend.log("  PDFs turned off ([tools] musescore = \"off\"). MusicXML is written.")
    elif not pdfs and engrave.find_musescore() is None:
        frontend.log("  No PDF: MuseScore is not installed (brew install --cask musescore). MusicXML is written.")
    elif len(pdfs) < 2:
        frontend.log("  Some PDFs were not made (see the MuseScore message above). MusicXML is written.")
    take.record("notation", tool="music21", key=result["key"], swing=result["swing"],
                swing_source=result["swing_source"], pdf=pdfs)
    if result.get("squeezed") or result.get("grid", "tracked") != "tracked":
        frontend.log(f"  beat grid: {result.get('grid')}; {result.get('squeezed', 0)} notes moved off a shared slot")
    frontend.log(f"  {len(result['notes'])} of {len(notes)} sax notes written in {result['key']}, swing {result['swing']:.2f} "
                 f"({result['swing_source']}); wrote {take.musicxml.name} and "
                 f"{take.written_musicxml(horn.name).name}")


# ---------------------------------------------------------------- time to beats

def repair_grid(beats: list[float], notes: list[dict], tempo_bpm: float | None) -> tuple[list[float], str]:
    """A beat grid that covers every note.

    Normally the tracker's beats with its gaps filled (fill_grid). When the
    tracker found too few beats to trust (more of the grid would be filled in
    than tracked, common on a lone horn), and the notes themselves repeat
    clearly once a beat, the grid is built from the notes instead
    (beats_from_notes). Omnibook 7XTyc: Beat This! gave 13 beats in 90 s,
    about 1.5 beats apart, so the line was written at 162 BPM; the notes
    say 261 BPM, and swung eighths then read as eighths.
    """
    filled, note, added, b = fill_grid(beats, notes, tempo_bpm)
    if added > len(b) and len(notes) >= NOTES_FOR_TEMPO:
        spb, strength = onset_period([n["onset"] for n in notes])
        if spb and strength >= PERIOD_STRENGTH:
            grid = beats_from_notes([n["onset"] for n in notes], [n["offset"] for n in notes], spb)
            return grid, (f"from the notes: a beat every {spb:.3f} s ({60 / spb:.0f} BPM); "
                          f"the beat tracker found only {len(b)} beats")
    return filled, note


def onset_period(onsets: list[float]) -> tuple[float | None, float]:
    """The beat length the notes repeat at, and how clearly (0-1).

    Autocorrelation of the onsets (each a 15 ms bump) over 0.2-0.75 s, that
    is 80-300 BPM. The shortest lag within 85% of the best wins, so a line of
    straight eighths gives the beat and not the half-bar."""
    on = np.asarray(sorted(onsets), dtype=float)
    if len(on) < 2:
        return None, 0.0
    rate = 200
    n = int((on[-1] - on[0]) * rate) + 64
    x = np.zeros(n)
    np.add.at(x, ((on - on[0]) * rate).astype(int) + 16, 1.0)
    x = np.convolve(x, np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2), "same")
    spec = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(spec * np.conj(spec))[:n]
    if ac[0] <= 0:
        return None, 0.0
    ac = ac / ac[0]
    lo, hi = int(0.2 * rate), min(int(0.75 * rate), n - 1)
    if hi <= lo:
        return None, 0.0
    window = ac[lo:hi]
    best = float(window.max())
    first = int(np.argmax(window >= 0.85 * best))
    # refine around the chosen peak
    i = lo + first
    while i + 1 < hi and ac[i + 1] > ac[i]:
        i += 1
    return i / rate, best


def beats_from_notes(onsets: list[float], offsets: list[float], spb: float) -> list[float]:
    """Beats that follow the notes: start at the first note, step one beat at a
    time, and lean halfway toward a note that starts close to where the beat
    was expected, so the grid follows the player's drift without jumping. The
    beat length adapts slowly and stays within 10% of spb. If the off-beats
    land before the middle of the beat, the grid sat on the off-beats, and it
    is moved over to the beat."""
    on = np.asarray(sorted(onsets), dtype=float)
    end = max(offsets) if offsets else on[-1]
    grid, period = [float(on[0])], spb
    while grid[-1] < end + spb:
        expect = grid[-1] + period
        near = on[np.abs(on - expect) < 0.2 * period]
        nxt = expect + 0.5 * (float(near[np.argmin(np.abs(near - expect))]) - expect) if len(near) else expect
        period = float(np.clip(0.9 * period + 0.1 * (nxt - grid[-1]), 0.9 * spb, 1.1 * spb))
        grid.append(nxt)
    g = np.asarray(grid)
    pos = np.interp(on, g, np.arange(len(g)))
    frac = pos - np.floor(pos)
    mid = frac[(frac > 0.25) & (frac < 0.75)]
    if len(mid) >= SWING_MIN_NOTES and np.median(mid) < 0.5:
        shift = float(np.median(mid))  # the real beat sits this far into each grid step
        g = np.interp(np.arange(len(g)) + shift, np.arange(len(g)), g, right=np.nan)
        g = g[~np.isnan(g)]
        g = np.concatenate([[g[0] - spb], g, g[-1] + spb * np.arange(1, 3)])
    return [float(x) for x in g]


def fill_grid(beats: list[float], notes: list[dict], tempo_bpm: float | None):
    """The tracker's beats with its gaps filled: (grid, note, beats added, tracked beats).

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
        return b, "tracked", 0, b
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
    return filled, note, added, b


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
    their median. Only beats with one or two onsets count: swing is how a pair
    of eighths is split, and the inner notes of a busy ballad beat (six or
    eight to a beat) would otherwise read as swing. Returns None when there
    are too few to tell.
    """
    whole = np.floor(positions)
    _, where, count = np.unique(whole, return_inverse=True, return_counts=True)
    positions = positions[count[where] <= 2]
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

def step_of(grid: tuple[Fraction, ...]) -> Fraction:
    return grid[1]


def snap_beat(events: list[tuple[str, float, float]], swung: bool = False, fine: bool = False
              ) -> tuple[tuple[Fraction, ...], list[Fraction]]:
    """Snaps the events inside one beat to one grid: eighths, sixteenths or triplets,
    and when fine (a long or crowded beat) also sextuplets or thirty-seconds.

    events are (kind, straight position, as-played position) with kind "on" or
    "off". Eighths and sixteenths are fitted to the straightened position,
    triplets to the position as played (so swing does not bend a triplet).
    The cheapest grid wins: its error, plus a small cost per event for a busier
    grid, plus a large cost for each pair of onsets it would put on one spot.
    In swing, a beat is only a triplet when a note starts on its middle third:
    notes on the first and last thirds are just swung eighths.
    """
    options = beat_options(events, swung, fine)
    best = min(options, key=lambda o: o[0])
    return best[1], best[2]


def beat_options(events: list[tuple[str, float, float]], swung: bool = False, fine: bool = False
                 ) -> list[tuple[float, tuple[Fraction, ...], list[Fraction]]]:
    """Every grid a beat may take, as (cost, grid, picks, onset picks), in PENALTY order (see snap_beat)."""
    options = []
    for grid, penalty in PENALTY[swung].items():
        if grid in FINE and not fine:
            continue
        g = np.array([float(x) for x in grid])
        picks, cost = [], 0.0
        for kind, straight, played in events:
            f = played if grid in TRIPLET_FAMILY else straight
            pick = grid[int(np.argmin(np.abs(g - f)))]
            picks.append(pick)
            cost += abs(float(pick) - f) * (1.0 if kind == "on" else OFFSET_WEIGHT) + penalty
        ons = [p for (kind, _, _), p in zip(events, picks) if kind == "on"]
        if swung and grid is TRIPLET and Fraction(1, 3) not in ons:
            continue
        cost += COLLIDE * (len(ons) - len(set(ons)))
        options.append((cost, grid, picks, ons))
    return options


def feel_of(grid: tuple[Fraction, ...], onsets: list[Fraction]) -> str | None:
    """"triplet" or "plain" for a beat as written; None when every note starts on
    the beat, which reads the same in either feel (where a note ends does not
    set the feel)."""
    if all(p % 1 == 0 for p in onsets):
        return None
    return "triplet" if grid in TRIPLET_FAMILY else "plain"


def choose_grids(options: dict[int, list], switch: float | dict[int, float]) -> dict[int, tuple]:
    """One grid per beat, chosen per phrase: the cheapest path through the beats
    (Viterbi), where changing between triplet and plain feel from one beat to
    the next costs `switch` beats of error. A beat with no notes ends the
    phrase, so a new phrase starts free. switch = 0 is the old beat-by-beat pick;
    a dict gives each beat its own cost of changing feel on the way into it."""
    chosen: dict[int, tuple] = {}
    beats = sorted(options)
    k = 0
    while k < len(beats):
        run = [beats[k]]
        while k + 1 < len(beats) and beats[k + 1] == run[-1] + 1:
            k += 1
            run.append(beats[k])
        k += 1
        # Viterbi over the run. State = option index; the feel carried forward
        # is the last beat's feel that was not neutral.
        cost = [o[0] for o in options[run[0]]]
        feel = [feel_of(o[1], o[3]) for o in options[run[0]]]
        back: list[list[int]] = []
        for b in run[1:]:
            fee = switch.get(b, 0.0) if isinstance(switch, dict) else switch
            new_cost, new_feel, ptr = [], [], []
            for o in options[b]:
                f = feel_of(o[1], o[3])
                best = None
                for j, c in enumerate(cost):
                    step = c + (fee if f and feel[j] and f != feel[j] else 0.0)
                    if best is None or step < best[0] - 1e-12:
                        best = (step, j)
                new_cost.append(best[0] + o[0])
                new_feel.append(f or feel[best[1]])
                ptr.append(best[1])
            cost, feel = new_cost, new_feel
            back.append(ptr)
        j = int(np.argmin(cost))
        for b, ptr in zip(reversed(run), reversed([None] + back)):
            chosen[b] = options[b][j]
            if ptr is not None:
                j = ptr[j]
    return chosen


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
    off = off.copy()
    # Close short gaps so tongued notes keep their written length.
    for i in range(len(notes) - 1):
        if on[i + 1] - off[i] < CLOSE_GAP:
            off[i] = on[i + 1]
    on_played, off_played = on.copy(), off.copy()
    if s != 0.5:
        on = np.array([unswing(p, s) for p in on])
        off = np.array([unswing(p, s) for p in off])

    # Snap every onset and offset beat by beat, so each beat picks one grid.
    events: dict[int, list[tuple[int, str, float, float]]] = {}
    for i in range(len(notes)):
        for kind, pos, played in (("on", on[i], on_played[i]), ("off", off[i], off_played[i])):
            beat = int(np.floor(pos))
            events.setdefault(beat, []).append((i, kind, float(pos - beat), float(played - beat)))
    q_on, q_off = [Fraction(0)] * len(notes), [Fraction(0)] * len(notes)
    step: dict[int, Fraction] = {}  # each beat's grid step: 1/2, 1/3 or 1/4
    options, fees = {}, {}
    for beat, evs in events.items():
        seconds = beats[beat + 1] - beats[beat] if 0 <= beat < len(beats) - 1 else 60.0 / (tempo_bpm or 120.0)
        fees[beat] = PHRASE_SWITCH if seconds < PHRASE_SLOW_SECONDS else 0.0
        fine = seconds >= FINE_BEAT_SECONDS or sum(k == "on" for _, k, _, _ in evs) >= FINE_ONSETS
        options[beat] = beat_options([(k, f, pf) for _, k, f, pf in evs], swung=s != 0.5, fine=fine)
    chosen = choose_grids(options, fees)
    for beat, evs in events.items():
        _, grid, picks, _ = chosen[beat]
        step[beat] = step_of(grid)
        for (i, kind, _, _), p in zip(evs, picks):
            (q_on if kind == "on" else q_off)[i] = beat + p
    # Every note keeps a place: an onset that landed on or before the previous
    # one moves a thirty-second later (fidelity over tidiness).
    squeezed = 0
    for i in range(1, len(notes)):
        if q_on[i] <= q_on[i - 1]:
            prev = step.get(int(q_on[i - 1] // 1), MIN_STEP)
            move = prev if is_triplet(q_on[i - 1]) and prev in (Fraction(1, 3), Fraction(1, 6)) else MIN_STEP
            q_on[i] = q_on[i - 1] + move
            squeezed += 1
    placed = []
    for i in range(len(notes)):
        start, end = q_on[i], max(q_off[i], q_on[i] + MIN_STEP)
        # The shortest value written by default is one step of the beat's grid
        # (an eighth, a triplet eighth or a sixteenth), so a short note is not
        # written as a sixteenth and a rest.
        least = step.get(int(start // 1), Fraction(1, 4))
        if (start % 1) % least:
            least = Fraction(1, 6) if is_triplet(start) and (start % 1).denominator == 6 else \
                Fraction(1, 3) if is_triplet(start) else Fraction(1, 4)
        if end - start < least:
            end = start + least
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
    return {"key": find_key([n["pitch"] for n in notes],
                                [n["offset"] - n["onset"] for n in notes]), "swing": s, "swing_source": source,
            "shift": shift, "tempo_bpm": tempo_bpm, "squeezed": squeezed, "grid": grid_note,
            "notes": placed}


def is_triplet(x: Fraction) -> bool:
    """A point on the triplet or sextuplet grid (and not on the plain one)."""
    return (x % 1).denominator in (3, 6)


def on_grid(x: Fraction) -> bool:
    """A spot MuseScore can write without odd tuplets: a 32nd-note point, or a triplet or sextuplet point."""
    d = (x % 1).denominator
    return d in (3, 6) or 8 % d == 0


def one_grid_per_beat(placed: list[dict]) -> list[dict]:
    """Each beat is written in one grid: triplets or sextuplets, or sixteenths and thirty-seconds.

    A beat that mixes the two (from a squeezed note, or a long note that started
    on a triplet), or holds a point on neither grid (a squeeze after a triplet
    point lands on 11/24 of a beat, which would need a 6:5 or 12:7 tuplet), is
    moved to sixteenths. Order is kept and no note is dropped. If a few passes
    do not settle it, every point goes to the 32nd grid, which always works.
    """
    for attempt in range(5):
        points: dict[int, list[Fraction]] = {}
        for p in placed:
            for x in (p["start"], p["start"] + p["length"]):
                if x % 1:
                    points.setdefault(int(x // 1), []).append(x)
        # A beat with triplet or sextuplet points is written as a sextuplet at
        # finest, so every point in it must sit on the sixth-of-a-beat grid.
        mixed = {b for b, xs in points.items()
                 if any(not on_grid(x) for x in xs)
                 or (any(is_triplet(x) for x in xs) and any((x * 6).denominator != 1 for x in xs))}
        if not mixed:
            return placed
        last = attempt == 4

        def fix(x: Fraction) -> Fraction:
            if last or int(x // 1) in mixed and (is_triplet(x) or not on_grid(x)):
                return Fraction(round(x * 4), 4) if not last else Fraction(round(x * 8), 8)
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


def pieces(start: Fraction, end: Fraction, sixths: frozenset = frozenset()) -> list[tuple[Fraction, Fraction]]:
    """(start, length) pieces of a span, cut at beat lines so no written value
    straddles a beat (a triplet never spills into the next beat). Whole beats
    in a row stay one piece, so a half note is still a half note. sixths
    holds the beats written as sextuplets (see triplet_pieces)."""
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
    return syncopate([bit for a, n in out for bit in triplet_pieces(a, n, int(a // 1) in sixths)])


def triplet_pieces(start: Fraction, length: Fraction, sextuplet: bool = False) -> list[tuple[Fraction, Fraction]]:
    """A piece inside a triplet or sextuplet beat, cut so each value is one
    3:2 value: in a triplet beat, triplet eighths and quarters; in a
    sextuplet beat, triplet sixteenths only, so the brackets close every half
    beat. Without the cut a span of five sixths would need a 6:5 tuplet, which
    MuseScore will not read."""
    end = start + length
    if not sextuplet and (start % 1).denominator not in (3, 6) and (end % 1).denominator not in (3, 6):
        return [(start, length)]
    if length >= 1 and start % 1 == 0:
        return [(start, length)]
    third = Fraction(1, 6) if sextuplet else Fraction(1, 3)
    cuts = [start] + [k * third for k in range(int(start // third) + 1, int(-(-end // third)))] + [end]
    bits = [(x, y - x) for x, y in zip(cuts, cuts[1:]) if y > x]
    out: list[tuple[Fraction, Fraction]] = []
    for x, n in bits:
        if not sextuplet and out and out[-1][1] == third and n == third and (out[-1][0] % 1) in (0, third):
            out[-1] = (out[-1][0], 2 * third)   # two triplet eighths on the beat or its first third: a triplet quarter
        else:
            out.append((x, n))
    return out


def syncopate(bits: list[tuple[Fraction, Fraction]]) -> list[tuple[Fraction, Fraction]]:
    """Joins the first two pieces of a tied note into one value where a chart
    would: an off-beat eighth tied into the next beat becomes a syncopated
    quarter or dotted quarter (eighth-quarter-eighth), and a quarter tied to
    an eighth on the beat becomes a dotted quarter. Only inside one half of
    the bar, so the middle of the bar stays visible."""
    if len(bits) < 2:
        return bits
    (s, first), (b, second) = bits[0], bits[1]
    total = first + second
    if b % 1 or second not in (Fraction(1, 2), Fraction(1)):
        return bits
    offbeat = s % 1 == Fraction(1, 2) and first == Fraction(1, 2) and total in (Fraction(1), Fraction(3, 2))
    onbeat = s % 1 == 0 and first == 1 and second == Fraction(1, 2)
    if not (offbeat or onbeat):
        return bits
    half = BEATS_PER_BAR // 2
    end = s + total
    inner = range(int(s // 1) + 1, int(-(-end // 1)))  # beat lines strictly inside
    if any(x % half == 0 for x in inner):
        return bits
    return [(s, total)] + bits[2:]


# ---------------------------------------------------------------- key and spelling

def find_key(pitches: list[int], lengths: list[float] | None = None) -> str:
    """The key of the notes, e.g. "B- major". C major when there is nothing to go on.

    music21's key finder (Krumhansl profiles), with each note weighted by how
    long it sounds. Blues fools it: the flat third and seventh and the IV chord
    make a blues in C look like F major. So the notes are also matched against
    a blues profile (the major profile with the flat third and seventh as
    strong as the third, and the major seventh weak); when that fits better,
    its home note wins, written as a major key the way blues charts are. On
    the 429 Weimar Jazz Database solos this names the home note right for 60%
    of solos against 49% for music21 alone (70% against 47% on the 92
    twelve-bar blues). Keeping music21's minor keys was tried and was worse
    overall (58%).
    """
    from music21 import note, stream
    if len(pitches) < 4:
        return "C major"
    if lengths is None:
        lengths = [1.0] * len(pitches)
    lengths = [min(max(float(x), 0.05), 4.0) for x in lengths]
    s = stream.Stream([note.Note(p, quarterLength=round(x, 3)) for p, x in zip(pitches, lengths)])
    best = s.analyze("key")
    heard = np.zeros(12)
    for p, x in zip(pitches, lengths):
        heard[p % 12] += x
    fit = [np.corrcoef(heard, np.roll(BLUES_PROFILE, t))[0, 1] for t in range(12)]
    home = int(np.argmax(fit))
    if fit[home] > best.correlationCoefficient and home != best.tonic.pitchClass:
        from music21 import key as m21key
        k = m21key.Key(BLUES_HOME[home])
        return f"{k.tonic.name} major"
    return f"{best.tonic.name} {best.mode}"


def display_key(key_name: str, horn: Horn | None = None) -> str:
    """The key a part is written in: the concert key, or the horn's written key.

    Never more than six sharps or flats: G# major becomes A- major."""
    from music21 import interval, key as m21key
    k = m21key.Key(*key_name.split())
    if horn is not None:
        k = k.transpose(interval.Interval(horn.written_interval))
    if abs(k.sharps) > 6:
        k = m21key.Key(k.tonic.getEnharmonic().name, k.mode)
    return f"{k.tonic.name} {k.mode}"


def spell(midi: int, key_name: str, rising: bool | None = None):
    """A music21 Pitch for a MIDI number, spelled to suit the key.

    A note outside the key is spelled the way it moves, as players and
    transcribers write it: sharp on the way up (F F# G), flat on the way down
    (G Gb F). rising=None (a repeated or last note) falls back to the key:
    flats in flat keys and C, sharps in sharp keys."""
    from music21 import key as m21key, pitch
    k = m21key.Key(*key_name.split())
    pc = midi % 12
    for sp in k.getPitches():
        if sp.pitchClass == pc:
            p = pitch.Pitch(sp.name)
            break
    else:
        p = pitch.Pitch(midi)
        want_sharp = rising if rising is not None else k.sharps > 0
        if not want_sharp and p.accidental is not None and p.accidental.name == "sharp":
            p = p.getEnharmonic()
        elif want_sharp and p.accidental is not None and p.accidental.name == "flat":
            p = p.getEnharmonic()
    p.octave = 4
    p.octave += (midi - p.midi) // 12  # B#, Cb and friends sit across an octave line
    assert p.midi == midi, (midi, p)
    return p


# ---------------------------------------------------------------- score

def build_score(result: dict, horn: Horn, written: bool):
    from music21 import key as m21key, meter, metadata, note, spanner, stream, tempo, tie
    part = stream.Part()
    part.partName = f"{horn.name.capitalize()} Sax" + (f" in {horn.key}" if written else "")
    # Each part is spelled in its own key, so the written part never inherits
    # odd spellings from transposing the concert one.
    key_name = display_key(result["key"], horn if written else None)
    shift = horn.written_shift if written else 0
    part.insert(0, meter.TimeSignature(f"{BEATS_PER_BAR}/4"))
    part.insert(0, m21key.Key(*key_name.split()))
    if result.get("tempo_bpm"):
        part.insert(0, tempo.MetronomeMark(number=round(result["tempo_bpm"])))
    # Lay out the whole timeline ourselves, notes and rests, cut at beats, so
    # every written value is a plain note, a dotted note, or a 3:2 triplet.
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
    pitched = [x[2] for x in spans if x[2] is not None]
    way = {}  # each pitched span's direction, for spelling: where it goes, else where it came from
    j = 0
    for i, (_, _, pitch) in enumerate(spans):
        if pitch is not None:
            after = pitched[j + 1] if j + 1 < len(pitched) else None
            before = pitched[j - 1] if j > 0 else None
            if after is not None and after != pitch:
                way[i] = after > pitch
            elif before is not None and before != pitch:
                way[i] = pitch > before
            else:
                way[i] = None
            j += 1
    sixths = frozenset(int(x // 1) for a, z, _ in spans for x in (a, z) if (x % 1).denominator == 6)
    for i, (a, z, pitch) in enumerate(spans):
        bits = pieces(a, z, sixths)
        for k, (s, length) in enumerate(bits):
            if pitch is None:
                el = note.Rest(quarterLength=length)
            else:
                el = note.Note(spell(pitch + shift, key_name, way[i]), quarterLength=length)
                if len(bits) > 1:
                    el.tie = tie.Tie("start" if k == 0 else "stop" if k == len(bits) - 1 else "continue")
            part.insert(s, el)
    part = part.makeNotation()
    for run in empty_bar_runs(part):
        rests = [m.notesAndRests.first() for m in run]
        part.insert(0, spanner.MultiMeasureRest(rests, useSymbols=False))
    from .ranges import mark_unplayable
    mark_unplayable(part, horn, shift)  # notes kept as heard but outside the horn's range show red
    score = stream.Score()
    score.metadata = metadata.Metadata(title="Transcription", composer="saxscribe")
    score.insert(0, part)
    return score


def empty_bar_runs(part, least: int = 2) -> list[list]:
    """Runs of at least `least` bars in a row that hold only rests."""
    runs, now = [], []
    for m in part.getElementsByClass("Measure"):
        if not m.notes:
            now.append(m)
            continue
        if len(now) >= least:
            runs.append(now)
        now = []
    if len(now) >= least:
        runs.append(now)
    return runs


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
