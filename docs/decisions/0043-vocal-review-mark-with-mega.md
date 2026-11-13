# ADR-0043: Band records get a vocal review mark from Mega's vocal stem

- **Date**: 2026-11-13
- **Status**: Accepted
- **Decided by**: Austin (Build decision card, 17:07Z: "every band record, full Mega")
- **PR**: the build PR that adds rule V3 (code and `e82c_rows.jsonl`); this docs PR
- **Reviewed by**: three rounds of E82 with a pre-registered main setting in round 3; Austin's flagged takes as the outside test

## Context
On pop records, voices leak into setup D's sax stem and get written as sax (Austin's Najee, Burning Daylight and Just the Two of Us flags; the step 1 diagnosis found about half our notes in the flagged pop bars overlap a louder vocal). E82 tried a review mark: flag a note when a vocal stem is louder than the sax stem at that pitch. With Demucs's vocal stem (rounds 1–2), the mark hit real sax on instrumentals (218 bad marks on Austin's six tunes), because Demucs routes the sax into its vocals. With MVSep Mega 53-stem's vocal stem (round 3, run locally), it gave 112 good marks and 0 bad on 11 songs, and marked 241 of 603 notes inside Austin's Najee not-sax flags against 19 of 528 outside.

## Decision
Every band record runs Mega's vocal stem locally, and rule V3 (Mega vocals at least 0 dB louder than the Filosax sax stem at the note's pitch ±1 semitone, holding that pitch 3 dB over its median) marks notes for review. Marks never hide or delete notes (ADR-0016).

## Options considered
- **Mega on every band record (chosen):** the same check everywhere, so no vocal passage is missed because a cheaper check didn't suspect it. Costs about 3.5 times the song's length on the CPU.
- **Mega only where Demucs suspects vocals:** much faster on instrumentals. But Demucs's vocal stem is exactly what failed in rounds 1–2, so it would decide where to look using the signal we found unreliable.
- **More testing first:** a vocal tuning set (plan step 3) before any adoption. Safer, but leaves the known pop-record problem unmarked meanwhile; the mark only flags, so a wrong mark costs a glance, not a note.

## Case against
- Eleven songs is a small test, and only one (Bloody Well Right) had many vocal marks; the 0 bad marks could rise on singers whose range and tone sit close to the sax (for example a breathy tenor voice in unison with the horn). This breaks if new pop songs show more than about 1.5% of matched notes marked.
- The threshold was pre-registered, not tuned on vocal songs, because no vocal tuning set exists yet.
- Processing time grows: each band record takes several minutes longer on the Mac. Accuracy over speed is Austin's standing rule, but long sessions will feel it.
- It depends on Mega's model being available locally; if the model changes or is withdrawn, the marks change with it.

## Consequences
- Band-record runs take longer (Mega at about 3.5× real time).
- The review marks appear in the app's listener like the other not-sax marks; Austin's flags remain the test.
- A fast home-grown vocal detector distilled from Mega's decisions is on the roadmap (Later) to remove the speed cost.
- `experiments.jsonl` gets the E82 round 3 rows with the build PR.

## Look back
After the vocal test set (plan step 3) and the next pop records: did bad marks stay near zero, and did the marks cover Austin's vocal flags?
