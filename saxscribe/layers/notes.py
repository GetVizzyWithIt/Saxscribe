"""Layer 3: note events, plus the beat grid.

notes.json holds:
  notes      [{onset, offset, pitch, cents, amp, tags}] in seconds and concert
             MIDI numbers. cents is how far the pitch line sat from that note
             (median over the note, +30 = 30 cents sharp). tags is for
             articulations (slur, scoop, fall, ...). On a band record, notes
             found where the sax lays out (piano or bass solo, drum break; see
             isolate.sax_spans), or that the sax's pitch line does not back up
             (bleed.py: no_pitch_line, off_line), are tagged "not_sax": kept
             here, left off the score and the scorecard.
  beats, downbeats, tempo_bpm   from the full source, so a band's groove counts
  key        not filled in yet (step 2)

One line (one_line): Basic Pitch hears every instrument, so its notes are made
one line for a single horn. A note that starts while a held note rings ends the
held note, unless the pitch line shows the horn still holding: then the held
note keeps going and the note under it is kept, tagged "under_held" (on a band
record it is usually a piano or bass attack, and the bleed check hides it).

Range rules (ranges.py, --range-rules): every note is checked against the
horn's range. A note no sax can play is moved by octaves into range, with its
first pitch kept as "detected_pitch"; altissimo notes and possible overtones
are tagged. Nothing is removed.

Note tools (--notes-tool):
  basic_pitch  Spotify's Basic Pitch on the stem (the default when installed).
               Its shortest note follows the take's own note spacing
               (frontend.basic_pitch_notes). basic_pitch_raw is the same thing,
               kept as an older name.
  basic_pitch_fixed  Basic Pitch with a fixed 50 ms shortest note (the
               default before 2026-11-03).
  basic_pitch_join  Basic Pitch, then same-pitch neighbours joined where the
               stem shows no re-articulation. Off by default: on URMP and
               Bach10 it merged real repeated notes (note F1 -1.6 and -10.4).
  segment      the pitch line cut into notes after the CREPE Notes method (segment.py)
  contour      a simpler cutter on the pitch line: a new note wherever the pitch
               settles somewhere new or the stem has a clear new attack
  filosax      Riley and Dixon's sax transcriber (filosax.py), made one line
               like Basic Pitch. It was trained to stay quiet where no sax
               plays, so the sax-rest and bleed checks are skipped: on the
               Weimar solos they cost it 10 points of note F1 (76.3 -> 66.4).
"""
from __future__ import annotations

import json

import numpy as np

from .. import LAYOUT_VERSION, frontend
from ..horns import Horn
from ..take import Take
from . import contour as contour_layer

NOT_SAX = "not_sax"  # tag for notes found where the sax is not playing
SAME_START = 0.03  # two notes starting closer than this are one attack
UNDER_HELD = "under_held"  # a note that starts under a held note the pitch line stays on
HELD_VOICED = 0.8  # share of the later note's frames the pitch line must be voiced for
HELD_ON = 0.5  # share of those frames on the held note's pitch (or its octave)
EDGE = 0.02  # s skipped at each end of a note when reading the pitch line


def run(take: Take, horn: Horn, tool: str = "auto", range_rules: str = "out") -> None:
    frontend.log("Layer 3/4: note events and beats")
    from . import segment
    line = contour_layer.read(take.contour)
    extra = {}

    def stem_envelopes():
        y = frontend.load_mono(take.stem, sr=contour_layer.RATE)
        return segment.envelopes(y, contour_layer.RATE, len(line["time"]))

    basic = ("auto", "basic_pitch", "basic_pitch_raw", "basic_pitch_join", "basic_pitch_fixed")
    if tool in basic and frontend.basic_pitch_available():
        info = {}
        notes = one_line(frontend.basic_pitch_notes(take.stem, horn.min_hz, horn.max_hz,
                                                    by_spacing=tool != "basic_pitch_fixed", info=info), line)
        extra.update(info)
        name = tool if tool in ("basic_pitch_join", "basic_pitch_fixed") else "basic_pitch"
        if name == "basic_pitch_join":
            notes, extra["joined"] = segment.join_repeats(notes, *stem_envelopes())
    elif tool in basic:
        raise SystemExit("Basic Pitch is not installed; use --notes-tool segment or install it.")
    elif tool == "filosax":
        from .. import filosax
        which = filosax.finder()
        notes, name = one_line(filosax.transcribe(take.stem), line), "filosax"
        extra["weights"] = filosax.WEIGHTS[which].get("name", "filosax_25k")
        extra["weights_sha256"] = filosax.WEIGHTS[which]["sha256"]
    elif tool == "segment":
        notes, name = segment.segment(line, *stem_envelopes()), "segment"
    else:
        onsets = frontend.detect_onsets(frontend.load_mono(take.stem))
        notes, name = from_contour(line, onsets), "contour"
    for n in notes:
        n["cents"] = cents_off(line, n)
        n["tags"] = [UNDER_HELD] if n.pop(UNDER_HELD, False) else []
    if take.read_manifest().get("mix") and name == "filosax":
        extra["sax_spans"] = extra["bleed"] = "skipped: the Filosax transcriber decides where the sax plays"
    elif take.read_manifest().get("mix") and take.source.exists():
        from .isolate import sax_spans
        isolated = take.read_manifest().get("layers", {}).get("isolate", {})
        used = (isolated.get("stem") or "").split("+")
        folder = take.folder / isolated["stems_folder"] if isolated.get("stems_folder") else take.stems

        def stems(*names):
            return [folder / f"{name}.wav" for name in names if name not in used and (folder / f"{name}.wav").exists()]
        extra["sax_spans"], cuts = sax_spans(take.stem, take.source, stems("other", "guitar", "vocals"),
                                             stems("drums", "bass"), stems("piano", "bass"))
        extra["sax_cuts"] = cuts
        for n in notes:
            if any(a <= n["onset"] < b for a, b in cuts):
                n["tags"].append(NOT_SAX)
        dropped = sum(NOT_SAX in n["tags"] for n in notes)
        if cuts:
            frontend.log(f"  The sax lays out at {', '.join(f'{a:.0f}-{b:.0f} s' for a, b in cuts)}: "
                         f"{dropped} notes there are kept in notes.json, tagged {NOT_SAX!r}, and left off the score")
        from . import bleed
        extra["bleed"] = bleed.tag(notes, line)
        if extra["bleed"]["no_pitch_line"] or extra["bleed"]["off_line"]:
            frontend.log(f"  {extra['bleed']['no_pitch_line']} notes where the sax's pitch line is silent and "
                         f"{extra['bleed']['off_line']} off the line (other instruments): kept, left off the score")
    chosen = take.read_manifest().get("sax_sections") or []
    if chosen:
        from .. import sections
        hidden = sections.tag(notes, chosen, NOT_SAX)
        extra["sax_sections"] = {"sections": chosen, "pad_s": sections.PAD, "hidden": hidden}
        frontend.log(f"  Sax sections {sections.text(chosen)}: {hidden} notes outside them are kept in "
                     f"notes.json, tagged {NOT_SAX!r} and {sections.OUTSIDE!r}, and left off the score")
    if take.read_manifest().get("mix") and take.source.exists():
        extra["maybe_not_sax"] = review_marks(take, notes)
    from . import ranges
    stem = frontend.load_mono(take.stem, sr=ranges.RATE) if range_rules != "off" else None
    extra["range"] = ranges.apply(notes, horn, stem, ranges.RATE, range_rules)
    for n in notes:
        if "detected_pitch" in n:
            n["cents"] = cents_off(line, n)
    report_range(extra["range"], horn)
    beats, downbeats, beat_tool = frontend.detect_beats(take.source)
    data = {
        "layout_version": LAYOUT_VERSION,
        "horn": horn.name,
        "pitch": "concert",
        "tools": {"notes": name, "beats": beat_tool},
        "tempo_bpm": tempo(beats),
        "key": None,
        "beats": [round(b, 4) for b in beats],
        "downbeats": [round(d, 4) for d in downbeats],
        "notes": [{"onset": round(n["onset"], 4), "offset": round(n["offset"], 4),
                   "pitch": int(n["pitch"]), "cents": n["cents"],
                   "amp": round(float(n.get("amp", 0.5)), 3), "tags": n["tags"],
                   **({"detected_pitch": int(n["detected_pitch"])} if "detected_pitch" in n else {})}
                  for n in notes],
    }
    take.notes.write_text(json.dumps(data, indent=1) + "\n")
    take.record("notes", tool=name, beats=beat_tool, **extra)
    joined = f" ({extra['joined']} split notes joined)" if "joined" in extra else ""
    frontend.log(f"  {name}: {len(notes)} notes{joined}; {beat_tool}: {len(beats)} beats")


def review_marks(take: Take, notes: list[dict]) -> dict:
    """Marks notes that may be another instrument for review (notsax.py); never hides them.
    Uses Demucs' six stems, which the Filosax path also keeps in stems/."""
    from . import isolate, notsax
    isolated = take.read_manifest().get("layers", {}).get("isolate", {})
    filosax_path = isolated.get("separator") == "filosax"
    if not (take.stems / f"{isolate.DEFAULT_STEM}.wav").exists():
        if not frontend.demucs_available():
            return {"marked": 0, "why": "no Demucs stems"}
        frontend.log("Separating Demucs' six stems too, to check for other instruments' solos...")
        frontend.separate_stems(take.source, take.stems)
    stems = {p.stem: p for p in take.stems.glob("*.wav")}
    if filosax_path:  # the stems Demucs puts the sax in, chosen as the Demucs path would
        lead = isolate.choose({n: isolate.lead_score(stems[n]) for n in isolate.MELODIC if n in stems})
        lead = lead or [isolate.DEFAULT_STEM]
    else:
        lead = [n for n in (isolated.get("stem") or isolate.DEFAULT_STEM).split("+") if n in stems]
    rivals = {n: stems[n] for n in notsax.RIVALS if n in stems and n not in lead}
    if not lead or not rivals:
        return {"marked": 0, "why": "no rival stems"}
    out = notsax.mark(notes, take.source, [stems[n] for n in lead], rivals, "filosax" if filosax_path else "demucs")
    out["sax_stems"] = lead
    if out["marked"]:
        frontend.log(f"  {out['marked']} notes may be another instrument (the sax track is near-silent while "
                     f"{', '.join(rivals)} plays): kept on the score, marked for review in the play-along")
    return out


def report_range(c: dict, horn: Horn) -> None:
    if c.get("mode") == "off":
        return
    if "better_horn" in c:
        frontend.log(f"  {c['out_of_range']} notes are outside the {horn.name}'s range; kept as heard. "
                     f"Was this a {c['better_horn']} take? (--horn {c['better_horn']})")
    bits = [f"{c[k]} {label}" for k, label in (("octave_up", "moved up an octave"),
                                                ("octave_down", "moved down from above the altissimo"),
                                                ("altissimo", "altissimo"), ("overtone", "possible overtones"),
                                                ("below_range", "just below the low note (left off the score)"))
            if c.get(k)]
    if bits:
        frontend.log(f"  range ({horn.name}, {c['mode']}): " + ", ".join(bits))


def one_line(notes: list[dict], line: dict | None = None) -> list[dict]:
    """A sax plays one note at a time: drop doubled attacks and cut overlaps.

    When two notes start at the same moment, keep the louder one (the other is
    usually an octave or a harmonic). A note that is still ringing when the
    next one starts ends there, unless the pitch line says the horn is still
    holding it (under): then it runs on to the next note that is not under it,
    and the note under it is kept, marked UNDER_HELD. Nothing else is removed.

    Measured 2026-11-04 (follow_exp.py, notes layer re-run on existing takes,
    against the keys): note F1 0 to +0.2 on every set (Pennies 50.0 -> 50.1,
    Parker band 57.8 -> 57.9, Bach10 96.8 -> 97.0, ChoraleBricks 90.1 -> 90.3,
    GRFIA +0.1), 93 held notes lengthened, 2 of 64 notes under them real.
    Choosing between doubled attacks by the pitch line was also tried and cost
    Blues for Mary Jane 0.7, so the louder one is still kept.
    """
    out: list[dict] = []
    for n in sorted(notes, key=lambda n: n["onset"]):
        if out and n["onset"] - out[-1]["onset"] < SAME_START:
            if n.get("amp", 0) > out[-1].get("amp", 0):
                out[-1] = dict(n)
            continue
        out.append(dict(n))
    flags = [False] * len(out)
    if line is not None:
        held = None
        for i, n in enumerate(out):
            if held is not None and out[held]["offset"] > n["onset"] and under(n, out[held], line):
                flags[i] = True
            else:
                held = i
    for i, a in enumerate(out):
        j = next((j for j in range(i + 1, len(out)) if flags[i] or not flags[j]), None)
        if j is not None:
            a["offset"] = min(a["offset"], out[j]["onset"])
        if flags[i]:
            a[UNDER_HELD] = True
    return [n for n in out if n["offset"] > n["onset"]]


def line_shares(line: dict, pitch: int, a: float, b: float) -> tuple[float, float]:
    """(share of frames voiced, share of voiced frames on pitch or its octave) over [a, b)."""
    t = line["time"]
    m = (t >= a) & (t < b)
    if m.sum() < 3:
        return 0.0, 0.0
    v = line["voiced"][m] & np.isfinite(line["midi"][m])
    if not v.any():
        return float(v.mean()), 0.0
    d = line["midi"][m][v] - pitch
    on = (np.abs(d) <= 0.5) | (np.abs(np.abs(d) - 12) <= 0.5)
    return float(v.mean()), float(on.mean())


def under(b: dict, a: dict, line: dict) -> bool:
    """b starts under held note a: through b the line is voiced, never on b, mostly on a."""
    span = (b["onset"] + EDGE, max(b["offset"] - EDGE, b["onset"] + 0.05))
    voiced, on_b = line_shares(line, b["pitch"], *span)
    if voiced < HELD_VOICED or on_b > 0:
        return False
    return line_shares(line, a["pitch"], *span)[1] >= HELD_ON


def from_contour(line: dict, onsets: list[dict]) -> list[dict]:
    """Notes cut from the pitch line (adapted from the game's vocal transcriber).

    A new note starts where the line settles on a pitch more than 0.8 semitone
    away, or where the stem has a clear attack (a tongued repeat on one pitch).
    """
    import scipy.signal
    times, midi = line["time"], np.where(line["voiced"], line["midi"], np.nan)
    filled = np.where(np.isnan(midi), 0.0, midi)
    smooth = np.where(np.isnan(midi), np.nan, scipy.signal.medfilt(filled, 5))  # 50 ms: smooths vibrato
    attacks = np.array([o["t"] for o in onsets if o["s"] >= 0.3])
    step = float(times[1] - times[0]) if len(times) > 1 else 0.01
    notes: list[dict] = []
    start, values = None, []

    def close(k_end):
        if start is None or len(values) < 4:  # under 40 ms: a slide, not a note
            return
        notes.append({"onset": float(times[start]), "offset": float(times[k_end]) + step,
                      "pitch": int(round(float(np.median(values)))),
                      "amp": float(np.clip(np.nanmean(line["confidence"][start:k_end + 1]), 0.2, 1.0))})

    for k in range(len(times)):
        m = smooth[k]
        if np.isnan(m):
            close(k - 1)
            start, values = None, []
            continue
        if start is None:
            start, values = k, [m]
            continue
        ref = float(np.median(values[-6:]))
        attack = len(attacks) and len(values) >= 6 and np.min(np.abs(attacks - times[k])) < step / 2
        if abs(m - ref) > 0.8 or attack:
            close(k - 1)
            start, values = k, [m]
        else:
            values.append(m)
    close(len(times) - 1)
    return notes


def cents_off(line: dict, note: dict) -> float | None:
    """Median distance of the pitch line from the note's pitch, in cents.

    Skips the first and last 20 ms, where scoops and releases live.
    """
    t = line["time"]
    mask = (t >= note["onset"] + 0.02) & (t < note["offset"] - 0.02) & line["voiced"]
    vals = line["midi"][mask]
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return None
    return round(float(np.median(vals - note["pitch"])) * 100, 1)


def tempo(beats: list[float]) -> float | None:
    if len(beats) < 2:
        return None
    return round(60.0 / float(np.median(np.diff(beats))), 2)


def read(take: Take) -> dict:
    return json.loads(take.notes.read_text())


def played(notes: list[dict]) -> tuple[list[int], list[dict]]:
    """The notes the sax played (not tagged not_sax), with their places in notes.json."""
    keep = [i for i, n in enumerate(notes) if NOT_SAX not in (n.get("tags") or [])]
    return keep, [notes[i] for i in keep]
