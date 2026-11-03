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
| 2026-11-03 | #52 (open) | Shortest note follows the take's tempo, fast-passage safeguard | notes | grfia-alto / grfia-tenor / omnibook | Note F1 | 67.4 / 56.8 / 64.2% | 76.3 / 67.4 / 64.2% | yes | [E23](#e23--2026-11-03--basic-pitch-shortest-note-set-from-the-takes-tempo-with-a-fast-passage-safeguard-pr-52) |
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
| bach10 | 96.9% | **92.2%** ✓ | **87.5%** ✓ | 92.2% | 21 | solo | E4 |
| choralebricks | **98.9%** ✓ | 86.7% | 77.8% | 86.5% | 22 | solo | E4 |
| urmp | 94.4% | 81.6% | 64.4% | 80.8% | 24 | solo | E3 |
| omnibook | 74%† | **86%** ✓ | **64.2%** ✓ | — | — | mix | E6, E9 |
| urmp-mix | 41.6% | 48.9% | 17.1% | 35.4% | 27 | mix | E3 |
| omnibook-mix (10) | — | — | 56.4% | — | 64 | mix | E11 |
| grfia-alto (~950 takes with tenor) | 90.0% | 79.1% | 66.5%‡ | 78.5% | — | solo | E22 |
| grfia-tenor | 87.2% | 75.1% | 57.8%‡ | 73.8% | — | solo | E22 |
| bfmj-austin (Getz, 35 s, 136 notes) | — | 83% recall | 54% | 70% | — | mix | E19 |
| bach10-mix | 21.4% | 39.5% | 3.9% | 29.2% | 31 | mix | E4 |

† Understated by octave errors in some Omnibook answer keys (E10); about 87% on solos with sound keys.

‡ GRFIA with the final answer keys (PRs #46 and #47, E22).

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
- **Decision**: keep `htdemucs_6s` ([ADR-0027](../decisions/0027-keep-htdemucs-6s.md)); two shifts may become an optional quality setting later.

### E24 — 2026-11-03 — Rhythm scorecard on the Weimar Jazz Database (PR #53, open)
- **What**: `python -m saxscribe rhythm`, a notation-only scorecard with no audio: the Weimar solos' exact note timings go through Layer 4, and the written rhythm is compared with the Weimar transcription. Measures: exact position, right slot, right beat, triplet / sixteenth / busy ratios, notes kept. Split by performer; 12 Parker solos that are also in the Omnibook are left out ([protocol](protocol.md#rhythm-scorecard-weimar-no-audio)).
- **Baseline**: pending, after merge.

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
