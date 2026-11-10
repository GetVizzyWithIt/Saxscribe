# ADR-0041: Band records default to our sax model (Filosax separator + E77 finder)

- **Date**: 2026-11-10
- **Status**: Accepted
- **Decided by**: Austin (agreed 03:49Z in the build thread)
- **PR**: #147 (app change), #146 (E80 rows), #145 (this record)
- **Reviewed by**: E80 scorecard on held-out sets (six Austin tunes, Parker test); no outside review yet

## Context
The note finder was the bottleneck on band records (E73). The Filosax transcriber, fine-tuned on Mega sax stems (E77), improved every test set. E80 then ran four setups the way the app runs them, on the six Austin tunes and the three Parker test records:

| Set | A standard | D Filosax separator + our finder |
| --- | --- | --- |
| austin-6, note F1 | 37.7 | **45.7** |
| Parker test, note F1 | 56.6 | **69.9** |

D won on all 9 songs, and its note count came much closer to the key (1.32 → 1.04 notes per key note). Details: [E80](../evaluation/log.md).

## Decision
In the app, a new **Automatic** engine is the default. Band records run setup D. Solo takes keep the standard path, because E80 didn't test solo takes. The CLI default is unchanged; D on the CLI is `--separator filosax --notes-tool filosax`. The old standard path stays in the picker as "Old standard (test)" for comparing.

## Options considered
- **A, keep the standard path** (Demucs + Basic Pitch): lost on every song in E80.
- **B, Demucs + our finder**: keeps the familiar separator; its E80 rows are in #146.
- **C, Demucs + the original Filosax finder**: needs no fine-tuned weights, but the fine-tune gave the gain in E77; rows in #146.
- **D, Filosax separator + our finder (chosen)**: beat A on all 9 songs.
- Not in E80: MVSep Mega stems + our finder. Mega holds the most key notes (E73), but it is a web service and can't run inside the app on the Mac. This stays the best candidate for a later test.

The pick follows the scorecard rather than habit: D is a new path and replaces the long-standing default.

## Case against
- **No sax-rest cut or bleed hide on this path.** The Filosax finder decides where the sax plays, so these checks are skipped by design. D marked 0% of notes as not-sax, against 15% for A. Vocals or a horn section in the stem won't be hidden automatically. This breaks on records like "Just the Two of Us", where vocals were charted as sax. The sax-sections box (#144) and the maybe-not-sax review marks are the only guards left.
- **Walker's Theme stays flat** (28 to 30 under every setup). D doesn't fix smooth-jazz fast runs or bends.
- **Fallback is unscored.** If the E77 weights file is missing, the finder falls back to Riley & Dixon's original weights on the Filosax separator. E80 didn't score that combination.
- **Small test.** Nine songs, and the six tunes are the ones the pipeline has been tuned against for weeks. A loss on new band records would show this.

## Consequences
- Band-record results in the app change. Feedback runs are labelled by the path that ran ("Sax model" or "Standard"), so flags from before and after can be told apart (ADR-0039).
- Jobs made before the change keep their engine.
- To watch: not-sax notes on vocal records, and the weights file being present on the Mac.

## Look back
To fill in after the next band-record scorecard (bias check 11): did vocals or horn sections leak into the sheet more than under A?
