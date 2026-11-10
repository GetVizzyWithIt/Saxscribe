# ADR-0042: Every chart/audio pair passes a match check; benchmark songs follow a fixed rule

- **Date**: 2026-11-10
- **Status**: Accepted
- **Decided by**: Austin (standing rule, 07:03Z in the book matching work)
- **PR**: #148 (Results page tabs and review verdicts), this docs PR
- **Reviewed by**: Austin, by hand, through the app's Needs review tab

## Context
Answer keys now come from many places: Weimar, printed transcriptions, etude books and charts. Some of them don't fit their recording. Examples: a horn-section chart filed against a solo (The Motet, E78), the wrong transposition, a different take, or an edition that differs from the playing. A key that doesn't fit makes a good transcription look bad. Training on it would teach the model wrong notes. The Results page's new front page (PR #148) also needs a fixed set of songs to track progress on.

## Decision
1. **Match check**: no chart/audio pair is used to train or to score until it passes the match check. That means `match_check.py` from the book matching work, or Austin's verdict in the app.
2. **Austin's verdicts**: the app's Needs review tab records them in `~/saxscribe-runs/keys/match_review.jsonl` on the Mac. Each line is `{id, verdict: good | wrong | unsure | null, note, when}`, and `match_check.py` reads them into its report.
3. **Benchmark rule**: a song counts toward the benchmark only if all three hold:
   - its key passed the match check, or Austin marked it good;
   - Austin has not marked it wrong;
   - no model was trained on it.

## Options considered
- **Match check plus a strict benchmark rule (chosen):** costs one check per pair and some of Austin's listening time. Scores stay honest.
- **Trust each key's source tier (Tier A–E) alone:** no extra step. But E78 showed even good sources can be filed against the wrong record.
- **Hand-check every key note by note:** the most reliable, but far too slow for hundreds of keys.

## Case against
- The check measures how well the key and recording line up, not whether every note is right. A key with consistent small slips can pass (E78 keys were never proofread note by note).
- Austin's "good" overrides a failed check. A quick listen may pass a key that is off in places the listen didn't cover.
- The benchmark shrinks whenever a song is used for training. If the second fine-tune uses Austin's six tunes or the Parker test, they leave the benchmark, and scores from before and after stop being comparable. Watch the benchmark song count on the Progress tab.

## Consequences
- New keys wait in Needs review until checked, so each new source needs some of Austin's time.
- Training sets must list their song IDs, so the benchmark can exclude them.
- `match_review.jsonl` stays on the Mac with the other keys; it is not in the repo.

## Look back
To fill in after the next new key source is added: did the check catch bad pairs, and did any pass that shouldn't have?
