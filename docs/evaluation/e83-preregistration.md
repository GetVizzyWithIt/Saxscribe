# E83: second note-finder fine-tune (pre-registration)

Written 2026-11-13 23:00Z, before any E83 training or scoring. Austin's go: "go e83" (Build, 22:52Z).

## Question
Does more training for the note finder beat the E77 checkpoint on the 33-song benchmark? There are two possible changes: training on the stems the app actually uses (Filosax), and adding the newly checked transcribed keys (more styles, including R&B and pop).

## Arms
Both start from E77 `best.pt` (step 2488) and use the same train.py. Early stop: patience 1500 steps, validate every 500, cap at 6000 steps. The checkpoint is chosen on the same 24 held-out spans (Coltrane, Potter, Getz).

| Arm | Training audio | Training data | Isolates |
|---|---|---|---|
| E83a | Filosax-separated stems | E76 train set (110 spans) | Training on the stems the app uses (E77 trained on Mega stems) |
| E83b | Filosax-separated stems | E76 train set + transcribed keys that pass the downloads check | Adding the new data |

E83b runs only if the check passes at least 10 new usable pairs that are not excluded below. If fewer pass, only E83a runs and the shortfall is reported.

## Leakage rules
The following never go into training:
- the 33 E81 benchmark songs
- Austin's six tunes, his flagged takes and his own playing
- the 3 Parker test records
- any record by Coltrane, Potter or Getz (the held-out players)

New pairs are used only when `keys/match_report.jsonl` has `usable=true` after the check finishes.

## Scoring (once, at the end)
E81 setup D (Filosax separator) on all 33 songs, run three times: with the E77 finder, the E83a finder and the E83b finder. Same thresholds, same classify, bars on.

## Adoption rule (fixed now)
An arm is a candidate for the default when all of the following hold against E77:
- mean note F1 over the 33 songs is at least 1.0 point higher
- it wins at least 18 of the 33 songs
- mean note F1 without offsets is not lower

If both arms qualify, the arm with the higher mean note F1 is the candidate. Switching the app's default still needs Austin's go.

## Not in E83
- A note-end fix. Step 2's listening suggests the keys' note ends may be at fault, and it is unfinished (about 95 clips left).
- Soprano. No soprano training data is expected to pass the check.

## Case against
- Few new pop and R&B pairs (so far only Yakety Yak), so E83b may mostly add more jazz.
- Transcribed keys are tier B: score-reader slips could teach errors.
- Gains measured on held-out players chose the checkpoint, so they are slightly optimistic. The 33-song benchmark is the honest test.
