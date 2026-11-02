"""Scores for one take against its answer key, with mir_eval, so numbers compare with papers.

  pitch_accuracy   share of sounding answer-key frames where our pitch line is
                   within 50 cents (mir_eval "raw pitch accuracy"; the answer
                   key's frames take the note's pitch, so vibrato costs a little)
  onset_f1         attacks found within 50 ms, pitch ignored
  note_f1          onset within 50 ms, pitch within 50 cents, offset within
                   20% of the note's length (or 50 ms)
  note_f1_no_offset  the same without the offset rule
  beat_f1          beats within 70 ms (only when the answer key has beats)
"""
from __future__ import annotations

import numpy as np

FRAME = 0.01


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
        return {"onset_f1": 0.0, "note_f1": 0.0, "note_f1_no_offset": 0.0}
    onset = mir_eval.transcription.onset_precision_recall_f1(ri, ei, onset_tolerance=0.05)
    full = mir_eval.transcription.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05,
                                                             pitch_tolerance=50.0, offset_ratio=0.2)
    no_off = mir_eval.transcription.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05,
                                                               pitch_tolerance=50.0, offset_ratio=None)
    return {"onset_precision": onset[0], "onset_recall": onset[1], "onset_f1": onset[2],
            "note_precision": full[0], "note_recall": full[1], "note_f1": full[2],
            "note_f1_no_offset": no_off[2]}


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
    return {"pitch_accuracy": s["Raw Pitch Accuracy"], "voicing_recall": s["Voicing Recall"],
            "voicing_false_alarm": s["Voicing False Alarm"]}


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
    out = {}
    out.update(pitch_scores(ref.notes, contour_layer.read(take.contour)))
    out.update(note_scores(ref.notes, data["notes"]))
    out.update(beat_scores(ref.beats, data.get("beats") or []))
    out["ref_notes"] = len(ref.notes)
    out["est_notes"] = len(data["notes"])
    return {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}
