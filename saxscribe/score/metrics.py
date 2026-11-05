"""Scores for one take against its answer key, with mir_eval, so numbers compare with papers.

  pitch_accuracy   share of sounding answer-key frames where our pitch line is
                   within 50 cents (mir_eval "raw pitch accuracy"; the answer
                   key's frames take the note's pitch, so vibrato costs a little)
  chroma_accuracy  the same, but an exact octave off also counts as right
                   (mir_eval "raw chroma accuracy")
  octave_errors    chroma_accuracy - pitch_accuracy: the share of frames that are
                   right except for the octave. Over OCTAVE_FLAG on one take
                   usually means part of the answer key is written in the wrong
                   octave (seen on Omnibook BRfYc and 7RfYc), or the pitch
                   tracker dropped an octave; a look at the stem's spectrum tells which
  onset_f1         attacks found within 50 ms, pitch ignored
  note_f1          onset within 50 ms, pitch within 50 cents, offset within
                   20% of the note's length (or 50 ms)
  note_f1_no_offset  the same without the offset rule
  sax_found    share of the answer key's notes we wrote (onset within 50 ms,
               pitch within 50 cents, ends ignored): sax the tool did not lose
  sax_purity   share of our notes the answer key has (same rule): the rest is
               bleed from other instruments, ghosts or wrong pitches
  beat_f1          beats within 70 ms (only when the answer key has beats)

Guard metrics. A change can lift note F1 by merging or dropping notes (fewer
wrong notes, fewer right ones too). This tool must not learn to leave notes
out, so these sit beside F1 and must not fall when F1 rises:
  short_found      sax_found on the key's notes under SHORT seconds: fast runs
  ghost_found      sax_found on notes the key marks "ghost": true (only when it does)
  extras_in_rests_per_min  our notes that start where the key has a rest
                   (no key note within REST_PAD), per minute of rest: piano
                   or guitar bleed and other ghosts in the gaps
  onset_f1_100ms, note_f1_100ms  onset F1 and note F1 (ends ignored) at 100 ms.
                   A big gap over the 50 ms numbers means timing jitter, not
                   missing notes; listeners judge closer to the looser number
                   (Ycart et al., TISMIR 2020)

When an answer key covers only part of the recording (Reference.partial),
only what we found inside the key's span (first onset - 0.5 s to last
offset + 0.5 s) is scored, so playing the key leaves out is not counted as
wrong notes.
"""
from __future__ import annotations

import numpy as np

FRAME = 0.01
SPAN_MARGIN = 0.5
OCTAVE_FLAG = 0.05  # a take with more octave-only errors than this is flagged on the card
SHORT = 0.12        # seconds: Basic Pitch's floor is about here; a 16th at 300 BPM lasts 0.05
REST_PAD = 0.1      # a note starting this close to a key note is not "in a rest"
MIN_REST = 0.25     # gaps in the key shorter than this are articulation, not rests


def span_of(ref_notes: list[dict]) -> tuple[float, float]:
    return (min(n["onset"] for n in ref_notes) - SPAN_MARGIN, max(n["offset"] for n in ref_notes) + SPAN_MARGIN)


def inside(notes: list[dict], span: tuple[float, float]) -> list[dict]:
    return [n for n in notes if span[0] <= n["onset"] < span[1]]


def hz(midi) -> np.ndarray:
    return 440.0 * 2 ** ((np.asarray(midi, dtype=float) - 69) / 12)


def as_arrays(notes: list[dict]):
    if not notes:
        return np.zeros((0, 2)), np.zeros(0)
    return (np.array([[n["onset"], n["offset"]] for n in notes]),
            hz([n["pitch"] for n in notes]))


def note_scores(ref: list[dict], est: list[dict]) -> dict:
    import mir_eval
    ri, rp = as_arrays(ref)
    ei, ep = as_arrays(est)
    if len(ri) == 0:
        return {}
    if len(ei) == 0:
        return {"onset_f1": 0.0, "note_f1": 0.0, "note_f1_no_offset": 0.0, "sax_found": 0.0}
    onset = mir_eval.transcription.onset_precision_recall_f1(ri, ei, onset_tolerance=0.05)
    full = mir_eval.transcription.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05,
                                                             pitch_tolerance=50.0, offset_ratio=0.2)
    no_off = mir_eval.transcription.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05,
                                                               pitch_tolerance=50.0, offset_ratio=None)
    out = {"onset_precision": onset[0], "onset_recall": onset[1], "onset_f1": onset[2],
           "note_precision": full[0], "note_recall": full[1], "note_f1": full[2],
           "note_f1_no_offset": no_off[2], "sax_found": no_off[1], "sax_purity": no_off[0]}
    out.update(guard_scores(ref, est))
    return out


def guard_scores(ref: list[dict], est: list[dict]) -> dict:
    """The guard metrics (see the module notes): notes we must not lose, and notes in rests."""
    import mir_eval
    ri, rp = as_arrays(ref)
    ei, ep = as_arrays(est)
    out = {}
    if len(ri) and len(ei):
        out["onset_f1_100ms"] = mir_eval.transcription.onset_precision_recall_f1(ri, ei, onset_tolerance=0.1)[2]
        out["note_f1_100ms"] = mir_eval.transcription.precision_recall_f1_overlap(
            ri, rp, ei, ep, onset_tolerance=0.1, pitch_tolerance=50.0, offset_ratio=None)[2]
    found = set()
    if len(ri) and len(ei):
        found = {i for i, _ in mir_eval.transcription.match_notes(ri, rp, ei, ep, onset_tolerance=0.05,
                                                                 pitch_tolerance=50.0, offset_ratio=None)}
    for name, keep in (("short_found", lambda n: n["offset"] - n["onset"] < SHORT),
                       ("ghost_found", lambda n: bool(n.get("ghost")))):
        idx = [i for i, n in enumerate(ref) if keep(n)]
        if idx:
            out[name] = sum(i in found for i in idx) / len(idx)
            out[name.replace("_found", "_notes")] = len(idx)
    rest = rest_seconds(ref)
    if rest > 0:
        starts = sorted(n["onset"] for n in ref)
        on = np.array(starts)
        lo, hi = min(starts), max(n["offset"] for n in ref)
        extras = 0
        for n in est:
            t = n["onset"]
            if not (lo <= t <= hi):
                continue
            sounding = any(r["onset"] - REST_PAD <= t <= r["offset"] + REST_PAD for r in ref)
            if not sounding and not np.any(np.abs(on - t) <= REST_PAD):
                extras += 1
        out["extras_in_rests_per_min"] = extras / (rest / 60)
        out["rest_seconds"] = rest
    return out


def rest_seconds(ref: list[dict]) -> float:
    """Seconds inside the key's span where no key note sounds, counting gaps of MIN_REST or more."""
    if not ref:
        return 0.0
    spans = sorted((n["onset"], n["offset"]) for n in ref)
    total, end = 0.0, spans[0][1]
    for a, b in spans[1:]:
        if a - end >= MIN_REST:
            total += a - end
        end = max(end, b)
    return total


def pitch_scores(ref: list[dict], contour: dict) -> dict:
    """Pitch line against the answer key's notes, frame by frame."""
    import mir_eval
    if not ref:
        return {}
    end = max(n["offset"] for n in ref)
    t = np.arange(0, end, FRAME)
    ref_hz = np.zeros_like(t)
    for n in ref:
        ref_hz[(t >= n["onset"]) & (t < n["offset"])] = hz(n["pitch"])
    est_hz = np.where(contour["voiced"], np.nan_to_num(contour["f0_hz"]), 0.0)
    s = mir_eval.melody.evaluate(t, ref_hz, contour["time"], est_hz)
    return {"pitch_accuracy": s["Raw Pitch Accuracy"], "chroma_accuracy": s["Raw Chroma Accuracy"],
            "octave_errors": max(0.0, s["Raw Chroma Accuracy"] - s["Raw Pitch Accuracy"]),
            "voicing_recall": s["Voicing Recall"], "voicing_false_alarm": s["Voicing False Alarm"]}


def beat_scores(ref_beats: list[float] | None, est_beats: list[float]) -> dict:
    import mir_eval
    if not ref_beats:
        return {}
    return {"beat_f1": mir_eval.beat.f_measure(np.array(ref_beats), np.array(est_beats),
                                               f_measure_threshold=0.07)}


def score_take(ref, take) -> dict:
    """Every layer's scores for one take folder against one Reference."""
    from ..layers import contour as contour_layer, notes as notes_layer
    data = notes_layer.read(take)
    est = notes_layer.played(data["notes"])[1]
    beats = data.get("beats") or []
    if getattr(ref, "partial", False) and ref.notes:
        span = span_of(ref.notes)
        est = inside(est, span)
        beats = [b for b in beats if span[0] <= b < span[1]]
    out = {}
    out.update(pitch_scores(ref.notes, contour_layer.read(take.contour)))
    out.update(note_scores(ref.notes, est))
    out.update(beat_scores(ref.beats, beats))
    out["ref_notes"] = len(ref.notes)
    # Answer-key notes inside stretches cut as "no sax": a wrong cut hides sax
    # notes from the score as well as the sheet music, so it is counted here.
    cuts = take.read_manifest().get("layers", {}).get("notes", {}).get("sax_cuts") or []
    if cuts:
        out["key_notes_cut"] = sum(any(a <= n["onset"] < b for a, b in cuts) for n in ref.notes)
    out["est_notes"] = len(est)
    return {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}
