# Evaluation log

Every scorecard run, newest first. Protocol: [protocol.md](protocol.md).
The same runs, machine-readable, are in [results.jsonl](results.jsonl) (one line per run, `entry` = the E-number here) and the change table below is mirrored in [changes.json](changes.json); both feed the app's Results page (PR #38). Keep all three in step ([protocol](protocol.md#three-records-of-the-same-runs-kept-in-step)).
Machine is Austin's M3 Pro MacBook unless noted. "Default" = torchcrepe full
for the contour, Basic Pitch for notes, Beat This! for beats.

## Change by change: what each model or pipeline change did

One row per change, newest first, with the main number before and after.
"Kept" says whether the change is on by default. Details and full tables are
in the entry linked in the last column. Answer-key and grading fixes (PR #46 and #47 for GRFIA) are not listed here: they change the yardstick, not the transcriber; see the entries. Notation-only changes leave pitch,
onset and note F1 untouched, so they are measured on the written score.

| Date | PR | Change | Layer | Set | Measure | Before | After | Kept | Entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-05 | #112 | Straight sixteenth runs kept straight in swung tunes | notation | weimar rhythm scorecard (444 solos), pfh-austin (Filosax take) | Position read / notes right | 67.26% / 578 of 734 | 67.85% / 589 of 734 | yes | [E66](#e66--2026-11-05--straight-sixteenth-runs-kept-straight-in-swung-tunes-pr-112-merged) |
| 2026-11-05 | #109 | Bar lines follow the beat tracker's downbeats; beat grid mended where it slips | notation | tuning records, held-out records, pfh-austin | Bars in the right place | 44.2 / 34.1 / 0.6% | 75.1 / 58.0 / 87.5% | yes | [E64](#e64--2026-11-05--bar-lines-kept-on-the-right-beat-pr-109-merged) |
| 2026-11-05 | #103 | Filosax separator and transcriber as opt-in settings (`--separator filosax`, `--notes-tool filosax`) | isolate + notes | weimar-tenor, omnibook-mix, pfh-austin, bfmj-austin | Note F1 (opt-in vs default) | 57.3 / 58.2 / 50.1 / 56.2% | 76.9 / 67.5 / 56.8 / 48.6% | opt-in | [E59](#e59--2026-11-05--filosax-separator-and-transcriber-as-opt-in-settings-pr-103-merged) |
| 2026-11-05 | #102 | Sax-span check measures against the mix without drums and bass and sums split stems | isolate | weimar-tenor, omnibook-mix, resolution-austin, walkers-theme-austin, bloody-well-right-austin | Note F1 | 57.3 / 60.6 / 42.5 / 28.3 / 11.6% | 65.6 / 60.6 / 42.0 / 28.3 / 11.4% | yes | [E57](#e57--2026-11-05--sax-span-check-ignores-drums-and-bass-sums-split-stems-pr-102-merged) |
| 2026-11-05 | #99 | Sax-span check never tags more than 80% of a record as "sax rests" | isolate | 27 band takes | Note F1 | — | unchanged on all 27 | yes | [E54](#e54--2026-11-05--sax-span-loudness-bar-set-per-record-pr-97-merged) |
| 2026-11-05 | #97 | Sax-span loudness bar set per record, so a quietly mixed sax isn't cut | isolate | walkers-theme-austin (26 other band takes unchanged) | Note F1 | 0% | 28.3% | yes | [E54](#e54--2026-11-05--sax-span-loudness-bar-set-per-record-pr-97-merged) |
| 2026-11-05 | #86 | Piano notes under a held sax note no longer cut it short | notes | pfh-austin, omnibook-mix, bach10, choralebricks, grfia-alto, grfia-tenor | Note F1 | 50.0 / 57.8 / 96.8 / 90.1 / 78.5 / 66.3% | 50.1 / 57.9 / 97.0 / 90.3 / 78.6 / 66.4% | yes | [E49](#e49--2026-11-04--piano-notes-no-longer-cut-held-sax-notes-short-pr-86-merged) |
| 2026-11-05 | #93 (was #84) | Hide piano and bass notes the sax's pitch line doesn't back up (band records) | isolate + notes | pfh-austin, omnibook-mix, bfmj-austin | Note F1 | 49.2 / 57.6 / 56.0% | 49.8 / 57.8 / 56.2% | yes | [E48](#e48--2026-11-04--hide-piano-and-bass-notes-the-saxs-pitch-line-doesnt-back-up-pr-93-merged) |
| 2026-11-04 | #81 | Notes below the horn's low note tagged `not_sax` and left off the sheet, on every take | notes + notation | pfh-austin, grfia-alto, omnibook, omnibook-mix | Note F1 | 50.3% / 75.1% / 64.2% / 57.62% | +0.11 / +0.03 / ~0 / +0.21 points (4 / 8 / 3 / 27 notes hidden) | yes | [E43](#e43--2026-11-04--no-notes-below-the-horns-low-note-on-the-sheet-pr-81-merged) |
| 2026-11-04 | — (#78) | Suspected overtones moved down to the lower note (`--range-rules overtones`), tested as the default; #78 then turns the overtone check off by default | notes | omnibook, grfia-tenor, grfia-alto | Note F1 (Omnibook / tenor / alto) | 64.20 / 65.84 / 75.10% | 63.85 / 65.83 / 75.10% | no (moves stay an option; check off by default) | [E39](#e39--2026-11-04--moving-suspected-overtones-by-default-rejected-overtone-check-off-by-default-pr-78) |
| 2026-11-04 | #74 | CREPE search capped at 1600 Hz again (Basic Pitch keeps the full range) | contour | omnibook, 45 solos | Pitch accuracy | 72.4% (after #69) | 74.3% (74.2% before #69) | yes | [E38](#e38--2026-11-04--range-rules-final-scorecards-pr-74-confirmed-as-the-pitch-line-fix), [E37](#e37--2026-11-04--range-rules-on-the-omnibook-a-pitch-line-regression-from-the-raised-ceiling-fixed-by-pr-74) |
| 2026-11-04 | #69 | Range rules per horn; altissimo search ceiling raised to written A7 | contour + notes | synthetic 72-note phrase (real sets pending) | Note F1, alto / tenor (Basic Pitch) | 92.6 / 89.6% | 100 / 100% | yes | [E34](#e34--2026-11-04--range-rules-per-horn-altissimo-kept-unplayable-notes-moved-by-octaves-pr-69-merged) |
| 2026-11-04 | #66 | Triplet or plain feel chosen per phrase on fast beats | notation | Weimar, 444 solos | Position read (up tempo); triplets × Weimar | 65.9% (74.8%); 1.37× | 67.4% (77.0%); 0.76× | yes | [E33](#e33--2026-11-04--triplet-or-plain-feel-chosen-per-phrase-on-fast-beats-pr-66-merged) |
| 2026-11-04 | #64 | Sextuplet and 32nd grids on slow or busy beats; swing read from one- or two-note beats | notation | Weimar, 444 solos | Position read (ballads) | 63.1% (16.9%) | 65.9% (36.2%) | yes | [E32](#e32--2026-11-04--sextuplet-and-32nd-grids-for-slow-and-busy-beats-pr-64-merged) |
| 2026-11-04 | #61 | Demucs with two averaged shifts by default | isolate | omnibook-mix / Blues for Mary Jane | Note F1 | 57.1 / 53.1% | 57.9 / 55.0% | yes | [E30](#e30--2026-11-04--separator-comparison-round-2-clean-ups-after-demucs-and-other-separators-pr-61-merged) |
| 2026-11-03 | #57 | Restore re-tongued repeats (loudness dip ≥ 10 dB before the attack) | notes | urmp (all sets in E29) | Onset recall (89.1% before #52); note F1 | 74.5%; 69.0% | 81.9%; 68.8% | yes | [E29](#e29--2026-11-03--full-scorecards-for-re-tongued-repeats-pr-57-merged) |
| 2026-11-03 | #52 | Shortest note follows the take's tempo, fast-passage safeguard | notes | bach10 / choralebricks / grfia-alto / urmp / omnibook | Note F1 (URMP onset recall 89% → 75%: fidelity fix pending) | 87.5 / 77.8 / 66.5 / 64.4 / 64.2% | 97.3 / 91.8 / 75.8 / 69.0 / 64.2% | yes, conditional | [E23](#e26--2026-11-03--full-scorecards-for-the-adaptive-shortest-note-pr-52-merged) |
| 2026-11-03 | #44 (open) | Chromatic runs spelled with sharps going up, flats going down | notation | Blues for Mary Jane | Spelling | Ab where the book has G# (E18) | to check | — | [E18](#e18--2026-11-03--blues-for-mary-jane-pdf-against-austins-transcription-first-two-choruses-qualitative) |
| 2026-11-03 | #43 | No sax-span cut where Demucs moved the horn into another melodic stem | isolate | older take | Wrong cuts | 1 (8 s) | 0 | yes | [E16](#e16--2026-11-03--write-only-where-the-sax-plays-pr-35-merged) |
| 2026-11-03 | — | First full run on GRFIA-RealSax (provisional; baseline, not a change) | all | grfia-alto / grfia-tenor, ~950 takes | Note F1 / pitch | — | 58 / 84% alto, 54 / 85% tenor | — | [E20](#e20--2026-11-03--grfia-realsax-full-scorecards-alto-and-tenor-provisional) |
| 2026-11-03 | #35 | Write only where the sax plays | isolate + notation | omnibook-mix (7XTyc); Blues for Mary Jane | Note F1 on 7XTyc; answer-key notes lost to cuts | 56%; — | 62%; 0 | yes | [E16](#e16--2026-11-03--write-only-where-the-sax-plays-pr-35-merged) |
| 2026-11-03 | #34 | Blues-aware key finder | notation | Weimar, 429 solos | Home key right | 49.3% (blues 46.7%) | 60.0% (blues 69.6%) | yes | [E15](#e15--2026-11-03--key-finder-that-hears-the-blues-pr-34-merged) |
| 2026-11-03 | #32 | Syncopations as one note | notation | Parker 7XTyc | Ties | 46 | 41 | yes | [E14](#e14--2026-11-03--syncopations-as-one-note-instead-of-tied-eighths-pr-32-merged) |
| 2026-11-03 | #29 | Beat from the notes on lone sax | notation | Parker 7XTyc | 32nd notes / plain eighths | 80 / 88 | 1 / 231 | yes | [E13](#e13--2026-11-03--beat-taken-from-the-notes-on-lone-sax-pr-29-merged) |
| 2026-11-03 | #26 | Off-grid points moved to sixteenths | notation | Blues for Mary Jane | Files MuseScore refuses | 1 | 0 | yes | [E12](#e12--2026-11-03--readable-notation-on-a-real-recording) |
| 2026-11-03 | #24 | Auto pick of the Demucs stem holding the sax | isolate | omnibook-mix, 10 records | Note F1 / s per min | 50.6% / 110 | 56.4% / 64 | yes | [E11](#e11--2026-11-03--picking-the-sax-stem-from-demucs-pr-24-merged) |
| 2026-11-02 | #22 | Split-note join turned off | notes | urmp / bach10 / choralebricks | Note F1 | 62.8 / 77.1 / 72.1% | 64.4 / 87.5 / 77.8% | yes | [E8](#e8--2026-11-02--split-note-join-pr-10-before-and-after) |
| 2026-11-02 | #21 | Readability pass | notation | synthetic swing solos | Swung eighths misplaced / triplets right | ~33 / ~4 | ~3 / ~45 | yes | [E7](#e7--2026-11-02--notation-readability-pass-on-synthetic-swing-solos-pr-21-merged) |
| 2026-11-02 | #16 | Grade only inside the answer key's span (grading fix, not a model change) | scorecard | omnibook, 45 solos | Note F1 / onset F1 | 45.0% / 60.4% | 64% / 86% | yes | [E6](#e6--2026-11-02--omnibook-re-graded-inside-each-answer-keys-span-pr-16) |
| 2026-11-02 | #15 | Never drop notes without a beat grid | notation | Parker solo PDF | Notes written | 42 of 398 | 398 of 398 | yes | [E5](#e5--2026-11-02--first-real-pdf-render-finding-not-a-scorecard) |
| 2026-11-02 | #10 | Join notes Basic Pitch splits | notes | urmp / bach10 / choralebricks | Note F1 | 64.4 / 87.5 / 77.8% | 62.8 / 77.1 / 72.1% | no (off in #22) | [E8](#e8--2026-11-02--split-note-join-pr-10-before-and-after) |
| 2026-11-02 | #6 | CREPE Notes style cutter vs Basic Pitch | notes | omnibook, 45 solos | Note F1 | 64.2% (Basic Pitch) | 59.8% (cutter) | no | [E9](#e9--2026-11-02--omnibook-three-note-tools-graded-inside-the-key-span) |

## Summary: best result so far per set

| Set | Pitch | Onset F1 | Note F1 | Note F1 no offset | s/min | Targets | Run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bach10 | 96.9% | **92.2%** ✓ | **97.3%** ✓¶ | 92.2% | 21 | solo | E4, E29 |
| choralebricks | **98.9%** ✓ | 86.7% | **90.3%** ✓¶ | 86.5% | 22 | solo | E4, E29 |
| urmp | 94.4% | 81.6% | 68.8%¶ | 80.8% | 24 | solo | E3, E29 |
| omnibook | 74%† | **86%** ✓ | **64.2%** ✓ | — | — | mix | E6, E9 |
| urmp-mix | 41.6% | 48.9% | 17.1% | 35.4% | 27 | mix | E3 |
| omnibook-mix (10) | — | — | 57.6%¶ | — | 64 | mix | E11, E29 |
| grfia-alto (~950 takes with tenor) | 90.0% | 79.1% | 75.2%‡¶ | 78.5% | — | solo | E22, E29 |
| grfia-tenor | 87.2% | 75.1% | 66.1%‡¶ | 73.8% | — | solo | E22, E29 |
| bfmj-austin (Getz, 35 s, 136 notes) | — | 80% recall¶ | 56%¶ | 70% | — | mix | E19, E29 |
| pfh-austin (Getz, tenor, 169 bars, 867 notes) | 69.3% | 75.1% | 50.3% | 66.5% | — | mix | E40 |
| resolution-austin (Coltrane, tenor, 939 notes) | 85.4% | 63.1% | 41.7% | 55.8% | — | mix | E53 |
| isnt-she-lovely-austin (solo, 319 notes) | 52.1% | 62.7% | 24.6% | 36.3% | — | mix | E53 |
| bloody-well-right-austin (174 notes) | 67.3% | 50.4% | 21.0% | 34.8% | — | mix | E53 |
| walkers-theme-austin (863 notes) | 0 (70.4%*) | 0 (61.7%*) | 0 (28.2%*) | 0 (47.6%*) | — | mix | E53 |
| weimar-tenor (6 solos, 11,729 notes) | 72.2% | — | 65.6% default after #102 (76.3% on Riley & Dixon's pipeline, E58) | 66.4% | — | mix | E56, E58 |
| bach10-mix | 21.4% | 39.5% | 3.9% | 29.2% | 31 | mix | E4 |

† Understated by octave errors in some Omnibook answer keys (E10); about 87% on solos with sound keys.

¶ Current default, after PRs #52 and #57 (E29); other columns from the earlier run. Provisional: onset recall is still 1–7 points below where it was before #52 (URMP 89% → 82%), a fidelity regression being fixed.

‡ GRFIA with the final answer keys (PRs #46 and #47, E22).

Omnibook now uses chorus-limited grading (PR #16, E6); the earlier 45% note F1 (E2) was understated.

\* Walker's Theme with the sax-span cut ignored; the default hides every note (E53 bug).

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

### E28 — 2026-11-03 — Rhythm scorecard on the new swing-aware measure (after PR #55)
- **What**: the E24 Weimar rhythm run repeated on main `78063ad` with `position_read` as the headline: a swung off-beat written as a swung eighth now counts as read right ([protocol](protocol.md#rhythm-scorecard-weimar-no-audio)). Nothing in the transcriber changed; this is the yardstick. Cards: `~/saxscribe-runs/rhythm/wjd-rhythm-all-20261103-123353.json` and `wjd-rhythm-sax-all-20261103-123430.json`.
- **Result**: position read **63.1%** on all 444 solos, **57.6%** on the 259 sax solos (exact position was 58.7% and 53.6%). Every other measure is the same as E24: exact 58.7 / 53.6, slot 58.9 / 53.9, beat 89.3 / 87.0, busy 0.94× / 0.96×.

| Feel | All: position read (solos) | Saxes: position read (solos) |
| --- | --- | --- |
| Swing | 63.4% (350) | 58.9% (203) |
| Two-beat | 81.1% (32) | 68.1% (5) |
| Latin | 61.7% (26) | 62.6% (23) |
| Funk | 56.9% (20) | 56.5% (15) |
| **Ballad** | **16.9% (10)** | **16.9% (10)** |

| Tempo | All: position read (solos) | Saxes: position read (solos) |
| --- | --- | --- |
| Up | 78.3% (197) | 76.2% (103) |
| Medium up | 65.0% (92) | 61.1% (48) |
| Medium | 51.7% (85) | 48.5% (52) |
| Medium slow | 47.4% (31) | 43.6% (23) |
| **Slow** | **19.5% (39)** | **18.3% (33)** |

- **Reading**: the swing fix moves the headline by about 4 points and leaves the shape alone. Accuracy falls steadily with tempo, and slow tunes and ballads (17–20%) stay the clear gap (E24 finding 2). They are the next rhythm target.
- Not a model change; not in the change table.

### E66 — 2026-11-05 — Straight sixteenth runs kept straight in swung tunes (PR #112, merged)
- **Status**: merged 2026-11-05 19:20Z (11:20 am Pacific); on by default.
- **Change**: in a swung tune, a beat with at least 3 notes, each within 0.2 of a sixteenth slot as played, is now written straight instead of swung. This fixes the "swing bends straight 16ths" fault found on Pennies From Heaven (E61).
- **Rejected first version**: a beat with more than 2 notes written straight. It also straightened swung eighths with a pickup: 168 of 444 solos got worse, and Walker's Theme lost 5 points.
- **Tuning set**: the Weimar rhythm scorecard (444 solos).

| Measure | Before | After |
| --- | --- | --- |
| Position read | 67.26% | 67.85% |
| Exact | 61.47% | 62.08% |
| Solos better / worse | — | 183 / 20 (worst −1.6 points) |

- **Held-out records, scored once** (notes in the right place):

| Record | Before | After |
| --- | --- | --- |
| Pennies From Heaven, Filosax app take | 578 of 734 | 589 of 734 |
| — bars 85–92 | 28 of 52 | 41 of 52 |
| — misplacements caused by the quantizer | 78 | 67 |
| Pennies From Heaven, standard take | 544 of 691 | 544 of 691 |
| Resolution | 293 | 293 |
| Walker's Theme | 274 | 277 |
| Isn't She Lovely | 36 | 36 |
| Bloody Well Right | 42 | 42 |

- Note F1 is unchanged (notation only). No `experiments.jsonl` rows, since this is a rhythm-only measure.
- **Next**: development pauses after each step until Austin says go.

### E65 — 2026-11-05 — Half-time beat grids: diagnosis and a doubling rule (not adopted)
- **Setup**: Mac, main `2369603`, the E58 takes, with bar references from the barline keys (E63).
- **Finding**: Beat This! follows long stretches at exactly half the tempo. Share of the take in half time: Calypso take 1 58%, Calypso take 2 55%, Item 1 27%, Impressions 1961 13%, Impressions 1963 13%. The true tempo there is 190–300 BPM. All of these beats come from the tracker itself, not from the grid mending added in #109, and the beat spacing is steady across the change, so the tracker gives no warning.
- **Signal**: the gap between the notes' own beats divided by the grid spacing. Median 0.50 in half-time stretches, 0.97 where the grid is right.
- **Rule tried**: double the grid where that ratio is 0.42–0.58 (signal strength at least 0.35) for 16 beats or more, and only if the doubled tempo is at most 330 BPM. Tuned on Calypso takes 1–2, Confirmation and 7XTyc.

| Set | Bars right, before | After |
| --- | --- | --- |
| Tuning records | 44.5% | 58.0% |
| Calypso take 1 | 52% | 87% |
| Calypso take 2 | 52% | 72% |
| Held-out records | 54.1% | 54.1% |

- **Why rejected**: a line of straight eighths at the right tempo gives the same ratio. Synthetic straight-eighth lines at 90, 120 and 129 BPM, and the 120 BPM test fixture, were all doubled wrongly. From the notes alone, straight eighths can't be told apart from a half-time grid, so the rule would break pop and straight-feel tunes.
- **Next**: a "double the tempo here" control in the editor, so the player marks the stretch by hand. Development paused on Austin's word (2026-11-05 18:39Z, 10:39 am Pacific).

### E64 — 2026-11-05 — Bar lines kept on the right beat (PR #109, merged)
- **Status**: merged 2026-11-05 16:50Z (8:50 am Pacific); now the default for every take.
- **Change**: bars now follow most of the beat tracker's downbeats rather than counting every 4th beat from the start, and the beat grid is mended where it slips (E63). Tuned on practice records, with Austin's tunes held out.
- **Result**, share of bars in the right place, measured on the Mac from the branch:

| Set | Before | After | Offline simulation |
| --- | --- | --- | --- |
| Tuning records | 44.2% | 75.1% | 76.9% |
| Held-out records (includes Austin's tunes) | 34.1% | 58.0% | 60.9% |
| Pennies From Heaven | 0.6% | **87.5%** | — |

- **Per set**, bars right before → after, as shown on the Results page (PR #114, merged): Pennies From Heaven 1 → 88%, Parker 62 → 90%, tenor tunes 29 → 51%, Weimar solos 12 → 37% (still low from half-time grids, E65).
- Fixed records: Parker 1p64c, 6Cbwc and 73bwc, Pennies From Heaven, Isn't She Lovely. No record gets worse by more than 5 points.
- **Still open**: half-time beat grids (Calypso, Item 1, Impressions; automatic fix rejected in E65), and swing applied to straight 16ths.
- **Data**: the PR also brings the Mac's E57–E60 rows into `experiments.jsonl`. They replace the 33 overnight rows and the five E59 rows written from the log, and the set "tenor-tunes" becomes "new-tunes". Guard counts and rates (`extras_in_rests_per_min`, `rest_seconds`, `short_notes`, `ghost_notes`) sit in a separate `guards` field, so `metrics` holds shares only.

### E63 — 2026-11-05 — Barline check on 22 records (finding, no change yet)
- **Setup**: the bar positions written by the tool were compared with known bar positions on 22 records: the Parker records, the six Weimar solos and Austin's six keys.
- **Result**: barlines are wrong on 13 of 22.
  - Pennies From Heaven is the only whole-tune 2-beat shift: the beat tracker locks on beat 3.
  - Three Parker records are off by one beat throughout.
  - Most of the others have a tempo grid that slips: it drops to half time (Impressions, Item 1, both Calypso takes) or gains and loses beats. Because barlines are placed every 4th beat, they drift.
- **Cues tried**: chord changes, bass hits and the starts of long notes were each tried as barline cues. None beat the beat tracker's own downbeats.
- **Next** (build thread): hold one tempo in the beat grid, then re-sync the bars from all of the tracker's downbeats. It will be tuned on practice records, with Austin's tunes held out as test.

### E62 — 2026-11-05 — "Filosax + Demucs check" hybrid, offline (not adopted)
- **Setup**: offline simulation on the E58/E59 takes. Thresholds were tuned on Confirmation, Calypso 1–2 and the 7 Parker training records; the held-out records were scored once. It tried two ways to use Demucs as a check on Filosax (E61's piano-solo and quiet-sax problems).
- **FILL** (add Demucs notes where the Filosax stem goes quiet): every setting lowers tuning F1; the best scores 76.7% against 77.0%. On Parker 7XTyc it adds 52–67 notes and none are key notes. **Not adopted.**
- **AWAY** (tag Filosax notes where Demucs hears no sax): no effect on the tuning records. Every tagged note falls outside the key spans, because the keys cover solos only, so no setting could be chosen. Held-out score equals E59 (65.1% against E58's 48.7%). On Pennies, a setting of 12 dB for at least 8 s would tag all 70 piano-solo notes plus 3 others. That is descriptive only, since Pennies is a test record.
- **Also tried, little or no effect**: tagging windows where both stems sound chord-like (0 notes tagged); disagreement between the two pitch lines (0–9 windows per record); energy at each note's own pitch, which was no better than overall loudness.
- **Blocker**: tuning AWAY needs keys that mark where the sax rests across the whole record, not just the solo. The build thread has asked Austin for rest times on a few records.

### E61 — 2026-11-05 — Pennies From Heaven in the app with Filosax (test): notes better, rhythm shared, piano solo leaks
- **Setup**: Austin's own app run of Pennies From Heaven with the "Filosax (test)" note finder after #103 merged (main `0d15200`). Read-only analysis by the build thread against his 867-note key. (E60 is reserved for the guard-metric comparison, still running.)
- **Notes**:

| Path | Note F1 | No offsets | Sax found | Sax purity |
| --- | --- | --- | --- | --- |
| App, Filosax (test) | 57.1% | 71.1% | 73.0% | 69.3% |
| CLI, Filosax (E59) | 56.8% | — | — | — |
| Standard (Demucs + ours) | 50.1% | — | — | — |

- **Rhythm, shared by both paths**:
  - Every barline is 2 beats off; this is a downbeat-finder problem, already seen in E40. Allowing for that shift, 78.7% of matched notes are placed right on both paths.
  - Bars fully right: 62 of 166 with Filosax, 42 of 166 standard.
  - Misplaced notes, Filosax / standard: wrong subdivision chosen by the quantizer 50% / 44%; onset more than 50 ms off 32% / 37%; beat grid 18% / 18%.
  - Worst stretches: bars 85–92, a straight 16th run bent by swing 0.66; bars 1–8, where the grid starts one beat short; bars 126–133, triplets written as eighths.
- **Quiet sax** (4 stretches, 56 key notes): Filosax finds 20, standard 28. Of Filosax's misses there, 21 are lost in the separator and 15 by the transcriber. In bars 82–84 the Filosax stem holds the sax at −28.5 dB of the mix; Demucs holds it at −3.6 dB.
- **Fidelity problem, piano solo (3:42–4:21)**: Filosax writes 64 piano notes. The standard path hides them; the bleed check (ADR-0034) can't, because the Filosax stem keeps the piano near sax level and the pitch line stays voiced. A fix needs a rival-stem signal, such as running Demucs's stems alongside Filosax.
- **Next** (build thread): fix the 2-beat barline shift, then stop swing bending straight 16ths, then test Demucs alongside Filosax for the piano solo and quiet spots.

### E60 — 2026-11-05 — Guard check on the Filosax jump: real gains, not dropped notes
- **Question**: does Filosax's rise on Weimar (57 → 77% note F1) come from leaving notes out (ADR-0016)?
- **Setup**: the existing takes were rescored with PR #106's guard metrics, without transcribing again. The two setups are (a) Demucs + ours (E58) and (b) Filosax separator + transcriber (#103 CLI, E59). Scoring commit `1bbb126`. A note under 0.12 s counts as short. A gap of at least 0.25 s in the key counts as a rest. 32 rows were written to the Mac's `experiments.jsonl`.
- **Result**, (a) / (b):

| Set | Note F1 | Short notes found | Notes in rests per min | Note F1 at 100 ms |
| --- | --- | --- | --- | --- |
| Weimar solos (6) | 57.3 / **76.9%** | 55.4 / **76.2%** | 12.6 / **1.0** | 67.5 / **84.6%** |
| Pennies From Heaven | 50.1 / **56.8%** | **71.7** / 70.5% | 48.6 / **17.7** | 74.3 / **80.5%** |
| Blues for Mary Jane | **56.2** / 48.6% | **57.9** / 42.1%* | **0** / 17.3* | 79.7 / **84.8%** |
| Four tenor tunes | 32.5 / **35.9%** | 37.0 / **42.4%** | 94.8 / **77.0** | — |

\* Small samples on Blues for Mary Jane: 3 of only 19 short notes, and 1 note in 3 s of rest.

- **Answer**: the Weimar jump is real. Filosax finds more short notes and writes far fewer notes in rests. Every solo improves on both guards except Impressions 1963, where notes in rests go from 1.7 to 2.5 per minute. Blues for Mary Jane is the exception: it loses a few quick notes. On the four tenor tunes, ghost notes found are 4.6 / 6.9% (only 19 marked).
- **Caveat**: most notes in the Weimar keys are short, so short found is close to found overall.
- **Next** (build thread): tune "Filosax + Demucs check", for piano solos and quiet sax (E61), on training records only, with Austin's tunes held out as test.

### E59 — 2026-11-05 — Filosax separator and transcriber as opt-in settings (PR #103, merged)
- **Change**: adds `--separator filosax` and `--notes-tool filosax` to the CLI, and a "Filosax (test)" note finder in the app. It is off by default and the default pipeline is unchanged. Model card: `docs/models/filosax.md` (in the PR).
- **Setup**: the branch's own CLI path on the Mac, commit `7708267`, Filosax separator + Filosax transcriber.
- **Result**, note F1:

| Set | Branch | Riley & Dixon run (E58) |
| --- | --- | --- |
| Weimar solos (6) | 76.9% | 76.3% |
| Parker band records (10) | 67.5%* | 67.2%* |
| Pennies From Heaven | 56.8% | 57.7% |
| Blues for Mary Jane | 48.6% | 52.0% |
| Four tenor tunes | 35.9% | 36.1% |

\* The Omnibook keys may favour this model (E58).

- **Reading**: the in-app path matches the experiment within about 1 point. The exception is Blues for Mary Jane, where 3.4 points is separator run-to-run variation (about 2 of its 136 notes). The one-line rule moves any record by 0.5 points at most.
- **Status**: merged as PR #103 (2026-11-05 15:16 UTC), off by default.
- **Speed**: 40–74 s per minute of audio end to end. That is within the full-mix target of 60 s on some records and over it on others.

### E58 — 2026-11-05 — Riley & Dixon head-to-head: Filosax sax separator and their sax transcriber
- **Setup**: Riley and Dixon's Filosax-trained models (arXiv 2405.16687; MIT): the sax separator `xavriley/demucs_v3_saxophone_separation` and the sax transcriber (`filosax_25k.pth`). Run locally in a separate environment on current main, with Demucs's sax-span cuts applied to every setup. 16 records outside Weimar, then the six Weimar solos. Full table on the Mac: `~/saxscribe-runs/exp/2026-11-06-rd/rd_scores.json`.
- **Parker band records (10)**, note F1 (no offsets / sax found / sax purity):

| Separator + note finder | Note F1 | No offsets | Sax found | Sax purity |
| --- | --- | --- | --- | --- |
| Demucs + ours (app today) | 58.2% | 73.3% | 73.4% | 73.4% |
| Mega + ours | 61.3% | 75.6% | 73.4% | 77.9% |
| MVSep website + ours | 62.1% | 76.0% | 74.6% | 77.7% |
| Filosax separator + ours | 62.6% | 77.1% | 76.5% | 77.9% |
| Filosax separator + their transcriber | 67.2%* | 79.9% | 79.7% | 80.3% |
| Demucs + their transcriber | 62.4% | 76.8% | 74.8% | 80.1% |

\* Inflated by an unknown amount: the paper (section 3.1) says the Omnibook keys' onsets were refined against a transcription model's frame activations, so their transcriber is partly graded on its own kind of output. Judge it on the records below and on Weimar.

- **Other records**, note F1:

| Setup | Pennies From Heaven | Blues for Mary Jane | Four tenor tunes (note-weighted) |
| --- | --- | --- | --- |
| Demucs + ours | 50.1% | **56.2%** | 32.5% |
| Mega + ours | 57.2% | 52.4% | — |
| MVSep website + ours | **58.2%** | 51.8% | — |
| Filosax separator + ours | 54.7% | 52.2% | **37.3%** (pitch 57.0 → 62.3%) |
| Filosax separator + theirs | 57.7% | 52.0% | 36.1% |
| Demucs + theirs | 53.9% | 48.8% | 34.6% |

| Tenor tune | Demucs + ours | Filosax sep + ours | Filosax sep + theirs |
| --- | --- | --- | --- |
| Resolution | 42.5% | 46.2% | **47.9%** |
| Isn't She Lovely | 25.7% | **35.9%** | 34.5% |
| Bloody Well Right | 11.6% | 18.6% | **19.0%** |
| Walker's Theme | 28.3% | 31.9% | 27.4% (Mega 34.0%, website 34.1% best) |

- **Reading**:
  - The Filosax separator beats Demucs on 15 of 16 records with our note finder; Blues for Mary Jane is the exception.
  - It is fast: about 7 s per minute of audio on the Mac, against about 210 s for Mega. That makes it the strongest separator candidate so far.
  - Their transcriber wins on clean jazz sax and is about even on pop and fusion.
  - The sax-span cuts barely change it.
- **Weimar rows** (added 10:03 UTC): six solos, 11,729 notes, note-weighted. The Weimar keys are human transcriptions with no Riley & Dixon involvement, so these are free of the Omnibook caveat.

| Setup | Note F1 |
| --- | --- |
| Demucs + ours, main sax cuts | 57.3% (pitch 72.2%) |
| Demucs + ours, #102 sax cuts | 65.6% |
| Filosax separator + ours, main cuts | 60.2% (pitch 77.9%) |
| Demucs + their transcriber, main cuts | 61.7% |
| Filosax separator + theirs, main cuts | 66.4% (purity 87.7%) |
| Filosax separator + theirs, no sax cuts | **76.3%** (no offsets 82.4%, found 78.2%, purity 87.5%) |

| Solo | Demucs + ours (main) | Filosax sep + theirs (no cuts) |
| --- | --- | --- |
| Confirmation | 78.4% | 88.6% |
| The Everywhere Calypso 1 | 67.9% | 83.0% |
| The Everywhere Calypso 2 | 64.4% | 81.8% |
| Impressions 1961 | 54.8% | 73.1% |
| Impressions 1963 | 50.2% | 66.6% |
| Item 1 | 43.8% | 79.5% |

- **Reading (with Weimar)**:
  - Their transcriber beats ours on every Weimar solo, on the same stem with the same cuts.
  - Their separator helps both note finders.
  - On clean jazz band records their full pipeline is the best measured so far, about 10 points over #102.
  - On pop and fusion it is about even with ours. Mega or the MVSep website wins Walker's Theme, and Blues for Mary Jane still favours Demucs.
  - Mega and the website were not run on Weimar: uploads were approved only for the 13 earlier records.
- **Decision**: not yet; it is Austin's call whether to adopt their pipeline for jazz band records.

### E57 — 2026-11-05 — Sax-span check ignores drums and bass, sums split stems (PR #102, merged)
- **Change** (`sax_spans`): (1) the sax's share is measured against the mix without the drums and bass stems; (2) when Demucs splits the lead across stems, they are summed before the "is the sax playing" rescue; (3) a rest is still marked when another instrument takes over and the old whole-mix test also fails: piano at −10 dB or more of the mix and louder than every sax stem, or bass 16 dB over them. Tuned over four rounds on 33 band takes. Tags only; nothing is deleted.
- **Result**, note F1:

| Set | Before | After |
| --- | --- | --- |
| Weimar solos (6) | 57.3% | **65.6%** |
| Item 1 (Potter) | 43.8% | 67.4% |
| Impressions 1961 (Coltrane) | 54.8% | 64.7% |
| Impressions 1963 (Coltrane) | 50.2% | 55.5% |
| Parker band records (10) | 60.6% | 60.6% |
| Resolution | 42.5% | 42.0% |
| Walker's Theme | 28.3% | 28.3% |
| Bloody Well Right | 11.6% | 11.4% |

- **Fidelity**: fixes most of E56's wrong cuts on split-stem records. Known sax rests stay mostly cut, with two small leaks: Resolution 154–165 s (about 11 notes) and the end of the Blues for Mary Jane bass solo, 357–368 s (14 notes).
- **Status**: merged as PR #102 (2026-11-05 15:07 UTC).
- Details in the PR body.

### E56 — 2026-11-05 — First Weimar solos with bought audio (main `c06b298`)
- **Setup**: six tenor solos from the five records Austin bought (Weimar datasheet), main `c06b298` (includes #97 and #99), Demucs, default settings. Keys are the Weimar Jazz Database notes aligned to the bought audio; scored inside the alignment spans and weighted by notes, over 11,729 key notes.
- **Result**, all six: note F1 **57.3%**, no offsets 66.4%, onset recall 62.7% / precision 88.7%, sax found 58.0%, sax purity 81.3%, pitch 72.2%.

| Solo | Note F1 | No offsets |
| --- | --- | --- |
| Confirmation (Michael Brecker) | **78.5%** | 87.9% |
| The Everywhere Calypso, solo 1 (Sonny Rollins) | 68.0% | 87.2% |
| The Everywhere Calypso, solo 2 (Sonny Rollins) | 64.4% | 83.7% |
| Impressions, 1961 (John Coltrane) | 54.9% | 62.0% |
| Impressions, 1963 (John Coltrane) | 50.1% | 59.4% |
| Item 1, D.I.T. (Chris Potter) | 43.8% | 48.8% |

- **Fidelity problem**: wrong "sax lays out" cuts (`sax_spans`) hide 2,593 key notes, 22% of the total, all on the three records where the lead was split across two Demucs stems (for example vocals + other on Impressions 1961, guitar + other on Item 1). That is why sax found (58%) is far below purity (81%). Diagnosis running in the build thread.
- **Reading**: Confirmation at 78.5% is the best real band record so far. Without the wrong cuts these solos would likely sit well above the Getz records. The Weimar keys are machine-aligned, not hand-checked, so treat single-solo numbers as approximate.

### E55 — 2026-11-05 — Gated hybrid: Mega sax stem with Demucs fallback (no gain yet)
- **Setup**: the [ADR-0036](../decisions/0036-gated-two-separator-hybrid.md) hybrid, first version. It uses the Mega 53-stem sax stem (E51) and falls back to Demucs where Mega's pitch line goes quiet but Demucs's is voiced. Same records as E51 and E52; sax-span check at the fixed −6 dB bar.
- **Result**, note F1 / onset recall:

| Set | Demucs | Mega | Hybrid |
| --- | --- | --- | --- |
| Pennies From Heaven | 49.2 / 79.5% | 57.2 / 82.8% | 57.2 / 82.8% (no fallback used) |
| Blues for Mary Jane | 56.0 / 80.2% | 52.4 / 75.7% | 52.4 / 75.7% |
| Parker band records (10) | 57.8 / 81.8% | 60.4 / 79.6% | 60.3 / 79.8% (precision 86.9%, pitch 70.5%) |
| Parker 6Cbwc (note F1) | 63.3% | 56.8% | 56.8% |
| Parker BRfYc (note F1) | 41.3% | 38.1% | 37.9% |

- **Finding**: the fallback windows are short (0–35 s) and are not where the losses are. The losses come from the sax-span check. A cleaner sax stem holds a smaller share of the mix, so the fixed −6 dB bar cuts real sax stretches. Mega's cuts are 6Cbwc 0–32, 44–53 and 99–174 s; BRfYc 0–8, 79–103, 120–138 and 177–187 s; Blues for Mary Jane 198–368 s (Demucs cuts 203–293 and 305–368 s there).
- **Decision**: not adopted as is. The fallback rule is not the lever; the sax-span bar is.
- **Follow-up** (same day): PR #97's per-record bar (E54) does not change the Mega or website takes. On these clean stems the loud windows sit at −0.4 to −2.8 dB, so the bar stays at −6 dB, and scores are unchanged (Parker Mega 60.5%, website 61.0%; Pennies 57.2 / 58.2%; Blues for Mary Jane 52.4 / 51.8%). The cut passages are quieter ones that the Demucs stem's bleed used to hold above the bar.
- **Next** (build thread): decide the sax spans on the Demucs stem and transcribe from the Mega stem.

### E54 — 2026-11-05 — Sax-span loudness bar set per record (PR #97, merged)
- **Change**: `sax_spans` (PR #35) decides where the sax lays out on a band record. Before, a window counted as sax only if the sax stem held at least −6 dB of the mix. Now the bar comes from the record itself: `max(min(−6, p90(share) − 3), −14)` dB. A record with a loud sax keeps −6 dB; on a quiet mix the bar drops to 3 dB under the record's loud windows, never below −14 dB (a piano solo sits 10–50 dB down). It only changes which notes get the `not_sax` tag; nothing is deleted.
- **Setup**: branch `93791bd` vs main `addb947`, against the stem-timed keys (E53), within each key's span. 27 band takes: 10 Parker records, Pennies From Heaven, Blues for Mary Jane, the four new tenor tunes and 11 URMP mixes.
- **Result**: only Walker's Theme changes. Its bar moves from −6.0 to −9.4 dB, and the cut goes from the whole track (0–241 s) to 0–20, 29–49 and 70–99 s. The other 26 takes keep −6 dB and identical cuts.

| Walker's Theme | Note F1 | No offsets | Onset F1 | Sax found | Sax purity |
| --- | --- | --- | --- | --- | --- |
| main | 0 | 0 | 0 | 0 | 0 |
| PR #97 | 28.3% | 46.9% | 57.2% | 46.8% | 47.0% |

- **Fidelity**: no take gains notes inside a known piano solo (Pennies 3:42–4:21, Resolution's piano stretches). 162 Walker's Theme key notes are still hidden, in 29–49 and 70–99 s, where the sax dips below −9.4 dB; follow-up pending.
- **Status**: merged as PR #97 (2026-11-05 06:23 UTC). A guard added afterwards, PR #99 (merged 06:38 UTC), stops the check from ever tagging more than 80% of a record; it changes none of the 27 takes.
- **Tests**: 160 pass, including two new ones in `tests/test_isolate.py` (a sax mixed about 8 dB low is not cut, which fails on main, and the bar's limits).

### E53 — 2026-11-05 — Four new tenor answer keys, first scores (main `0691a52`)
- **Keys**: four tenor parts from Austin's PDFs, typed by eye (concert = written minus 14 semitones). Resolution (Coltrane, 939 notes, whole record; sax out in bars 1–16, a bass solo, and 84–175, a piano solo), Walker's Theme (Gerald Albright, 863 notes, whole record), Isn't She Lovely (Hornheads, Kenni Holmen's tenor solo only, 319 notes) and Bloody Well Right (Supertramp, John Helliwell, 174 notes: bars 17–18, 47–49 probably in unison with the band, and the solo in bars 69–87). Key timing is a draft, fitted by DTW to the sax stem's pitch line; 66–81% of key notes agree with the pitch heard on the stem. Report: https://claude.ai/artifact/AUNMwoXsCKudesizn1a1PY; files in the project files under `transcriptions/<tune>/`.
- **Setup**: main `0691a52`, default settings, scored within each key's span against the notes shown on the sheet. Two scorings exist. The new-tunes thread used the keys timed on the sax stem (the better timing). The build thread used an earlier version timed on the full mix, and also gives sax found (recall) and sax purity (precision) as on the Results page (PR #90).
- **Result**, keys timed on the sax stem (headline):

| Record | Note F1 | No offsets | Onset F1 | Pitch |
| --- | --- | --- | --- | --- |
| Resolution | 41.7% | 55.8% | 63.1% | 85.4% |
| Isn't She Lovely (solo) | 24.6% | 36.3% | 62.7% | 52.1% |
| Bloody Well Right (solo) | 21.0% | 34.8% | 50.4% | 67.3% |
| Walker's Theme | 0 | 0 | 0 | 0 |
| Walker's Theme, `not_sax` ignored | 28.2% | 47.6% | 61.7% | 70.4% |

- **Result**, keys timed on the full mix (build thread):

| Record | Span scored | Note F1 | No offsets | Sax found | Sax purity |
| --- | --- | --- | --- | --- | --- |
| Resolution | whole record | 23.1% | 41.0% | 44.3% | 38.1% |
| Isn't She Lovely (solo) | 46–102 s | 21.4% | 33.6% | 40.4% | 28.8% |
| Bloody Well Right | 64–272 s | 7.3% | 12.7% | 32.2% | 7.9% |
| Walker's Theme | whole record | 0 | 0 | 0 | 0 |
| Walker's Theme, span cut ignored | whole record | 11.0% | 22.3% | 23.9% | 20.9% |

- **Key timing matters**: on Resolution the same output scores 41.7% against the stem-timed key and 23.1% against the mix-timed one. The draft keys are themselves a source of error until their timing is checked.
- **Walker's Theme bug**: the sax-span check (`sax_spans`, PR #35) keeps only stretches where the sax stem is louder than a fixed −6 dB share of the mix. Here the sax sits about 8 dB under the band (median share −8.2 dB), so every note was tagged `not_sax` and the sheet came out empty.
- **Ranked gaps** (new-tunes thread): the `sax_spans` threshold; other instruments on the sax stem (guitar, vocals and keys on the pop and fusion records, where purity falls to 8%); fast runs; same-pitch splits; altissimo (Isn't She Lovely goes up to written F7).
- **Reading**: all four sit below the Getz records (Pennies 50%, Blues for Mary Jane 56%). Resolution comes closest, with 85% pitch accuracy. These are the hardest test records so far and the clearest case for a sax-specific separator.
- **Next** (build thread): a per-record (relative) loudness bar for `sax_spans` instead of the fixed −6 dB; then all four through the sax-specific separators (E51, E52) and the gated hybrid ([ADR-0036](../decisions/0036-gated-two-separator-hybrid.md)).
- No `results.jsonl` line yet: it will be copied from the Mac's history with the next run that logs these sets.

### E52 — 2026-11-05 — MVSep website Saxophone model (not adoptable)
- **Setup**: the MVSep website's Saxophone model (sep_type 61, a BS-RoFormer, SDR 9.77; no public weights, so audio is uploaded to MVSep). With Austin's OK (00:41 UTC), 12 commercial records were uploaded 01:30–01:47 UTC; the upload log is `~/saxscribe-runs/exp/2026-11-05-sax-id/mvsep_web_uploads.txt` on the Mac. Compared with Demucs and the local Mega 53-stem model (E51).
- **Result**, note F1:

| Set | Demucs | Mega 53-stem (local) | MVSep website Saxophone |
| --- | --- | --- | --- |
| Pennies From Heaven | 49.2% | 57.2% | **58.1%** |
| Parker band records (10) | 57.8% | 60.4% | **61.0%** |
| Blues for Mary Jane | **56.0%** | 52.4% | 50.9% |

- **Parker onset recall / precision**, Demucs / Mega / website: recall 81.8 / 79.6 / 78.4%, precision 81.0 / 87.0 / 86.7%.
- **Fidelity problem**: it loses real playing on two Parker records: BRfYc recall 80.5% → 45.2% (over a third of the solo gone) and 6Cbwc 78.4% → 65.6%.
- **Decision**: not adoptable in the app; it only runs on MVSep's site and it drops real playing.
- **Reading**: both sax-specific models trade fewer bleed notes and better pitch for occasional missed sax passages. The deciding test is a hybrid that falls back to Demucs where the sax stem goes quiet (build thread, running).

### E51 — 2026-11-05 — Sax-specific separator: MVSep open 53-stem model (mixed; not adopted as a swap)
- **Setup**: the MVSep Mega 53-stem model (ZFTurbo Music-Source-Separation-Training v1.0.21, a BS-RoFormer with its own sax stem, MIT licence), run on CPU at about 210 s per minute of audio. Its sax stem replaced Demucs's stem; rerun on main `f64316b`. Output `~/saxscribe-runs/exp/2026-11-05-sax-id/msst_out.txt` on the Mac. Austin approved the test at 00:41 UTC.
- **Result**, note F1 Demucs → Mega sax stem:

| Set | Demucs | Mega sax stem | Other measures |
| --- | --- | --- | --- |
| Pennies From Heaven | 49.4% | **57.2%** | pitch accuracy 68.0% → 73.8% |
| Parker band records (10) | 57.8% | **60.4%** | precision +6.0, recall −2.1, pitch +4.0 points |
| Blues for Mary Jane | 56.0% | 52.4% | recall 80.2% → 75.7% (thins parts of the solo) |

- **Fidelity problem**: on the Parker record 6Cbwc it dropped part of the solo (recall 78.4% → 58.8%). Losing real playing breaks the never-drop rule (ADR-0016), so it is not adopted as a straight swap.
- **Piano stem as a bleed check**: fails. Pennies flags 141 notes, 93 of them real sax; Parker flags 267, 190 real.
- **Reading**: the biggest jump yet on band records, but mixed. Next (build thread): combine the two stems, either the union of their sax spans or a choice per phrase.

### E50 — 2026-11-05 — PANNs instrument tagger as a `not_sax` signal (not adopted)
- **Setup**: PANNs Cnn14 (DecisionLevelMax) scores sax and piano frame by frame; rules hid notes where the piano score was high or the sax score low. Tested on Pennies From Heaven, Blues for Mary Jane and the Parker band records, against #84's pitch-line check (E48).
- **Model**: panns-inference 0.1.1, Cnn14_DecisionLevelMax weights (327,428,481 bytes, md5 starting 70539c43, CC BY 4.0), run on CPU. Output `~/saxscribe-runs/exp/2026-11-05-sax-id/panns_out.txt` on the Mac.
- **Result**:
  - The median piano score is 0.001–0.007 everywhere, even during the confirmed Pennies piano solo (3:42–4:21): it barely hears the piano.
  - The median sax score is only a little higher on real sax than on bleed: Pennies key notes 0.38 vs other notes 0.28; Parker 0.29 vs 0.19.
  - Every rule that hid noticeably more notes threw away about half real notes: on the Pennies mix, sax score under 0.05 hides 100 notes, 44 of them real; on Parker, 369 hidden, 173 real. Rules on the separated stem did worse.
  - Best note F1 per set is still #84's check alone: Pennies 49.9%, Blues for Mary Jane 56.2%, Parker 57.8%.
- **Decision**: not adopted. #84's pitch-line check beats every PANNs rule on all three sets.
- **Next (build thread, running)**: a local sax stem from ZFTurbo's Music-Source-Separation-Training (the MVSep Mega 53-stem open model), then the MVSep Saxophone web model (sep_type 61). Austin approved both in writing at 00:41 UTC, including uploading audio for the web model.

### E49 — 2026-11-04 — Piano notes no longer cut held sax notes short (PR #86, merged)
- **Change** (bleed fix 3 from E46): when a piano note sounds under a held sax note, the sax note keeps its full length instead of being cut at the piano attack.
- **Rule ("hold")**: a note that starts under a held note doesn't cut it while the pitch line stays on the held note. Run with `follow_exp.py` on the Mac, notes layer redone on main `f64316b`; output `~/saxscribe-runs/exp/follow_out.txt`. Branch `claude/held-notes-follow-pitch-line` (153 tests pass).
- **Result**, note F1: Pennies From Heaven 50.0% → 50.1%, Parker band records 57.8% → 57.9%, Bach10 96.8% → 97.0%, ChoraleBricks 90.1% → 90.3%, GRFIA alto 78.5% → 78.6%, GRFIA tenor 66.3% → 66.4%; Blues for Mary Jane, URMP and Omnibook flat. 93 held notes lengthened; of the 64 notes found under them, 2 were real.
- **Dropped variant ("pick")**: letting the pitch line choose between two notes that start together cost Blues for Mary Jane −0.7 points.
- **Status**: merged as PR #86 (2026-11-05 00:27 UTC), with the `test_history` date fix (the fixed "late" run moved to 2099). On band records it only cleans the sheet together with #84, which is still pending merge.

### E48 — 2026-11-04 — Hide piano and bass notes the sax's pitch line doesn't back up (PR #93, merged)
- **Change**: fixes 1 and 2 from the bleed review (E46), on band records only. A stretch where the sax pitch line is unvoiced for 8 s or more is cut from the sax spans, and notes the pitch line never sits on get an `off_line` tag. Those notes come off the sheet but stay in `notes.json`; nothing is deleted (ADR-0016).
- **Scorecard**:

| Set | Note F1 before → after |
| --- | --- |
| Pennies From Heaven (Austin's key; fresh run) | 49.2% → 49.8%; the whole 3:42–4:21 piano solo hidden (65 notes) |
| Parker band records (10) | 57.6% → 57.8% |
| Blues for Mary Jane | 56.0% → 56.2% |
| Solo sets | unchanged (rule applies to band records only) |

- **How** (`layers/bleed.py`, mix takes only): a note gets `not_sax` with a reason. `no_pitch_line` means the pitch line is unvoiced for 8 s or more. `off_line` means the line is voiced for at least 80% of the note but never on its pitch or octave, and more than a semitone away on at least 60% of frames. Scored offline on existing runs; 154 tests pass. [ADR-0034](../decisions/0034-hide-notes-the-pitch-line-does-not-back.md).
- **Fidelity**: at most one real note hidden per set, and it stays in `notes.json`.
- **Status**: merged as PR #93 (2026-11-05 05:21 UTC). #93 is the same code as #84, with main merged in (157 tests pass). #84 was closed without merging at 20:46 UTC on 2026-11-04; Austin did not close it, and it stays closed.
- **Check by ear and eye** (Austin, 2026-11-04 23:57 UTC): the 93 suspect notes on the second staff of the key-vs-suspects MusicXML are not sax, which backs the notes #84 hides.

### E47 — 2026-11-04 — Onset model v2 plus a pitch-confidence dip (not adopted); cheap onset signals ruled out
- **Setup**: split a note only where onset model v2 peaks and CREPE's confidence dips at the same time (E45's next step). Output: `~/saxscribe-runs/exp/split2_out.txt` on the Mac.
- **Result**: best URMP onset recall +0.2 points (bar +3), GRFIA held-out +0.1. At loose settings it costs note F1: ChoraleBricks −1.2 (49 wrong splits against 3 right), Pennies From Heaven −0.6.
- **Why**: CREPE's confidence barely moves on a soft same-pitch re-attack, but it dips on vibrato and on bleed, so the two signs mostly agree in the wrong places.
- **Conclusion**: the cheap signals are all ruled out for the URMP repeat gap: v2 alone (E44), v2 adding notes (E45), and v2 with a confidence dip (this entry).
- **Next (build thread)**: retrain v2 with training targets weighted toward repeats inside held notes, after the piano-bleed test (E46).
- **Not adopted**.

### E46 — 2026-11-04 — Pennies From Heaven: piano and bass in the sax part (review, no change yet)
- **Question (Austin, 11:49 am PT)**: why do piano notes land in the sax part where tenor and piano share a range? Review doc: https://claude.ai/artifact/3yt9mWJbwHkAxrFAgFAbYR; note list `transcriptions/pennies-from-heaven/piano-bleed/suspect-notes.csv` in the project files. Take: `~/saxscribe-runs-pr74/pfh/take` (stem "vocals + other", made before #81).
- **Findings**:
  1. **3:42–4:21 is a piano solo** (confirmed by Austin by ear, 2026-11-05 00:06 UTC: Getz is out and comes back in strong right after): the CREPE pitch line is 0% voiced there (82–86% elsewhere), yet about 65 notes reach the sheet. The sax-span check (#35) cut nothing.
  2. **In the keyed half (bars 1–169), 87 notes in the tenor's range are piano or bass**: 33 in rests of the key, 48 under held sax notes, 6 an octave or fifth below. That is 9% of the 964 notes on the sheet. They cluster on written D5 and G5 (concert C4 and F4), mostly in bars 62–77 and 122–143.
  3. **Separation can't remove them**: Demucs's piano stem is about 58 dB below the sax stem. Oscar Peterson's piano ends up inside "vocals + other" with the sax.
- **Size of the problem**: onset-and-pitch match 66.3% now; 69.9% if all 87 were hidden.
- **Ranked fixes (tag and hide only, never delete; ADR-0016)**:
  1. Sax-span cut when the pitch line is unvoiced for 8 s or more.
  2. An `off_line` tag for notes the CREPE pitch line never sits on. Trial: 66.3% → 67.9%, hiding 48 of the 87 piano notes, but also 9 notes that are in the key. Those 9 real notes need a look before this is adopted.
  3. Where two notes overlap, keep the one the pitch line follows, not the louder one.
  4. Onset model v2 as a check for piano attacks.
  5. Better separation.
- **Next (build thread)**: try 1 and 2 first, then 3.

### E45 — 2026-11-04 — Onset model v2 adding notes where none exist (not adopted)
- **Setup**: following E44, the model may add a note where it fires on a voiced stretch of the pitch line with no note present, pitch from CREPE. Adds only, never drops.
- **Result** (output `~/saxscribe-runs/exp/add_out.txt` on the Mac):
  - Best URMP onset recall +1.2 points (bar +3); best GRFIA held-out +0.6 (bar +1). Note F1 within −0.2 everywhere.
  - Safest variant (threshold 0.7, notes at least 50 ms, plus splitting): note F1 −0.1 to +1.3 across sets; 34 of the 64 added notes were right.
- **Reading**: after this step, the URMP onsets still missed are mostly soft re-attacks inside held notes, not notes in silence. E44's finding (missed starts lie outside kept notes) held for the starts this test could add; what remains is inside notes.
- **Next (build thread, running)**: split only where v2 fires and CREPE's confidence dips at the same time.
- **Not adopted**.

### E44 — 2026-11-04 — Onset model v2 in the pipeline, split-only (not adopted)
- **Setup**: onset model v2 (E41) wired in so it may only split an existing Basic Pitch note at a start it hears; it never removes notes. Scored against main with #74 under the adoption rule (at least +3 points of onset F1 on URMP, nothing worse elsewhere).
- **Result** (output `~/saxscribe-runs/exp/split_below_out.txt` on the Mac):
  - Best URMP onset-recall gain is +0.8 points (the bar is +3), at threshold 0.5 with a 60 ms edge. It costs note F1: URMP −1.3, ChoraleBricks −4.9, Bach10 −1.3.
  - The safest variant (threshold 0.7, 100 ms edge) never costs more than 0.1 points: ChoraleBricks +1.4 note F1 / +1.8 onset recall, URMP +0.3 / +0.5.
  - Does not clear the bar.
- **Why**: most of the starts the model finds and the pipeline misses fall where Basic Pitch has no note at all, so there is nothing to split.
- **Next (build thread)**: add a note where v2 fires on a voiced stretch of the pitch line with no note present, pitch from CREPE (adds only, never drops).

### E43 — 2026-11-04 — No notes below the horn's low note on the sheet (PR #81, merged)
- **Change**: Austin's rule (E40). On soprano, alto and tenor nothing below written low B♭ goes on the sheet, on any take. The pitch search still reaches 2 half steps lower (`BEND_ROOM`), but notes found there are now tagged `not_sax` as well as `below_range` and left off the notation. They stay in `notes.json`. Bari's low A is its lowest note and is unchanged. [ADR-0033](../decisions/0033-nothing-below-the-low-note.md).
- **Scorecard**, rescoring the runs made with #69 (note F1, notes hidden): GRFIA alto +0.03 (8), Omnibook about 0 (3), Pennies From Heaven +0.11 (4).
- **Fidelity check**: on a fresh Pennies run, one hidden note was a real sax note, costing 0.12 points of onset recall. It is still in `notes.json`.
- **Fresh runs on main `80cba98`** (notes redone, compared against #57-era runs):
  - Parker band records (10): 27 notes hidden in 4 records; note F1 57.62% → 57.83%, onset F1 +0.27, onset recall −0.03 (about one hidden note was real).
  - URMP, Bach10, ChoraleBricks and Blues for Mary Jane: unchanged; no notes hidden inside the key span.
- **Side finding, attributed to #69, not #81**: Bach10 note F1 97.32% → 97.04% since #57, even with range rules off. #69 raised Basic Pitch's top frequency to the altissimo ceiling, which lets 1–2 extra high notes through; the same cause as the small loss on very short GRFIA takes (E38).
- Housekeeping: the Blues for Mary Jane app library take had been removed from `~/saxscribe-library`; it was re-run from the same mp3.

### E42 — 2026-11-04 — Joining held notes split at small dips (not adopted)
- **Goal**: fix the biggest Pennies From Heaven gap (E40): held notes split into same-pitch repeats at a small loudness dip.
- **Rule tried**: join same-pitch neighbours when the dip between them is under 1–6 dB, with or without a check that no new attack is heard. Output: `~/saxscribe-runs/exp/join_out.txt` on the Mac.
- **Result**:
  - Pennies From Heaven, dip under 2 dB plus the attack check: note F1 50.3% → 51.5%, onset recall −1.0 point, and 10 of 38 joins wrong (real repeated notes merged).
  - GRFIA tenor: +0.8 points, 1 wrong join.
  - URMP, ChoraleBricks and the Omnibook: real repeated notes merged at every threshold, about 45–50% of joins wrong.
- **Decision**: not adopted. Merging real repeats loses notes, which the fidelity rule forbids (ADR-0016). Next idea (build thread): only join where the onset model v2 (E41) hears no new start; that test is running.
- **Run-to-run note**: the Pennies key is now on the Mac (`~/saxscribe-runs/keys/pfh/`, JSON and MIDI). The app library take reproduces the E40 card exactly (50.3%); a fresh run of main scores 49.2%, so Demucs varies by about 1 point between runs on this record.

### E41 — 2026-11-04 — Onset model v2, trained with reverb, bleed and soft attacks (standalone; not adopted yet)
- **Change from v1 (E35, E36)**: same small CRNN, retrained with room reverb, bleed from other instruments and softer attacks mixed into the training audio. Existing datasets only; none of Austin's takes. Finished 18:04 UTC. Report: `~/saxscribe-runs/exp/2026-11-04-onset-model-v2/report.txt` on the Mac. Card: [onset-crnn](../models/onset-crnn.md).
- **Threshold**: 0.5 is the new default; the 0.6 picked on training data was too strict.
- **Result**, onset F1 at threshold 0.5 (mir_eval, 50 ms):

| Set | v1 | v2 | librosa detector |
| --- | --- | --- | --- |
| URMP | 38.9 (recall 29.7) | **75.4** (recall 79.3) | 65.3 (recall 81.5) |
| Bach10 | 77.8 | 77.3 | 68.4 |
| ChoraleBricks | 61.4 | **69.9** | 53.0 |
| GRFIA alto test | 75.4 | 75.8 | 58.5 |
| GRFIA tenor test | 73.4 | 74.3 | 60.9 |

- **Same-pitch repeats found**: URMP 19.6% → 72.3%, ChoraleBricks 64% → 97.7%.
- **URMP takes that blinded v1**: Miserere 89%, Jerusalem 86%, March 62%; weakest is Surprise (trumpet bleed), 29%.
- **Reading**: the augmentation fixed the blind spot. v2 now beats v1 and the plain detector on every set except Bach10 (level with v1). URMP recall is still 2 points under the plain detector. GRFIA test tunes share the player with training, so those two rows flatter it. These are detector scores, not transcription scores: the model is not in the pipeline yet.
- **Fidelity check for the next step**: it will be wired in split-only (it may add note starts, never remove notes, ADR-0016) and scored against #74 under the adoption rule. Pennies From Heaven is being added to that scorecard. That matters because the biggest error there (E40) is the opposite one: 118 held notes already split at small dips. A splitter must not add to those.
- **Not adopted yet**.

### E40 — 2026-11-04 — Second personal answer key: "Pennies From Heaven" (Getz with the Oscar Peterson Trio, tenor)
- **Key**: Austin's printed transcription, verified first half typed in by hand: 169 bars, 867 notes; 87% of key notes confirmed by the heard pitch. Key and a note-by-note differences CSV are in the project files (`transcriptions/pennies-from-heaven/`); Mac copy at `~/saxscribe-runs/keys/pfh/` (pending). Audio stays private on the Mac. Full report: https://claude.ai/artifact/716Zp2PXCrsVk7sCwreG2d
- **Tool**: main `4ed61f2` (#69 range rules, #74), default settings, band record through Demucs.

| Measure | Pennies From Heaven | Blues for Mary Jane (E29) |
| --- | --- | --- |
| Note F1 | 50.3% | 54.4% |
| Note F1 without offsets | 66.5% | 70.1% |
| Onset F1 | 75.1% (recall 80.7%) | 76.9% |
| Pitch accuracy | 69.3% | 72% |
| Octave errors | 2 of 867 | 0 |

- **Gaps, largest first**:
  1. **118 held notes split into repeats** of the same pitch at a small loudness dip (about 1.7 dB, far under #57's 10 dB re-tongue rule). Merging them would lift note F1 without offsets to about 71%. This is the opposite failure to the soft re-tongued repeats #57 restores, so a fix must tell the two apart, not just lower or raise the threshold.
  2. **85 missed notes**, 78 of them in fast runs; 41 clearly audible on the record.
  3. **Scoops**: 19 notes take the pitch from the start of a slide (wrong pitch), and about 25 ghost notes 1–2 semitones below the target.
  4. **Barlines 2 beats off** from the key; with a 2-beat shift, 97% of notes land on the right beat (notation, not scored by note F1).
  5. About 70 ghost notes in rests or shorter than 90 ms.
  6. 63 timing errors of 50–150 ms.
  7. **14 notes below the horn's range**, all written A3, a half step below tenor low B♭, shown in red (spotted by Austin). 4 fall in rests in the key (two before bar 1, bar 6 beat 3, bar 169 beat 3), 1 is a 90 ms blip at bar 98, and 9 are in the closing solo, where another instrument plays. They sound as concert G2, last 60–440 ms, and sit at 0.55, 0.91, 8.72, 130.0 and 221.52 s in the keyed half and at 223.7, 225.0, 232.7, 244.8 (twice), 246.2, 246.3, 260.6 and 304.5 s in the closing solo. They are almost certainly piano or bass. `ranges.apply` tags them `below_range` and keeps them, because the #69 rule leaves 2 half steps of bend room under the lowest key (`BEND_ROOM`) for a lipped-down or flat note. **Austin's rule (2026-11-04, 11:24 am PT)**: no notes below written low B♭ on soprano, alto or tenor, on any take. The bend room goes for those horns. Notes below are kept in `notes.json`, tagged `not_sax`/`below_range`, and left off the sheet; never deleted (ADR-0016). Bari's low A is its bottom note and is unaffected. Code: PR #81 (scorecard to follow).
- **Reading**: the tool does a little worse here than on Blues for Mary Jane, for the same reasons as other band records: separation leaves a busier stem, and Getz's legato and scoops trip the note cutter. The split-held-note and fast-run gaps are the biggest wins; neither may drop real notes (ADR-0016). Not a model change; not in the change table.

### E39 — 2026-11-04 — Moving suspected overtones by default: rejected; overtone check off by default (PR #78)
- **Question**: with the range rules (PR #69), should notes tagged `overtone` be moved down to the lower note by default (`--range-rules overtones`) instead of only tagged (`--range-rules out`)? Run on the Mac at main `4ed61f2` (with #69 and #74), 16:11–16:32 UTC.

| Set | Note F1, default → overtones moved | Moved notes the key could judge: agrees with lower note / with note as heard |
| --- | --- | --- |
| Omnibook (45 solos) | 64.20% → 63.85% (without offsets 78.79% → 78.30%) | 6 / 116 |
| GRFIA tenor (473 takes) | 65.84% → 65.83% | 0 / 11 |
| GRFIA alto (479 takes) | 75.10% → 75.10% | 0 / 2 |

- **What the tag got right**: 678 notes were flagged as overtones. Where the answer key could judge (135 of them), it backed the overtone reading 6 times and the note as heard 129 times. As a tag it points at the wrong note about 95% of the time.
- **Decision**: don't move overtones by default. PR #78 goes further and turns the overtone check off in the default mode (`out`), so no `overtone` tags are added there: a tag that is wrong 95% of the time would mislead editing and pollute edited takes saved as training data. `--range-rules overtones` and `flag` still run the check, for later tuning; the Omnibook solos with wrong moves (wkTyc, N3fYc, V3fYc, KRfYc) are the study set. Notes above the altissimo range still use the spectrum to choose between an octave and an octave-and-a-fifth move.
- **Scores**: unchanged by #78, since the default never moved overtone notes and tags are not scored. Tag counts in E38 (599 `overtone` on the Omnibook) no longer apply to the default.
- **Reading**: the spectrum test behind the tag is too loose to act on. Tightening it is a possible follow-up, not scheduled. Recorded as [ADR-0032](../decisions/0032-overtone-moving-rejected.md).

### E38 — 2026-11-04 — Range rules final scorecards; PR #74 confirmed as the pitch-line fix
- **Omnibook** (45 solos, confirmed on the Mac at main `4ed61f2`), before #69 / with #69 / with #74: pitch 74.2% / 72.4% / **74.3%**; chroma 76.1% / 74.1% / 76.1%; note F1 64.2% throughout. Tags with #74: 599 `overtone`, 240 `altissimo`, 48 `below_range`. The three solos that dropped (N3fYc, S5VYc, 9THwc) are back within 0.5 points of their numbers before #69. Note and onset F1 unchanged (64.2%, 85.7%).
- **GRFIA alto, full set** (479 takes): note F1 75.2% / 75.1% / 75.1%; pitch 90.0% / 89.6% / **90.0%**. Takes where CREPE dropped out near its top limit: 316 → 0.
- **GRFIA tenor, full set**: note F1 66.1% → 65.8% with #69; pitch 87.2% flat.
- Note F1 unchanged on the other sets.
- **Small open item**: Basic Pitch's higher ceiling lets a few stray top-of-range notes through (on very short takes an overtone is tagged `altissimo` and kept), costing 0.27 points of note F1 on tenor and 0.07 on alto. Scorecards with suspected overtones moved are queued on the Mac to decide the default.
- **Reading**: the range rules do no harm on the public sets and #74 removes the pitch-line regression. Their benefit (altissimo above written E7 / D#7) still needs recordings that go that high (E34).

### E37 — 2026-11-04 — Range rules on the Omnibook: a pitch-line regression from the raised ceiling, fixed by PR #74
- **Run**: Omnibook, 45 solos, 07:01 UTC, #57 settings → #69 (range rules, contour redone).
- **Result**: note F1 64.2% → 64.2%, onset F1 85.7% → 85.7% (recall 85.1%), octave errors 1.8% → 1.7%, but **pitch accuracy 74.2% → 72.4%** and chroma 76.1% → 74.1%. New tags: 629 `overtone`, 240 `altissimo`, 48 `below_range`; no notes removed.
- **Where**: three solos carry the whole drop (N3fYc 62.2% → 49.4%, S5VYc 75.0% → 69.8%, 9THwc 77.7% → 72.4% pitch); every other solo moved by 0.2 points or less.
- **Cause**: not the range rules. #69 raised CREPE's alto search ceiling from 1600 Hz to 2000 Hz; on those three solos CREPE put long stretches of real playing at 1966–1998 Hz with confidence 0, so those frames dropped out of the pitch line.
- **Fix**: PR #74 (merged) caps CREPE at 1600 Hz again, the ceiling every earlier scorecard used. That still covers tenor altissimo (written A7 = concert G6, 1568 Hz). Basic Pitch keeps the full range, so alto notes above concert 1600 Hz can still be found as notes, but the pitch line won't follow them. Confirmed in E38: Omnibook pitch back to 74.3%.
- **Reading**: the 629 overtone tags are worth a look before any default moves overtones (the Omnibook stems are band records, where a bass note an octave down can fake a lower fundamental, E34).

### E36 — 2026-11-04 — Onset model re-checked at looser thresholds (not adopted)
- **Question**: was the first onset model (E35) only too strict? Same saved model, no retraining, scored at lower thresholds. Files: `~/saxscribe-runs/exp/2026-11-04-onset-model/rescore.txt` and `rescore.py` on the Mac.
- **Result** (onset F1 / recall):

| Set | Threshold 0.1 | 0.3 | 0.5 | 0.6 | librosa |
| --- | --- | --- | --- | --- | --- |
| URMP | 58.0 / 58.8% | 49.0 / 42.1% | 38.9 / 29.7% | | 65.3 / 81.5% |
| Bach10 | 66.2 / 99.0% | | 77.8 / 95.9% | 80.9 / 94.1% | 68.4 / 99.4% |
| ChoraleBricks | | | 61.4 / 70.9% | | 53.0 / 72.7% |
| GRFIA alto test | | | 75.4 / 86.5% | | 58.5 / 95.0% |
| GRFIA tenor test | | | 73.4 / 85.6% | | 60.9 / 93.3% |

- At 0.5 the model beats librosa by 8–17 points of F1 everywhere except URMP, though its recall is still lower than librosa's on GRFIA.
- **URMP is a blind spot, not a threshold problem**: recall at 0.5 per take is Entertainer 2 82%, Rejouissance 1 64%, Entertainer 1 31%, King 25%, Pirates 14%, Fugue 14%, Surprise 11%, Miserere 3%, Jerusalem 1%, March 0.4%. On the worst takes its output at true onsets (about 0.005) is no higher than in between. These are slow legato pieces with bleed from the other players, which the GRFIA training takes lack.
- Scaling the output over non-silent frames helps a little (best threshold 0.4, URMP F1 38.9 → 45.6, GRFIA unchanged) but the blind takes stay blind.
- **Not adopted**. Next: training data or augmentation with legato playing, reverb, bleed and soft attacks; then threshold 0.4–0.5 with non-silent scaling, and a comparison against Basic Pitch's onsets.

### E35 — 2026-11-04 — First sax-trained onset model (interim, not adopted)
- **Goal**: catch the soft same-pitch repeats that loudness and Basic Pitch's own onsets miss (E29, E31) with an onset model trained on sax. Card: [onset-crnn](../models/onset-crnn.md).
- **Setup**: small CRNN on log-mel input, trained on GRFIA alto and tenor plus Omnibook train tunes (811 takes, 3.27 h, 2 h on the Mac). Scored on held-out URMP, Bach10, ChoraleBricks and GRFIA test tunes with mir_eval onsets at 50 ms; threshold 0.7. Files: `~/saxscribe-runs/exp/2026-11-04-onset-model/` on the Mac.
- **Result** (F1 / precision / recall / same-pitch repeat recall):

| Set | Onset model | librosa onset detector |
| --- | --- | --- |
| URMP | 20.8 / 66.9 / **14.1** / 8.4% | 65.3 / 55.0 / 81.5 / 67.3% |
| Bach10 | 83.1 / 78.3 / 88.8 / 89.2% | 68.4 / 52.3 / 99.4 / 100% |
| ChoraleBricks | 57.9 / 62.4 / 55.4 / 55.7% | 53.0 / 42.6 / 72.7 / 78.0% |
| GRFIA alto test | 76.6 / 74.2 / 79.8 / 86.7% | 58.5 / 42.6 / 95.0 / 97.0% |
| GRFIA tenor test | 72.8 / 70.9 / 75.2 / 80.7% | 60.9 / 46.0 / 93.3 / 92.2% |

- **Reading**: better F1 on four sets, but only through precision; it finds fewer note starts than the plain detector on every set, and on URMP, where the repeats go missing, it finds 14%. The threshold was picked on training data and is too strict. The baseline here is librosa, not Basic Pitch, so these numbers don't yet say whether it would help the pipeline. GRFIA test tunes share the player with training, so they flatter it.
- **Not adopted**. Next: a looser threshold chosen on a validation split, then a comparison against Basic Pitch's onsets on URMP and GRFIA.

### E34 — 2026-11-04 — Range rules per horn: altissimo kept, unplayable notes moved by octaves (PR #69, merged)
- **Problem**: the pitch search stopped below the top of the altissimo range (tenor at 1100 Hz, written D#7; alto at 1600 Hz, written E7), so real altissimo above those was impossible to transcribe. Nothing checked whether a note was playable on the chosen horn.
- **Change** ([ADR-0031](../decisions/0031-range-rules-per-horn.md)): a range table per horn in `saxscribe/horns.py` (soprano, alto, tenor, baritone: lowest key, top keyed note F#6 written, top altissimo A7 written on alto and tenor, F7 on soprano and bari). Rules in `saxscribe/layers/ranges.py`, run in the notes layer and recorded in `take.json`:
  - up to 2 semitones below the low note: kept, tagged `below_range` (a lipped-down low Bb or a flat horn);
  - further below: moved up by octaves, tagged `octave_up`;
  - above the keyed range but within altissimo: kept and never moved for being high, tagged `altissimo`;
  - above the top altissimo note: moved down an octave (or an octave and a fifth if the spectrum shows a 3rd partial), tagged `octave_down`;
  - spectrum shows the partials of a note an octave (or an octave and a fifth) lower: tagged `overtone`, kept as heard unless `--range-rules overtones`;
  - many notes out of range: nothing moved, the log suggests another `--horn`.
  - A moved note keeps the detector's pitch as `detected_pitch`; nothing is deleted; `not_sax` notes are skipped. Notes kept outside the horn's range show in red in the app, also when a take is viewed for another horn.
- **New options**: `--range-rules out|overtones|flag|off` on `transcribe` and `score` (default `out`: only moves notes no sax can play); `score --tag altissimo` scores only GRFIA takes with that technique tag ([protocol](protocol.md#how-to-run)).
- **Scorecard, synthetic only** (provisional): a 72-note phrase (low notes with a weak fundamental, middle notes, altissimo) in the build sandbox, Basic Pitch notes with a pYIN contour (no CREPE there), note F1 without offsets:

| Take | Before (main) | After (#69) | Altissimo notes found |
| --- | --- | --- | --- |
| Alto phrase, Basic Pitch | 92.6% | 100.0% | 15/24 → 24/24 |
| Alto phrase, contour cutter | 83.6% | 91.8% | 18/24 → 24/24 |
| Tenor phrase, Basic Pitch | 89.6% | 100.0% | 12/24 → 24/24 |

  - Low and middle notes unchanged; no false `overtone` tags on clean notes. A tenor phrase run as alto had its two notes heard two octaves up tagged `overtone`.
- **Real check, GRFIA altissimo-tagged takes** (8 per horn, contour redone, 2026-11-04): no change. Alto note F1 71.5% → 71.5% (pitch 86.1% → 86.2%); tenor 47.6% → 47.6% (pitch 82.2% → 82.1%). These takes barely enter altissimo (at most one note above high F# each, highest written A6), which the tool already heard before #69. The raised ceiling only matters above written E7 (alto) or D#7 (tenor), and no public set we have goes that high, so this shows the rules do no harm, not that they help. A real test needs recordings that go that high (Austin parked candidates for later: Lenny Pickett with the SNL band, Foreigner's "Urgent", Jaco Pastorius's "The Chicken").
- **Still to come**: Omnibook and full GRFIA scorecards with the range rules; with the contour redone because the search range changed: GRFIA alto and tenor altissimo takes (`--tag altissimo`), Omnibook, GRFIA tenor. Whether to move suspected overtones by default is open: on a band record, a bass note an octave below the sax could look like a lower fundamental. Other altissimo sources: GoodSounds, SaxTimbre (multiphonics and subtone as overtone traps), Weimar for range statistics.

### E33 — 2026-11-04 — Triplet or plain feel chosen per phrase on fast beats (PR #66, merged)
- **Problem**: after #64 the notation layer still chose triplet or plain feel beat by beat, so fast runs flipped between the two and wrote about 37% more triplets than the Weimar transcribers (1.37×).
- **Change**: a best-path search over the beats of each phrase (an empty beat ends a phrase). Switching between triplet and plain feel costs 0.4 beats, but only on beats shorter than 0.45 s (faster than about 133 BPM), so slow tunes and ballads still switch freely. Each beat's feel is set from its own note starts only ([ADR-0030](../decisions/0030-rhythm-feel-per-phrase.md)).
- **Scorecard**: all 444 Weimar solos, scored on the PR branch at `278e886` against main `fed6f9a`; same tempo groups as E32. Position read:

| Group | Before (main) | After (#66) |
| --- | --- | --- |
| Ballad (10) | 36.2% | 36.2% |
| Slow (60) | 44.0% | 44.0% |
| Medium (85) | 54.4% | 54.6% |
| Up (289) | 74.8% | **77.0%** |
| **All (444)** | 65.9% | **67.4%** |

  - Exact position 61.1% → 61.6%, right beat 92.2% → 92.5%.
  - Triplets 1.37× → 0.76× and sixteenths 0.65× → 0.91× of Weimar's counts: the triplet over-count is gone and slightly reversed.
  - Notes kept 100% (ADR-0016 holds). Note F1, onset and pitch unaffected: notation layer only.
- **Not adopted**: switch costs on every beat (ballads −1.4 to −2.3); costs of 0.6 and 0.6, which raised all to 68.6% but cut triplets to 0.47× (about half of the real triplets lost); 0.4 and 0.6 (slow −0.5). Experiment scripts: `~/saxscribe-runs/exp/2026-11-04-slow-rhythm/phrase_exp*.py` on the Mac.
- **Watch**: triplets now sit below Weimar's count (0.76×). Real triplets written as plain eighths are a readability loss, not a dropped note, but worth checking on Austin's own transcriptions.

### E32 — 2026-11-04 — Sextuplet and 32nd grids for slow and busy beats (PR #64, merged)
- **Problem** (E24, E28): ballads and slow tunes were written in the right place only 17–34% of the time. 85–88% of those misses were written late: with only quarter and triplet grids, a beat holding 6 or 8 notes put two notes on one spot, and pushing each later note into the next slot made whole runs late. The inner notes of busy ballad beats were also being read as swing.
- **Change**: a beat may be written as sextuplet sixteenths (6 per beat) or 32nds (8 per beat), offered only when the beat lasts at least 0.6 s (100 BPM or slower) or holds 5 or more note starts (penalty 0.07). Swing is read only from beats with one or two notes. Two notes on one spot are separated by the beat's own grid step. Sextuplet beats are written as 3:2 triplet sixteenths so MuseScore accepts them ([ADR-0029](../decisions/0029-finer-grids-for-slow-and-busy-beats.md)).
- **Scorecard**: all 444 Weimar solos, scored on the Mac with the PR's notation on main `245952d`. Tempo groups here are the PR's own (slow includes medium slow; up includes medium up; ballads counted on their own), so they differ from E28's five bands. Cells: position read / exact / right beat.

| Group | Before (main) | After (#64) | Position read change |
| --- | --- | --- | --- |
| Ballad (10) | 16.9 / 15.7 / 62.9% | **36.2** / 35.4 / 84.4% | +19.3 |
| Slow (60) | 34.3 / 33.2 / 74.9% | **44.0** / 43.0 / 87.1% | +9.7 |
| Medium (85) | 51.7 / 47.9 / 86.0% | 54.4 / 49.8 / 88.7% | +2.7 |
| Up (289) | 74.1 / 68.7 / 94.1% | 74.8 / 69.1 / 94.6% | +0.7 |
| **All (444)** | 63.1 / 58.7 / 89.3% | **65.9 / 61.1 / 92.2%** | +2.8 |

  - Triplets 1.29× → 1.37×, sixteenths 0.71× → 0.65× of Weimar's counts. Notes kept 100% on every solo (ADR-0016 holds).
  - Note F1, onset and pitch are unaffected: notation layer only.
- **Not adopted** (by position read on all 444): the finer grids on every beat 63.1 (up tempo −3.7); swing fix alone 63.7; no beat-length gate 65.5; no busy-beat gate 64.9; gate at 0.5 s 65.9 and 0.75 s 65.8 (0.6 s kept); higher fine-grid penalties (0.10, 0.13) 64.4. Shifting each solo by a lay-back before quantising (fixed 40 or 80 ms, or estimated per solo): 50.8 / 26.3 / 15–59, up tempo collapses. Files: `~/saxscribe-runs/exp/2026-11-04-slow-rhythm/` on the Mac.
- **Ceiling**: about 37% of ballad notes sit in Weimar divisions of 5, 7 or 9+ per beat (free-time tuplets) that no regular grid can hit, so ballads top out near 65–75% on this measure.
- **Next**: choose the rhythm per phrase rather than per beat.

### E31 — 2026-11-04 — Two more tries at the remaining missed repeats (not adopted)
- **Goal**: win back the onset recall still lost since #52 (E29) without adding wrong notes. Keep rule: note F1 may not drop more than 0.5 points on any set. Files: `~/saxscribe-runs/exp/2026-11-03-recall/` on the Mac.
- **Try 1, a smaller dip or a strong attack, checked against CREPE confidence**: the best rule that passed (dip ≥ 6 dB plus a CREPE confidence dip ≥ 0.2) gave URMP +1.5 points of recall at −0.4 F1, and nothing on Blues for Mary Jane or GRFIA tenor. A strong attack at any pitch gave URMP +2.8 recall but −0.8 F1 (GRFIA alto −1.3), which fails the rule.
- **Try 2, split held notes at Basic Pitch's onset peaks**: −2 to −6 F1 on every set; only 2–13% of the splits were real notes.
- **Finding**: what is still missed is mostly soft same-pitch repeats with less than 4 dB of dip (73 of 107 on URMP). Loudness and Basic Pitch's own onset signal can't separate those from noise. Next route: an onset model trained on sax, possibly on Austin's own recordings.

### E30 — 2026-11-04 — Separator comparison, round 2: clean-ups after Demucs and other separators (PR #61, merged)
- **Question** (Austin, 2026-11-03): is Demucs with two shifts right, or should another tool run after it or instead of it?
- **Sets**: `omnibook-mix` (10 Parker band records) and Blues for Mary Jane (Austin's answer key). Every row on main `c588240` with the #52 note settings, so the baseline differs slightly from E25. Report: `~/saxscribe-runs/exp/2026-11-03-separators2/final_report.txt` on the Mac.

| Separator | Parker: note F1 / onset recall / pitch | Blues for Mary Jane: note F1 / onset recall / pitch |
| --- | --- | --- |
| Demucs `htdemucs_6s` alone (current) | 57.1 / 81.1 / 66.2% | 53.1 / 76.5 / 72.7% |
| **Demucs, two shifts averaged** | **57.9 / 82.1 / 66.6%** | **55.0 / 78.7 / 73.0%** |
| Pitch-guided (harmonic) filter after Demucs, floor 0.1 | 59.2 / 82.2 / 67.3% | 49.8 / 72.8 / 72.6% |
| Pitch-guided filter after Demucs, floor 0 | 58.5 / 80.6 / 67.4% | 50.7 / 72.8 / 72.8% |
| UVR woodwind model instead of Demucs | 59.0 / 77.5 / 68.6% | 55.9 / 72.8 / 69.8% |
| UVR woodwind model after Demucs | 58.3 / 78.0 / 66.7% | 53.8 / 76.5 / 71.6% |
| BS-RoFormer cascade | 57.3 / 80.8 / 66.6% | 53.3 / 76.5 / 73.1% |
| AudioSep ("saxophone") after Demucs | 57.2 / 80.7 / 66.6% | 53.1 / 76.5 / 73.0% |
| Demucs twice | 56.7 / 80.4 / 66.1% | 52.6 / 73.5 / 72.8% |
| AudioSep instead of Demucs | 53.2 / 82.2 / 61.4% | 34.3 / 83.1 / 65.2% |
| Banquet after Demucs | 41.6 / 61.6 / 56.1% (alto query) | 28.6% (tenor query), 1.4% (alto query) |
| Banquet instead of Demucs | 35.5 / 60.6 / 43.1% | 0.0% (tenor query), 5.0% (alto query) |

- **What it shows**: two averaged shifts is the only change that helps on both sets with no loss anywhere (+0.8 / +1.9 note F1, more notes found, at about 50% more separation time). The woodwind model and the pitch-guided filter score higher on one set but find fewer real notes (onset recall down 4–5 points) or get pitches wrong on the other, which breaks the never-drop rule. Running Demucs twice is slightly worse on both sets.
- **Banquet** was included this time (non-commercial licence, fine for personal use; recorded in `SOURCES.md`). It was worst by far. It ran with 50% chunk overlap instead of the published 12×, and lost about 1000 answer-key notes to sax-span cuts, so these numbers understate it, but not by enough to matter.
- **Decision**: keep Demucs alone and make two shifts the default (PR #61, [ADR-0028](../decisions/0028-two-demucs-shifts-by-default.md)).

### E29 — 2026-11-03 — Full scorecards for re-tongued repeats (PR #57, merged)
- **What**: every scorecard set rerun with #57 on main `78063ad`, PDFs off. Notes were redone from the #52 runs (`--redo notes`); outputs are in `~/saxscribe-runs-pr57/` on the Mac. Cards: `~/saxscribe-runs-pr52/<set>/after.json` (#52, commit `c588240`) and `~/saxscribe-runs-pr57/<set>/pr57.json` (#57). Pitch accuracy is identical for #52 and #57 on every set: URMP 94.4%, Bach10 96.9%, ChoraleBricks 98.9%, Parker band records 66.4%, Omnibook 74.2%, GRFIA alto 90.0%, GRFIA tenor 87.2%. Speed is not reported: these runs shared the CPU.

| Set | Note F1: before #52 / #52 / #57 | Onset F1: #52 / #57 | Onset recall: before #52 / #52 / #57 | Notes restored by the dip rule |
| --- | --- | --- | --- | --- |
| urmp | 64.4 / 69.0 / 68.8% | 75.3 / 79.8% | 89.1 / 74.5 / **81.9%** | 143 |
| bach10 | 87.5 / 97.3 / 97.3% | 98.6 / 98.6% | 99.0 / 98.8 / 98.8% | 0 |
| choralebricks | 77.8 / 91.8 / 90.3% | 95.4 / 94.8% | 97.1 / 95.3 / 96.1% | 58 |
| grfia-alto | 66.5 / 75.8 / 75.2% | 83.0 / 82.7% | 88.0 / 85.3 / 86.0% | 169 |
| grfia-tenor | 57.8 / 67.2 / 66.1% | 79.0 / 78.8% | 85.3 / 81.6 / 82.9% | 256 |
| omnibook | 64.2 / 64.2 / 64.2% | 85.7 / 85.7% | 87.0 / 84.8 / 85.1% | 282 |
| omnibook-mix (Parker band records) | 56.4 / 57.8 / 57.6% | 80.9 / 81.0% | 84.1 / 81.5 / 81.8% | 55 |
| bfmj-austin (Blues for Mary Jane, book) | 54.4 / 56.6 / 56.4% | — | 83.1 / 79.4 / 80.1% | 57 |

- **Result**: #57 brings back about half of the notes #52 lost on URMP: onset recall goes from 74.5% to 81.9%, against 89.1% before #52. Note F1 stays within 1.5 points of #52 on every set, so most of the #52 gain is kept. The results match the prototype within about 1 point.
- **Still lost against before #52 (onset recall)**: URMP −7.2 points, Blues for Mary Jane −3.0, GRFIA tenor −2.4, Parker band records −2.3, GRFIA alto −2.0, Omnibook −1.9, ChoraleBricks −1.0. These are real notes not written, so ADR-0026 stays conditional. The build thread is working on them next.

### E27 — 2026-11-03 — Re-tongued repeats restored (PR #57, merged)
- **Finding**: most URMP notes lost under #52 (E26) were re-tongued repeats: the same pitch attacked again after the reed stops, which the tempo-based minimum removed as too short.
- **Change**: a removed short note comes back when the loudness dips by at least 10 dB in the 60 ms before its attack.
- **Result**: URMP onset-recall loss from #52 shrinks from 15 to 8 points; about 80% of the restored notes are real; the gains on other sets mostly hold. Full tables in E29.
- **Still open**: an 8-point onset-recall loss on URMP; the build thread keeps working on it. ADR-0026 stays conditional.

### E26 — 2026-11-03 — Full scorecards for the adaptive shortest note (PR #52, merged)
- **Settings**: default after #52 (shortest note from the take's note spacing, fast-passage safeguard, melodia off), merged main, Mac. Runs labelled "PR #52 Basic Pitch shortest note by note spacing". Note F1 with offsets:

| Set | Before | After |
| --- | --- | --- |
| bach10 | 87.5% | **97.3%** |
| choralebricks | 77.8% | **91.8%** |
| grfia-alto | 66.5% | **75.8%** |
| urmp | 64.4% | 69.0% |
| omnibook-mix (10 Parker band records) | 56.4% | 57.8% |
| omnibook | 64.2% | 64.2% |

- **Fidelity regression**: URMP onset recall fell from 89% to 75%. Real short notes are now missed: the note F1 gain hides notes the tool no longer writes, which breaks the never-drop-notes rule ([ADR-0016](../decisions/0016-notation-never-drops-notes.md), [ADR-0026](../decisions/0026-adaptive-minimum-note-length.md)). The build thread is fixing this next; until then, treat the gains as provisional.
- Full tables (pitch, onset F1, no-offset note F1, tenor) to follow from the build thread.

### E25 — 2026-11-03 — Separator comparison on band records (no code change)
- **Question**: does a newer separator get the sax out of a band better than Demucs `htdemucs_6s`?
- **Sets**: `omnibook-mix` (10 Parker band records) and Blues for Mary Jane (Austin's answer key). Default settings otherwise. Note F1:

| Separator | Parker records (10) | Blues for Mary Jane | Speed |
| --- | --- | --- | --- |
| htdemucs_6s (current) | 56.4% | 51.0% | baseline |
| htdemucs_6s, two shifts averaged | 57.0% | 54.3% | +50% time |
| htdemucs_ft | 52.2% | 32.3% | 3–4× slower |
| BS-RoFormer | 52.7% | 39.8% | 3–4× slower |

- **What it shows**: both alternatives are slower and worse here; they leave piano and guitar in the stem the sax lands in. Averaging two shifts helps a little at 50% more time.
- Banquet was left out of this round for its non-commercial licence; it was added in round 2 (E30) once Austin confirmed the tool is for personal use.
- **Decision**: keep `htdemucs_6s` ([ADR-0027](../decisions/0027-keep-htdemucs-6s.md)); two shifts may become an optional quality setting later (made the default after round 2, E30).

### E24 — 2026-11-03 — Rhythm scorecard on the Weimar Jazz Database: baseline (PR #53, merged)
- **What**: `python -m saxscribe rhythm`, a notation-only scorecard with no audio: the Weimar solos' exact note timings go through Layer 4, and the written rhythm is compared with the Weimar transcription. Measures: exact position, right slot, right beat, triplet / sixteenth / busy ratios, notes kept. Split by performer; 12 Parker solos that are also in the Omnibook are left out ([protocol](protocol.md#rhythm-scorecard-weimar-no-audio)).
- **Baseline** (2026-11-03, main `c588240`, Mac; cards in `~/saxscribe-runs/rhythm/`):

| Group | Solos | Exact position | Right slot | Right beat | Triplets × | Sixteenths × | Busy × | Notes kept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All | 444 | 58.7% | 58.9% | 89.3% | 1.29 | 0.71 | 0.94 | 100% |
| Saxes | 259 | 53.6% | 53.9% | 87.0% | 1.24 | 0.77 | 0.96 | 100% |
| Train | 392 | 58.5% | | | | | | |
| Test | 52 | 60.3% | | | | | | |

  - By feel (exact): two-beat 74.4%, Latin 59.4%, swing 58.7%, funk 55.5%, **ballad 15.7%**.
  - By tempo (exact): up 73.3%, medium up 58.7%, medium 47.9%, medium slow 46.1%, **slow 18.5%**.
  - 12 Parker solos excluded as Omnibook overlap; no solo failed; every note written (ADR-0016 holds).
- **Finding 1, the measure undercounts swing** (fixed in the scorecard by PR #55, merged; new baseline in E28): Weimar writes swung off-beats where they fell (2/3 or 3/4 of the beat); we write them as swung eighths (1/2, by design, [ADR-0018](../decisions/0018-swing-aware-notation.md)). "Exact position" counts correct swing notation as wrong. PR #55 (merged) adds `position_read`, which accepts that case in swung solos, as the headline measure.
- **Finding 2, ballads and slow tunes are a real gap** (15–19%): Weimar uses 6- and 8-way beat divisions; we round those and often push the last note of a run onto the next beat.
- Not a model change: it measures the current notation layer.

### E23 — 2026-11-03 — Basic Pitch shortest note set from the take's tempo, with a fast-passage safeguard (PR #52)
- **Change**: the shortest note Basic Pitch keeps is 0.4 × the take's median gap between note starts, clamped to 50–128 ms (was a fixed 50 ms), with the melodia trick off. **Safeguard**: a short note the stricter minimum would remove comes back on fast passages (onsets under 200 ms apart) when it has its own attack and a pitch different from both neighbours. The old behaviour stays as `--notes-tool basic_pitch_fixed` ([ADR-0026](../decisions/0026-adaptive-minimum-note-length.md)).
- **Results** (Mac; versions in `~/saxscribe-runs/exp/2026-11-03-settings/pip-freeze.txt`), note F1 with offsets:

| Set | Before | After |
| --- | --- | --- |
| GRFIA alto | 67.4% | **76.3%** |
| GRFIA tenor | 56.8% | **67.4%** |
| Blues for Mary Jane (Austin's key) | 53.6% | 56.2% |
| Omnibook | 64.2% | 64.2% |

- **Fidelity check**: without the safeguard the Omnibook lost 490 notes that matched the answer key. The safeguard brings back 134; about 350 real notes are still missed, offset by about 350 ghost notes removed, so Omnibook note F1 is unchanged. Those ~350 are the cost of the change and are recorded here so they aren't forgotten.
- GRFIA "before" differs slightly from E22 (66.5 / 57.8) because this sweep ran on the current code; same answer keys.

### E22 — 2026-11-03 — GRFIA-RealSax rescored with the final answer keys (after PR #47): current numbers
- **Set**: `grfia-alto`, `grfia-tenor`, same takes and default settings as E20; only the answer keys changed (PR #46 beat alignment, PR #47 per-take choice by pitch agreement). Not a model change.

| Measure | Alto | Tenor |
| --- | --- | --- |
| Note F1 (with offsets) | **66.5%** (E20: 58.1%) | **57.8%** (E20: 53.8%) |
| Note F1 without offsets | 78.5% (E20: 70.6%) | 73.8% (E20: 66.7%) |
| Onset F1 | 79.1% (E20: 71.1%) | 75.1% (E20: 67.5%) |
| Pitch accuracy | 90.0% (E20: 84.3%) | 87.2% (E20: 85.3%) |
| Trill takes, note F1 | ~27% | ~27% |

- **Alignment**: 27 of the 28 scale takes that slid after #46 are fixed. One tenor exercise appears to be paired with the wrong score (a dataset issue, *to check*).
- **What it shows**: with sound answer keys, real solo sax scores 66.5% (alto) and 57.8% (tenor) note F1, against the 80% solo target. The gap to alto on tenor is now 8 points, so tenor needs its own look. Trills stay low by labelling convention (E20).
- These are the current GRFIA numbers; E20 and E21 are kept as history.

### E21 — 2026-11-03 — GRFIA-RealSax answer keys re-aligned (PRs #46 and #47 merged): an answer-key change, not a model change
- **Why it is separate**: these PRs change how the GRFIA scores are lined up with the takes, which changes the answer keys. The transcription is unchanged. They are grading fixes like PR #16, so they are not drawn as model-change markers on the Results page and are not in `changes.json`.
- **PR #46**: metronome takes are aligned on the beat instead of by chroma DTW.

| Note F1 (with offsets) | Before #46 (E20) | After #46 |
| --- | --- | --- |
| Alto, all takes | 58% | 65% |
| Tenor, all takes | 54% | 53% |
| Alto, one-pitch drills | 25% | 79% |
| Tenor, one-pitch drills | 35% | 79% |

- **New slip**: 14 alto and 14 tenor scale takes now slide by one step, which is why tenor dips.
- **PR #47 (merged)**: per take, picks the alignment whose pitches match the audio and keeps the older key where it scores better. Result in E22: alto 66.5%, tenor 58%.
- **Reading the numbers**: compare GRFIA figures only within the same answer-key version; E22 is the current one.

### E20 — 2026-11-03 — GRFIA-RealSax full scorecards, alto and tenor (provisional)
- **Set**: `grfia-alto`, `grfia-tenor`, about 950 real takes, scores aligned to the audio by the etude aligner (tier B). Default settings, on the Mac. Supersedes the 10-take preliminary (E17).
- **Correction (2026-11-03 06:36)**: the 71% / 67% first logged as note F1 ignored note offsets. With offsets, as everywhere else in this log, note F1 is 58% alto and 54% tenor. Answer keys were then improved (E21).

| Measure | Alto | Tenor |
| --- | --- | --- |
| Pitch accuracy | 84% | 85% |
| Octave errors | 0.1% | 0.1% |
| Onset F1 | 71.1% | 67.5% |
| Note F1 (with offsets) | 58% | 54% |
| Note F1 without offsets | 71% | 67% |

- **By technique tag**:
  - **Trills**: note F1 (without offsets) 24% against about 57% elsewhere. The score writes one trilled note; we write every alternation. That is a labelling convention, not a detection miss: by the fidelity rule we keep the notes, and a "trill" articulation tag (F3a) would let notation show them as one written trill.
  - **Bends and falls** cost alto pitch accuracy: 71–78% against 85%. The pitch line follows the bend, the score holds one pitch.
  - **Vibrato**: no measurable effect (tagged in two-thirds of takes).
- **Provisional**: the worst takes are answer-key alignment slips on short repetitive exercises (scales and patterns repeat, so the alignment can lock one repeat off). Being fixed in the build thread; re-run before these numbers are compared with other sets.
- **What it shows**: first large real-sax test with both horns. Tenor scores close to alto, which is the first evidence that the default pipeline carries over to tenor. Octave errors are essentially gone on clean takes.
- `results.jsonl` lines: *to copy* from the Mac.

### E19 — 2026-11-03 — First personal answer key: Blues for Mary Jane, intro and choruses 1–2
- **Set**: Austin's own printed transcription of Stan Getz, "Blues for Mary Jane" (full quartet record), hand-entered for the intro and choruses 1–2: 136 notes, first 35 s, aligned to the recording. **The first personal answer key** ([ADR-0014](../decisions/0014-personal-answer-keys-from-paper.md), [datasheet](../data/datasheets/austin-recordings.md)). Tier B: aligned and hand-entered, not yet spot-checked note by note. Settings: default, app run, 2026-11-03.

| Measure | Result |
| --- | --- |
| Note F1 (onset ±50 ms, pitch ±50 cents, no offsets) | 70% |
| Note F1 with offsets | 54% |
| Onset recall | 83% |
| Octave errors | 0 |
| Notes: ours vs the book | 158 vs 136 |
| Extra notes (short ghost or split notes) | 55 |
| Book notes missed | 33, of which 11 had a note at the right time 1–2 semitones off (some may be reading errors from the photo of the page) |

- **What it shows**: on a full quartet record the sax line scores about as well as the clean Parker stems (Omnibook note F1 64%). The main loss is extra short notes, not missed ones. The missed notes are detection misses (see E18), not notation losses.
- **Next**: remove ghost notes, checked so that no real note is lost (fidelity rule); check the 11 near-misses against the page.

### E18 — 2026-11-03 — Blues for Mary Jane PDF against Austin's transcription, first two choruses (qualitative)
- **What**: bar-by-bar reading of the app's tenor PDF against Austin's printed transcription (Stan Getz), first two choruses. A hand check, not a scorecard; numeric scoring waits on the OMR tool install (Austin to approve) so the transcription can become a personal answer key.
- **Lines up**: bar count and bar lines, key (D on the tenor part, concert C).
- **Pitch**: mostly right. Some enharmonic spellings differ from the copy (Ab written where the copy has G#, and the like).
- **Rhythm, the weak spot**: extra triplets, sixteenths and ties where the copy has plain eighths and quarters; some pickups placed early or late.
- **Missing notes**: a few notes in the copy are absent from the PDF. They are **Basic Pitch detection misses (Layer 3)**, not notation losses: the notation layer wrote every sax note (1385 of 1385 in the runs log, 1310 of 1310 in the app run), and the first sax-span cut starts at 195 s, after the compared choruses (0–40 s). [ADR-0016](../decisions/0016-notation-never-drops-notes.md) holds. Note-by-note confirmation follows once the hand-entered answer key (intro and choruses 1–2) is aligned.
- **Next**: rhythm quantisation (build thread); spelling from the chord or melodic direction (roadmap: chord-aware spelling).

### E17 — 2026-11-03 — GRFIA-RealSax, first 10 alto takes (preliminary, superseded by E20)
- **Set**: GRFIA audio-to-score ("GRFIA-RealSax"), first 10 alto takes, default settings, on the Mac.
- **Result**: pitch 80% correct, **no octave errors**. Exact measure (frame pitch accuracy or matched-note pitch) *to verify* with the build thread's scorecard.
- **Status**: superseded by E20 (full run, about 950 takes).

### E16 — 2026-11-03 — Write only where the sax plays (PR #35, merged)
- **Finding**: on band records the score covered the whole track. Blues for Mary Jane came to about 419 bars against about 148 for Getz's solo: the piano solo bleeds into the sax stem and the bass solo adds junk. On Parker's 7XTyc, Basic Pitch wrote 8 to 17 notes per 4 s through a drum break.
- **Change**: `isolate.sax_spans` marks where the horn plays. Each 2 s window is checked for the stem's share of the mix (sax 0 to 3 dB below the mix; piano solo 10 to 50 dB down) and for how clearly it holds one pitch (drum break near 0), judged against the take's own sax windows. Only stretches of 8 s or more are cut, with 2 s given back at each end. Notes in a cut stay in `notes.json` tagged `not_sax` and leave the score, the MIDI and the scorecard. Solo takes are never cut ([ADR-0023](../decisions/0023-write-only-where-the-sax-plays.md)).
- **Probe on the Mac** (4 s windows): Blues for Mary Jane, Getz 0–192 s (intro plus 12 choruses, matching Austin's published transcription), piano solo 196–320 s, bass solo 324–364 s, Getz again 368–464 s. 7XTyc: clarity 0.31–0.46 while Parker plays, 0.00–0.16 in the 32–60 s drum break.
- **Guard**: cut stretches are saved in `take.json` (`sax_cuts`); the scorecard reports answer-key notes inside them per take and in a "Sax-span check" total. Any non-zero count is a cut that hid real sax.
- **Results on the Mac** (2026-11-03, after Austin merged through #40; 111 tests pass):
  - **Parker band records** (`omnibook-mix`): 0 answer-key notes inside cut stretches (sax-span check). On 7XTyc the 32–60 s drum break is removed and note F1 rises from 56% to 62%. Mean over the 10 records: *to fill in* from the scorecard.
  - **Blues for Mary Jane** (app upload): the piano solo (195–294 s) and the bass solo (305–368 s) are cut, about 500 notes that were not Getz. Key C concert (D on the tenor part), which matches Austin's transcription; PDF header correct.
  - **Known wrong cut**: one 8 s stretch on an older take, where separation had moved the sax into the guitar stem. Fixed in PR #43: no cut where the horn has moved into another melodic stem.
- **Other gaps seen in the same check** (not this PR): the Desktop copy of outputs (done in PR #42, `~/Desktop/Saxscribe` with title and artist) and the MusicXML title reading "Transcription" (fix *to confirm*).
- `results.jsonl` line: *to copy* from the Mac's `~/saxscribe-runs/results.jsonl`.

### E15 — 2026-11-03 — Key finder that hears the blues (PR #34, merged)
- **Finding**: Blues for Mary Jane (concert C) was written in F major. The blues flat third and flat seventh, plus the IV chord, pull music21's key finder to the subdominant.
- **Change**: weight notes by length, and also match against a blues profile (Krumhansl's major profile with flat 3 and flat 7 raised, major 7 lowered). When the blues profile fits better, its home note wins and the key is written as major ([ADR-0022](../decisions/0022-blues-aware-key-finding.md)).
- **Set**: Weimar Jazz Database, 429 solos with annotated keys, plus Blues for Mary Jane (home note right):

| Rule | All 430 | Major 342 | Minor 74 | 12-bar blues 92 |
| --- | --- | --- | --- | --- |
| music21 alone (before) | 49.3% | 49% | 58% | 46.7% |
| music21, notes weighted by length | 50.2% | 51% | 55% | 45.7% |
| Blues profile when it fits better (PR #34) | **60.0%** | **62%** | 54% | **69.6%** |
| Same, keeping music21's minor keys | 57.9% | 60% | 55% | 68.5% |

- Blues for Mary Jane: F before, C after. Minor tunes lose about 4 points; a minor guard was tried and left out (it cost more on major tunes).
- **Ceiling**: Weimar labels give the tune's key; a solo often sits on IV or V, so 100% is not reachable on this measure. Note, onset and pitch scores unchanged.

### E14 — 2026-11-03 — Syncopations as one note instead of tied eighths (PR #32, merged)
- **Change**: an off-beat eighth tied into the next beat is written as a syncopated quarter (or dotted quarter when it runs to the next "and"); a quarter tied to an on-beat eighth becomes a dotted quarter. Only within one half of the bar, so beat 3 stays visible. Triplets unchanged.
- **Result** on 7XTyc's real timings: ties 46 → 41, 407 notes, no MuseScore problems. Note, onset and pitch scores unchanged.
- **Remaining ties** are mostly notes running into a beat on a different grid (an "and" held into a triplet beat). Judging those needs a rhythm answer key (GRFIA audio-to-score).

### E13 — 2026-11-03 — Beat taken from the notes on lone sax (PR #29, merged)
- **Finding**: on the Parker test solo (Omnibook 7XTyc, sax stem alone) Beat This! found only 13 beats in 90 s. Filling the gaps gave a beat every 0.370 s (162 BPM); Parker's swung eighth pairs repeat every 0.23 s (about 261 BPM). On a grid 1.6× too slow, eighths come out as triplets and 32nds. This is the main cause of the busy notation in E12.
- **Change**: when the tracker finds too few beats (and there are at least 16 notes), take the beat from the note onsets: autocorrelation over 80–300 BPM, then step beat by beat, leaning toward nearby notes and moving the grid onto the beat if it sits on the off-beats. Band recordings with a dense tracked grid keep the tracker's beats. notation.json records where the grid came from ([ADR-0021](../decisions/0021-beat-from-notes-when-tracker-sparse.md)).
- **Scorecard**: notes, onset and pitch unchanged (notation only). Readability on 7XTyc, every note kept, MuseScore problems 0 both times:

| Measure | main | PR #29 |
| --- | --- | --- |
| Tempo | 162 BPM (wrong) | 264 BPM |
| Plain eighths | 88 | 231 |
| Triplet eighths | 162 | 146 (mostly full groups Parker plays) |
| 32nd notes | 80 | 1 |
| Dotted sixteenths | 20 | 1 |
| Notes squeezed off a shared spot | 85 | 1 |

- **Next**: score rhythm against the Omnibook's printed rhythm to see how many of the remaining triplets are right.

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
