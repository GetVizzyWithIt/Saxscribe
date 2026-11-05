"""Layer 1: get the sax on its own.

A solo take is passed through: stem.wav is a copy of the source. A full mix
goes through Demucs; every stem is kept in stems/ so you can listen and pick
another with --stem, and accompaniment.wav is everything else added together.

Which stem holds the sax: Demucs (htdemucs_6s) has no sax stem, so the horn
lands in "other" on most records but in "guitar" on some, or is split
between the two (seen on Parker records: 7XTyc all in guitar, BRfYc about
half and half). By default (--stem auto) each melodic stem gets a lead score:
its loudness in frames that sound like one clear pitch, which favours a horn
line over chords. A stem with LEAD_ALONE of the total is used on its own;
otherwise every stem over LEAD_PART is added together. The scores and the
choice go in take.json.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from .. import frontend
from ..take import Take

DEFAULT_STEM = "other"  # where sax usually lands in Demucs' six stems
MELODIC = ("other", "guitar", "piano", "vocals")  # stems a horn can land in
LEAD_ALONE = 0.8   # a stem with this share of the lead score is used alone
LEAD_PART = 0.2    # otherwise stems with at least this share are added together
LEAD_RATE = 16000
LEAD_FRAME = 2048  # 128 ms: many periods of the lowest note
LEAD_HOP = 800     # 50 ms
LEAD_HZ = (95.0, 1600.0)  # tenor low B-flat (concert A-flat2, 104 Hz) up to altissimo


def run(take: Take, src: Path, mix: bool, stem: str | None) -> None:
    take.folder.mkdir(parents=True, exist_ok=True)
    frontend.log(f"Layer 1/4: isolate ({'full mix' if mix else 'solo take'})")
    frontend.decode(src, take.source)
    if not mix:
        shutil.copyfile(take.source, take.stem)
        take.accompaniment.unlink(missing_ok=True)
        take.record("isolate", tool="passthrough", source=str(src))
        return

    stems = {p.stem: p for p in take.stems.glob("*.wav")}
    if stems:
        frontend.log("Using the stems already separated (delete stems/ to separate again).")
    else:
        if not frontend.demucs_available():
            raise SystemExit("A full mix needs Demucs. Install it with: pip install -r requirements.txt")
        stems = frontend.separate_stems(take.source, take.stems)
    scores = {}
    if stem in (None, "auto"):
        scores = {n: lead_score(stems[n]) for n in MELODIC if n in stems}
        chosen = choose(scores) or [DEFAULT_STEM]
    else:
        chosen = [n.strip() for n in stem.split("+")]
    missing = [n for n in chosen if n not in stems]
    if missing:
        raise SystemExit(f"No stem called {missing[0]!r}. Stems: {', '.join(sorted(stems))}")
    if len(chosen) == 1:
        shutil.copyfile(stems[chosen[0]], take.stem)
    else:
        write_sum(take.stem, [stems[n] for n in chosen])
    write_accompaniment(take.accompaniment, [p for n, p in stems.items() if n not in chosen])
    name = "+".join(chosen)
    share = {n: round(v, 3) for n, v in shares(scores).items()}
    take.record("isolate", tool="demucs htdemucs_6s", shifts=frontend.DEMUCS_SHIFTS, stem=name, source=str(src), stems=sorted(stems),
                **({"lead_share": share} if share else {}))
    how = f" (lead share {', '.join(f'{n} {v:.0%}' for n, v in share.items())})" if share else ""
    frontend.log(f"Using the {name!r} stem{how}. Others are in {take.stems} to listen to.")


def lead_score(path: Path) -> float:
    """Loudness in frames that hold one clear pitch in the horn range.

    Per 128 ms frame: the autocorrelation peak in the horn range says how
    clearly one pitch sounds (about 0.95 for a horn line, under 0.6 for piano
    chords, near 0 for drums). Frames are weighted by how far that sits above
    0.5, squared, times the frame's energy, and summed."""
    y = frontend.load_mono(path, sr=LEAD_RATE)
    if len(y) < LEAD_FRAME:
        return 0.0
    energy, clarity = frame_clarity(y)
    return float(np.sum(energy * clarity))


def shares(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    return {n: v / total for n, v in scores.items()} if total > 0 else {}


def choose(scores: dict[str, float]) -> list[str]:
    """One stem when it clearly holds the lead, else every stem with a fair part of it."""
    s = shares(scores)
    if not s:
        return []
    ranked = sorted(s, key=s.get, reverse=True)
    if s[ranked[0]] >= LEAD_ALONE:
        return ranked[:1]
    return [n for n in ranked if s[n] >= LEAD_PART]


def write_sum(dst: Path, paths: list[Path]) -> None:
    write_accompaniment(dst, paths)  # the same thing: stems added together


def write_accompaniment(dst: Path, paths: list[Path]) -> None:
    import soundfile as sf
    total, rate = None, None
    for p in paths:
        y, rate = sf.read(str(p), always_2d=True)
        if total is None:
            total = y
        else:
            n = min(len(total), len(y))
            total = total[:n] + y[:n]
    if total is not None:
        sf.write(str(dst), np.clip(total, -1.0, 1.0), rate)


# ---------------------------------------------------------------- where the sax plays

SPAN_WINDOW = 2.0      # seconds per window
SPAN_HOP = 1.0         # seconds between windows
SPAN_SHARE_DB = -6.0   # the sax stem must hold this much of the mix (dB) ...
SPAN_SHARE_MARGIN = 3.0  # ... or, on a mix where the sax sits low, this far under its loud windows (dB)
SPAN_SHARE_FLOOR = -14.0  # never lower than this: a piano solo sits 10-50 dB down
SPAN_CLARITY = 0.4     # ... and sound this clear, as a share of the take's typical sax clarity
SPAN_SMOOTH = 13       # windows (about 12 s) in the median that steadies the call
SPAN_MIN_GAP = 8.0     # seconds: a shorter stretch without sax is not cut
SPAN_GUARD = 2.0       # seconds kept at each edge of a cut, so no entry or last note is lost
SPAN_RIVAL_GAP = {"piano": 6.0, "bass": 12.0}  # dB a rival stem must sit over the sax to mark a rest
SPAN_MAX_CUT = 0.8     # cutting more of the record than this means the check failed, not that the sax rests


def sax_spans(stem: Path, mix: Path, others: list[Path] = (),
              rhythm: list[Path] = (), rivals: list[Path] = ()) -> tuple[list[list[float]], list[list[float]]]:
    """Where the horn plays in a band record: (spans with sax, spans cut).

    A full record has stretches where the sax lays out: piano and bass solos,
    drum breaks. Demucs still leaves something in the sax stem there (piano
    bleeds into "other"), so the note finder writes notes nobody played. Per
    2 s window two things are measured: how much of the mix the sax stem
    holds (a piano solo sits 10-50 dB down in it; the sax 0-3 dB) and how
    clearly it holds one pitch (a drum break is near 0; on an old noisy
    record the sax is only 0.3-0.5, so this is judged against the take's own
    sax windows). Some mixes keep the sax well under the band all through
    (Walker's Theme: -8 dB median), so the share bar drops to 3 dB under the
    take's own loud windows (90th percentile), never below -14 dB. A window is sax when both pass; a 12 s running median
    steadies the call. Only stretches of 8 s or more are cut, and each cut
    gives back 2 s at both ends, so a cut never takes the edge of a phrase.

    Drums and bass (rhythm) don't count against the sax: on a sax trio they
    are the loudest stems all through (Potter, Item 1: 3-7 dB over the sax),
    so the share is taken of the mix without them. When the sax is split
    across stems (Coltrane, Impressions: vocals + other), the other stems
    are added to the sax stem for a second try, not judged one by one.
    Without drums and bass the clean sax stem's piano bleed can pass in a
    piano solo. So a window is still a rest when a rival stem (piano, bass)
    sits well over every sax stem in the whole mix (piano 6 dB, bass 12 dB)
    and the sax fails the old whole-mix test. In a piano solo the piano sits
    15 dB over the sax stems, in a bass solo the bass 18 dB; under the sax,
    comping piano sits below it and a trio's bass at most 8 dB over it.
    """
    y = frontend.load_mono(stem, sr=LEAD_RATE)
    m = frontend.load_mono(mix, sr=LEAD_RATE)
    rest = [frontend.load_mono(p, sr=LEAD_RATE) for p in rhythm]
    extra = [frontend.load_mono(p, sr=LEAD_RATE) for p in others]
    n = min([len(y), len(m)] + [len(r) for r in rest + extra])
    full = m[:n]
    m = full - sum(r[:n] for r in rest) if rest else full
    win, hop = int(SPAN_WINDOW * LEAD_RATE), int(SPAN_HOP * LEAD_RATE)
    if n < win:
        return [[0.0, n / LEAD_RATE]], []
    share, clear = window_measures(y[:n], m[:n], win, hop)
    share, clear = np.array(share), np.array(clear)
    bar = share_bar(share)
    held = share > bar
    typical = float(np.median(clear[held])) if held.any() else 0.0
    sax = held & (clear > SPAN_CLARITY * typical)
    for o in extra:
        o_share, o_clear = window_measures(o[:n], m[:n], win, hop)
        sax |= (o_share > bar) & (o_clear > SPAN_CLARITY * typical)
    if extra:
        both = y[:n] + sum(o[:n] for o in extra)
        b_share, b_clear = window_measures(both, m[:n], win, hop)
        sax |= (b_share > bar) & (b_clear > SPAN_CLARITY * typical)
    if rivals:
        f_share = window_measures(y[:n], full, win, hop)[0]
        for o in extra:  # as before: each stem judged alone against the whole mix
            f_share = np.maximum(f_share, window_measures(o[:n], full, win, hop)[0])
        old = (f_share > share_bar(f_share)) & (clear > SPAN_CLARITY * typical)
        for path in rivals:
            gap = SPAN_RIVAL_GAP.get(Path(path).stem, max(SPAN_RIVAL_GAP.values()))
            r_share = window_measures(frontend.load_mono(path, sr=LEAD_RATE)[:n], full, win, hop)[0]
            sax &= ~((r_share > f_share + gap) & ~old)
    from scipy.signal import medfilt
    sax = medfilt(sax.astype(float), SPAN_SMOOTH) > 0.5
    end = n / LEAD_RATE
    cuts = []
    for a, b in runs(~sax):
        t0 = a * SPAN_HOP + SPAN_GUARD
        t1 = min((b - 1) * SPAN_HOP + SPAN_WINDOW, end) - SPAN_GUARD
        if b == len(sax):
            t1 = end  # nothing after it to protect
        if a == 0:
            t0 = 0.0
        if t1 - t0 >= SPAN_MIN_GAP:
            cuts.append([round(t0, 2), round(t1, 2)])
    if sum(b - a for a, b in cuts) > SPAN_MAX_CUT * end:
        cuts = []  # a record is a sax record: never tag nearly all of it "sax rests"
    keep, t = [], 0.0
    for a, b in cuts:
        if a > t:
            keep.append([round(t, 2), a])
        t = b
    if t < end:
        keep.append([round(t, 2), round(end, 2)])
    return keep, cuts


def window_measures(y: np.ndarray, m: np.ndarray, win: int, hop: int) -> tuple[np.ndarray, np.ndarray]:
    """Per window: the stem's share of the mix (dB) and how clearly it holds one pitch."""
    n = min(len(y), len(m))
    energy, clarity = frame_clarity(y[:n])
    frame_t = np.arange(len(energy)) * LEAD_HOP / LEAD_RATE
    share, clear = [], []
    for i in range(0, n - win + 1, hop):
        a, b = i / LEAD_RATE, (i + win) / LEAD_RATE
        share.append(10 * np.log10((np.mean(y[i:i + win] ** 2) + 1e-10) / (np.mean(m[i:i + win] ** 2) + 1e-10)))
        k = (frame_t >= a) & (frame_t < b)
        clear.append(float(np.sum(energy[k] * clarity[k]) / max(np.sum(energy[k]), 1e-12)))
    return np.array(share), np.array(clear)


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """[start, end) of each run of True."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def share_bar(share) -> float:
    """The share (dB) a window needs to count as sax, set from the take itself."""
    if not len(share):
        return SPAN_SHARE_DB
    loud = float(np.percentile(share, 90))
    return max(min(SPAN_SHARE_DB, loud - SPAN_SHARE_MARGIN), SPAN_SHARE_FLOOR)


def frame_clarity(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per 128 ms frame: energy, and how clearly one pitch in the horn range sounds (0-1)."""
    frames = np.lib.stride_tricks.sliding_window_view(y, LEAD_FRAME)[::LEAD_HOP] * np.hanning(LEAD_FRAME)
    spec = np.abs(np.fft.rfft(frames, n=2 * LEAD_FRAME, axis=1)) ** 2
    ac = np.fft.irfft(spec, axis=1)[:, :LEAD_FRAME]
    energy = ac[:, 0]
    lo, hi = int(LEAD_RATE / LEAD_HZ[1]), int(LEAD_RATE / LEAD_HZ[0])
    peak = ac[:, lo:hi].max(axis=1) / np.maximum(energy, 1e-12)
    return energy, np.clip((peak - 0.5) / 0.5, 0, 1) ** 2
