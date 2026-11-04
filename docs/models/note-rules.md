# Model card: note rules (one-line, split-note join, segmenter, contour cutter)

Rule-based components written for Saxscribe. No training; every threshold is a
constant in the code. They are carded because they change the output as much
as a model does.

## Model details

| Component | File | On by default | What it does |
| --- | --- | --- | --- |
| One-line | `layers/notes.py: one_line` | Yes, after Basic Pitch | A sax plays one note at a time: of notes starting within 30 ms, keep the louder; cut a note where the next begins. Nothing else is dropped |
| Split-note join | `layers/segment.py: join_repeats` | No since PR #22 (`--notes-tool basic_pitch_join`); was on by default after PR #10 | Joins same-pitch neighbours less than 30 ms apart, unless the stem shows a re-attack: a level dip of 35% of the loud level, or an attack at 70% of the take's strong attacks that swells the sound again |
| Segmenter | `layers/segment.py: segment` | No (`--notes-tool segment`) | Cuts the contour into notes after the CREPE Notes method: boundary strength = (1 − confidence) × normalised pitch slope, peaks above 0.002; joins neighbours on the same rounded note; drops quiet pieces; trims ends by level; splits repeats at strong attacks or level dips; drops notes under 30 ms. Pitch = median after the take's tuning offset |
| Range rules | `layers/ranges.py` | Yes from PR #69 (`--range-rules out`; also `overtones`, `flag`, `off`) | Checks each note against the horn's range table (`horns.py`). Altissimo kept and tagged; notes no sax can play moved by octaves with `detected_pitch` kept; suspected overtones checked from the stem spectrum (lower note's partials at least 0.3 as loud as the shared ones) only with `overtones` (moves them) or `flag`; off in the default since PR #78 because the check was wrong ~95% of the time (log E39); many out-of-range notes = wrong horn, nothing moved. Never deletes ([ADR-0031](../decisions/0031-range-rules-per-horn.md)) |
| Contour cutter | `layers/notes.py: from_contour` | No (`--notes-tool contour`) | New note where the pitch settles somewhere new or the stem has a clear attack (adapted from the game's vocal transcriber) |

- **Licence**: ours (repo licence). The segmenter is our own implementation from the paper's description; no code from the GPL `crepe-notes` package ([ADR-0006](../decisions/0006-own-crepe-notes-implementation.md)).
- **Reference**: Riley & Dixon, "CREPE Notes: A new method for segmenting pitch contours into discrete notes", SMC 2023.

## Intended use
Layer 3. The join and one-line rules fix known Basic Pitch failure modes on a monophonic horn. The segmenter and contour cutter are alternatives to compare on the scorecard.

## Factors
Legato vs. tongued playing; repeated notes; vibrato depth; how clean the stem is.

## Metrics
Onset F1, note F1 with and without offsets; ratio of our note count to the answer key's.

## Quantitative results (2026-11-02, [log](../evaluation/log.md))

| Set | Basic Pitch (default then) note F1 | Segmenter note F1 |
| --- | --- | --- |
| urmp | 64.4% | 46.7% |
| choralebricks | 77.8% | 60.3% |

On the Omnibook (45 solos, log E9) note F1 is 64.2% for Basic Pitch, 59.8% for the segmenter and 58.3% for the contour cutter.

The segmenter wins on slow legato URMP parts (King, Fugue, Jerusalem) and loses elsewhere. It does not reproduce the published CREPE Notes advantage on Filosax; possible reasons are our thresholds, the absence of the paper's amplitude-based end trimming details, or dataset differences. Not worth more time until Filosax allows a like-for-like check.

Split-note join, before → after (log E8): URMP onset F1 81.6% → 77.7%, note F1 64.4% → 62.8% (412 joins); Bach10 onset F1 92.2% → 88.4%, note F1 87.5% → 77.1% (55 joins); ChoraleBricks onset F1 86.7% → 82.8%, note F1 77.8% → 72.1% (271 joins). It merges real repeated notes, so it is off by default (PR #22). Omnibook pending.

## Caveats and recommendations
- Thresholds were set on the synthetic fixture and paper defaults, not tuned on the test sets (good: no leakage; bad: may be far from optimal). Tune only on train splits.
- These rules are the natural first thing a trained onset/articulation head replaces.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | One-line and contour cutter | #1 |
| 2026-11-02 | Segmenter | #6 |
| 2026-11-02 | Split-note join, on by default | #10 |
| 2026-11-02 | Split-note join off by default after scorecard; `basic_pitch_join` | #22 |
| 2026-11-04 | Range rules per horn; synthetic note F1 alto 92.6% → 100%, tenor 89.6% → 100% (log E34) | #69 |
