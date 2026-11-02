# Model card: note rules (one-line, split-note join, segmenter, contour cutter)

Rule-based components written for Saxscribe. No training; every threshold is a
constant in the code. They are carded because they change the output as much
as a model does.

## Model details

| Component | File | On by default | What it does |
| --- | --- | --- | --- |
| One-line | `layers/notes.py: one_line` | Yes, after Basic Pitch | A sax plays one note at a time: of notes starting within 30 ms, keep the louder; cut a note where the next begins. Nothing else is dropped |
| Split-note join | `layers/segment.py: join_repeats` | Yes (`basic_pitch`); off with `basic_pitch_raw` | Joins same-pitch neighbours less than 30 ms apart, unless the stem shows a re-attack: a level dip of 35% of the loud level, or an attack at 70% of the take's strong attacks that swells the sound again |
| Segmenter | `layers/segment.py: segment` | No (`--notes-tool segment`) | Cuts the contour into notes after the CREPE Notes method: boundary strength = (1 − confidence) × normalised pitch slope, peaks above 0.002; joins neighbours on the same rounded note; drops quiet pieces; trims ends by level; splits repeats at strong attacks or level dips; drops notes under 30 ms. Pitch = median after the take's tuning offset |
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

The segmenter wins on slow legato URMP parts (King, Fugue, Jerusalem) and loses elsewhere. It does not reproduce the published CREPE Notes advantage on Filosax; possible reasons are our thresholds, the absence of the paper's amplitude-based end trimming details, or dataset differences. Not worth more time until Filosax allows a like-for-like check.

Split-note join: before/after runs on URMP, Bach10, ChoraleBricks and Omnibook are running on the Mac.

## Caveats and recommendations
- Thresholds were set on the synthetic fixture and paper defaults, not tuned on the test sets (good: no leakage; bad: may be far from optimal). Tune only on train splits.
- These rules are the natural first thing a trained onset/articulation head replaces.

## Change history
| Date | Change | PR |
| --- | --- | --- |
| 2026-11-02 | One-line and contour cutter | #1 |
| 2026-11-02 | Segmenter | #6 |
| 2026-11-02 | Split-note join, on by default | #10 |
