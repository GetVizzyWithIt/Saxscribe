# Evaluation log

Every scorecard run, newest first. Protocol: [protocol.md](protocol.md).
Machine is Austin's M3 Pro MacBook unless noted. "Default" = torchcrepe full
for the contour, Basic Pitch for notes, Beat This! for beats.

## Summary: best result so far per set

| Set | Pitch | Onset F1 | Note F1 | Note F1 no offset | s/min | Targets | Run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bach10 | 96.9% | **92.2%** ✓ | **87.5%** ✓ | 92.2% | 21 | solo | E4 |
| choralebricks | **98.9%** ✓ | 86.7% | 77.8% | 86.5% | 22 | solo | E4 |
| urmp | 94.4% | 81.6% | 64.4% | 80.8% | 24 | solo | E3 |
| omnibook | 74%† | **86%** ✓ | **64.2%** ✓ | — | — | mix | E6, E9 |
| urmp-mix | 41.6% | 48.9% | 17.1% | 35.4% | 27 | mix | E3 |
| omnibook-mix (10) | — | — | 56.4% | — | 64 | mix | E11 |
| bach10-mix | 21.4% | 39.5% | 3.9% | 29.2% | 31 | mix | E4 |

† Understated by octave errors in some Omnibook answer keys (E10); about 87% on solos with sound keys.

Omnibook now uses chorus-limited grading (PR #16, E6); the earlier 45% note F1 (E2) was understated.

✓ = meets the v1 target for that set. Speed meets the full-mix target (60 s/min)
on every mix set and misses the solo target (15 s/min) on every solo set (21–24 s/min).

## Pending

| ID | What | Settings | Status |
| --- | --- | --- | --- |
| P1 | PR #10 before/after on omnibook | `basic_pitch_raw` vs `basic_pitch_join` | URMP, Bach10, ChoraleBricks done (E8); Omnibook still running |
| P2 | Omnibook with the segmenter and the contour cutter | `--notes-tool segment`, `--notes-tool contour` | Done, see E9 |
| P6 | Pitch-error breakdown on the weakest Omnibook solos | default | Done, see E10 |
| P3 | 10 full Parker records | `omnibook-mix --limit 10` | Done, see E11 |
| P4 | Dataset checksums | `fetch --check` | Done 2026-11-02: every file on the Mac matches its manifest md5 |
| P5 | Omnibook re-run with chorus-limited grading | PR #16 branch | Done, see E6 |

---

### E12 — 2026-11-03 — Readable notation on a real recording
- **Finding**: on real output (Parker solos, Austin's "Blues for Mary Jane") PR #21 gives multi-bar rests and far fewer ties, but still too many 32nds and triplets. Tuning is next.
- One bar of "Blues for Mary Jane" still produced a 6:5 tuplet MuseScore refused. PR #26 (merged) moves any point that is on neither the sixteenth nor the triplet grid onto sixteenths, and adds a setting to turn PDFs off (`[tools] musescore = "off"`).

### E11 — 2026-11-03 — Picking the sax stem from Demucs (PR #24, merged)
- **Finding**: Demucs has no sax stem. On some Parker records the sax lands in "guitar", or is split between "guitar" and "other", but the pipeline always read "other".
- **Change**: pick the stem that carries the clearest single melody line, and sum stems when the sax is split between them ([ADR-0020](../decisions/0020-pick-sax-stem-automatically.md)).
- **Set**: `omnibook-mix`, 10 Parker band records.

| Measure | Always "other" | Auto stem pick |
| --- | --- | --- |
| Note F1 (mean) | 50.6% | 56.4% |
| Worst three records | 24%, 30%, 25% | 56%, 49%, 41% |
| Other records | — | unchanged |
| Seconds per minute | 110 | 64 |

- **What it shows**: the gain comes entirely from the records where the sax had landed in the wrong stem; the rest are untouched. Speed is now close to the 60 s/min mix target.

### E10 — 2026-11-02 — Why Omnibook pitch accuracy is 74%: answer-key octave errors
- **Finding**: on the two worst solos (7RfYc, BRfYc) long passages of the answer key are an octave above what was played, checked against the recording. Our pitch line is right; the key is wrong.
- **On healthy solos**: pitch line right on ~87% of frames; matched notes have the correct pitch ~95% of the time.
- **Action**: PR #23 (merged) flags octave disagreements with the answer key in the scorecard. Datasheet updated with the data-quality issue.
- **Implication**: the 74% headline mixes our errors with the dataset's. Report Omnibook pitch with and without flagged solos once PR #23 lands.

### E9 — 2026-11-02 — Omnibook: three note tools, graded inside the key span
- **Set**: `omnibook`, 45 solos, chorus-limited grading (PR #16). Contour = torchcrepe for all three.

| Notes tool | Pitch | Onset F1 | Note F1 | Note F1 no offsets | Notes ours ÷ key | s/min |
| --- | --- | --- | --- | --- | --- | --- |
| `basic_pitch` (default) | 74% | 86% | **64.2%** | — | ≈1.0× | — |
| `segment` | — | — | 59.8% | — | — | — |
| `contour` | 74.3% | 82.5% | 58.3% | 72.7% | 0.99× | 83 |

- **What it shows**: Basic Pitch stays the default. The same three solos (FRfYc, BRfYc, 7RfYc) are the bottom three under every tool, and two of them have pitch accuracy of only 50–57%, so their problem is upstream of note cutting. It turned out to be the answer keys (E10).
- `contour` at 83 s/min misses the 60 s/min mix speed target.

### E8 — 2026-11-02 — Split-note join (PR #10), before and after
- **Settings**: before = `basic_pitch_raw` (no join), after = `basic_pitch` with the join, as merged in PR #10. Runs in `~/saxscribe-runs-pr10`.

| Set | Measure | Before | After |
| --- | --- | --- | --- |
| urmp (11) | Pitch accuracy | 94.4% | 94.4% |
| | Onset F1 | 81.6% | 77.7% |
| | Note F1 | 64.4% | 62.8% |
| | Notes joined | — | 412 |
| bach10 (10) | Pitch accuracy | 96.8% | 96.9% |
| | Onset F1 | 92.2% | 88.4% |
| | Note F1 | 87.5% | 77.1% |
| | Notes joined | — | 55 |
| choralebricks (38) | Pitch accuracy | 98.9% | 98.9% |
| | Onset F1 | 86.7% | 82.8% |
| | Note F1 | 77.8% | 72.1% |
| | Notes ours ÷ key | 1.25× | 1.10× |
| | Notes joined | — | 271 |

- **What it shows**: the join hurts all three clean sets. On ChoraleBricks it brings the note count closer to the key (1.25× → 1.10×) yet scores lower, so the notes it removes are often real ones. It merges real repeated notes (a player re-tonguing the same pitch), so it costs more than the split notes it fixes.
- **Action**: PR #22 (merged) turns it off by default ([ADR-0019](../decisions/0019-split-note-join-off-by-default.md)). Omnibook before/after still running.
- Fidelity note: wrongly joined repeats drop written notes, which is the failure the project rule forbids.

### E7 — 2026-11-02 — Notation readability pass on synthetic swing solos (PR #21, merged)
- **Set**: synthetic swing solos with known written answers (not a mir_eval scorecard; notation layer only). Per-solo averages.

| Measure | Before | After |
| --- | --- | --- |
| Swung eighths written in the wrong place | ~33 | ~3 |
| Eighth-note triplets written correctly | ~4 | ~45 |
| Dotted-sixteenth figures | baseline | about two thirds fewer |
| Runs of empty bars | one bar at a time | one numbered multi-bar rest |
| Enharmonic spelling | mixed within a line | consistent per part, in the horn's key |
| Notes kept | all | all |

- **What it shows**: the three readability issues found on the first real PDF are largely fixed on synthetic material. Synthetic swing is cleaner than a real player, so a check on real solos (Omnibook MusicXML is the natural reference) should follow before calling it done.

### E6 — 2026-11-02 — Omnibook re-graded inside each answer key's span (PR #16)
- **Settings**: default. 45 solos (one fewer than E2; reason to confirm from the scorecard).
- **Headline**: pitch 74%, onset F1 86% (mix target 75%: met), note F1 64% (mix target 60%: met).
- **What it shows**: E2's 45% came mostly from grading notes after the answer key ended. With fair grading the Omnibook stems meet the full-mix note targets; pitch accuracy (74% vs 90%) is now the gap, likely bleed in the separated stems.
- Our note count is now roughly equal to the answer key's.
- *To fill in*: commit, seconds per minute, note F1 without offsets.

### E5 — 2026-11-02 — First real PDF render (finding, not a scorecard)
- **What happened**: one Omnibook stem rendered to a clean PDF in the right alto
  key, but with only 42 of 398 notes. On unaccompanied sax the beat tracker found
  almost no beats, and the notation step dropped notes it couldn't place on a grid.
- **Why it matters**: a fidelity bug (the tool must never omit notes). Scorecards
  didn't catch it because they grade Layer 3, not the notation.
- **Fix**: PR #15 (merged), which also fixes a MuseScore crash on macOS. PR #17 (merged) cleans triplet markings MuseScore rejected.
- **Re-check after both**: the same Parker solo renders to 2 pages with all 398 notes, proper beaming and triplets.
- **Follow-up**: add a notation check to the scorecard: notes in the score ÷ notes in `notes.json` must be 1.

### E4 — 2026-11-02 — ChoraleBricks and Bach10 (PR #9)
- **Commit**: `489571e`. **Settings**: default, plus `segment` on choralebricks.

| Measure | choralebricks (38) | choralebricks, segment | bach10 (10) | bach10-mix (10) |
| --- | --- | --- | --- | --- |
| Pitch accuracy | 98.9% | 98.9% | 96.9% | 21.4% |
| Onset F1 | 86.7% | 74.1% | 92.2% | 39.5% |
| Note F1 | 77.8% | 60.3% | 87.5% | 3.9% |
| Note F1, no offsets | 86.5% | 73.9% | 92.2% | 29.2% |
| Seconds per minute | 22 | 20 | 21 | 31 |

- **What it shows**: pitch on clean sax is close to solved. Remaining solo
  losses are note boundaries: split repeated notes, and note ends (~9 points).
  Upper alto parts 86–96% note F1, inner alto parts 53–74%. The segmenter loses
  again. In the quartet the stem follows other instruments: 3–6× too many notes.

### E3 — 2026-11-02 — URMP (PR #8)
- **Commit**: `9abc06c`. **Settings**: default and `segment`; 11 sax parts.

| Measure | urmp | urmp, segment | urmp-mix |
| --- | --- | --- | --- |
| Pitch accuracy | 94.4% | 94.5% | 41.6% |
| Onset F1 | 81.6% | 72.1% | 48.9% |
| Note F1 | 64.4% | 46.7% | 17.1% |
| Note F1, no offsets | 80.8% | 71.4% | 35.4% |
| Seconds per minute | 24 | 23 | 27 |

- **What it shows**: default writes 5–45% more notes than the key (held or
  tongued notes split). The segmenter helps on slow legato parts only.
  Mixes: 1.5–5× too many notes; on Rejouissance onsets land (71%) but pitch is
  5% (following trombone/tuba). 16_Surprise: 81% pitch under both tools.

### E2 — 2026-11-02 — Omnibook baseline (Phase 0 gate)
- **Commit**: main after PR #6 (`b1f9563`). **Settings**: default. 46 stems.

| Pitch accuracy | Onset F1 | Note F1 | Seconds per minute |
| --- | --- | --- | --- |
| 73.3% | 60.4% | 45.0% | 44 |

- **What it shows**: Basic Pitch writes 1.5–3.2× the key's note count on these
  stems. Lower pitch accuracy than solo sets reflects bleed in the separated
  stems and the dataset's aligned-not-checked labels.

### E1 — 2026-11-02 — Omnibook smoke test
- **Settings**: default, `--limit 3`. Note F1 53%; Basic Pitch ~1.8× too many notes.
  Surfaced a fixture notation test failing only where Beat This! runs (fixed in PR #7).

## Published reference points

| Source | Data | Method | Note F-measure |
| --- | --- | --- | --- |
| Riley & Dixon, SMC 2023 | Filosax | CREPE Notes | 82.3 |
| | | Basic Pitch | 75.5 |
| | | pYIN notes | 58.3 |
| | | MT3 | 43.0 |

Not directly comparable with our sets until Filosax is available.
