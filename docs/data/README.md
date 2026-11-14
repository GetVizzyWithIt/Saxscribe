# Data

Every dataset Saxscribe uses or plans to use, what its labels are worth, and
the rules for using it. Detail per dataset is in [datasheets/](datasheets/).
Last updated 2026-11-14.

## Where data lives

- Nothing in the repo: no audio, no datasets ([CLAUDE.md](../../CLAUDE.md)).
- On Austin's Mac in `~/mir_datasets/<Folder>/` (about 125 GB), downloaded
  archives in `<Folder>/_zips/`, unpacked beside them.
- `datasets/manifest.json` (in the repo) lists every source, licence, access
  type and md5. `python -m saxscribe fetch` rebuilds the folder on any machine
  ([ADR-0011](../decisions/0011-dataset-manifest-and-fetch.md)).
- Other paths go in `config.local.toml` (ignored by git).
- When a GPU is needed: a slim private sax pack on private Hugging Face or
  Google Drive, never public.

## Label quality tiers

| Tier | Meaning | May be used for |
| --- | --- | --- |
| **A. Human-checked notes** | Note onsets, offsets and pitches checked by people, aligned to this audio | Scoring and training |
| **B. Aligned but machine-assisted** | Score or MIDI aligned to the audio by an algorithm, spot-checked | Scoring with care; training |
| **C. Single-note or technique labels** | One pitch or technique per file | Pitch range checks, articulation classifiers, augmentation |
| **D. Machine-made notes** | Another model's transcription | Drafts to correct, separation tests. **Never graded against** ([ADR-0008](../decisions/0008-grade-only-against-human-checked-notes.md)) |
| **E. Labels without audio** | Transcriptions of records we must source ourselves | Answer keys once paired with Austin's own copies |

## Inventory

| Dataset | Sax content | Tier | Scorecard set | Role | Licence | Datasheet |
| --- | --- | --- | --- | --- | --- | --- |
| Charlie Parker Aligned Omnibook | 46 alto solos with aligned MIDI (of 50) | B | `omnibook`, `omnibook-mix` | Main jazz test set; notation check; alto training | CC BY 4.0 | [omnibook](datasheets/omnibook.md) |
| URMP | 11 sax parts, classical ensembles | A | `urmp`, `urmp-mix` | Solo test; mix stress test | CC0 | [urmp](datasheets/urmp.md) |
| Bach10 | Tenor-voice sax in 10 chorales | A | `bach10`, `bach10-mix` | Solo test; mix stress test | Research use, *to verify* | [bach10](datasheets/bach10.md) |
| ChoraleBricks | 20 alto + 18 baritone parts | A | `choralebricks` | Solo test | CC BY 4.0 | [choralebricks](datasheets/choralebricks.md) |
| JazzSAMBA | 50 alto + 25 tenor songs, stems and mixes | D (sax notes) | none | Separation training/tests; tenor; drafts | MIT-style | [jazzsamba](datasheets/jazzsamba.md) |
| Weimar Jazz Database | 456 solos (80 alto, 157 tenor), no audio | E | none yet | Full-mix answer keys with Austin's records; chords for spelling | *to verify* (ODbL noted) | [weimar](datasheets/weimar.md) |
| Filosax | ~48 h jazz sax, 5 players, note annotations | A | `filosax` (loader ready) | Primary solo train/test; v1 gate | On request; pending | [filosax](datasheets/filosax.md) |
| MedleyDB-Pitch | Stems incl. sax with checked f0 | A (pitch) | none | Pitch check; separation | On request; pending | [medleydb-pitch](datasheets/medleydb-pitch.md) |
| TinySOL, Iowa MIS, Philharmonia, OrchideaSOL, GoodSounds | Single alto/tenor/soprano/bari notes, techniques | C | none | Range and technique checks, augmentation | various | [single-note-sets](datasheets/single-note-sets.md) |
| SaxTimbre, Vibrato Dataset, Register Control, Medley-solos-DB | Technique and register clips | C | none | Articulation/technique classifiers | various | [technique-sets](datasheets/technique-sets.md) |
| GRFIA audio-to-score | 1,026 short alto and tenor takes (~3 h), written score per take, technique tags | B (machine-aligned, not spot-checked); C (techniques) | `grfia-alto`, `grfia-tenor` | Notation and rhythm answer key; technique tags; tenor | Non-commercial | [grfia-audio-to-score](datasheets/grfia-audio-to-score.md) |
| Alto etude keys (Ferling Op. 31, Luft Op. 1 No. 2) | 52 alto takes of written studies, keys read from public-domain scores | B (score-reader keys, machine-aligned; 92% agree with heard pitch) | `etudes-alto` | Written-music test on real alto; held-note and vibrato checks | Scores public domain; recordings *to verify* | [etude-keys](datasheets/etude-keys.md) |
| Austin's recordings and answer keys | Etude takes; records paired with his paper transcriptions | A (once aligned and checked) | `pairs` | Frozen 20-take test set; fine-tuning; personal answer keys | Private | [austin-recordings](datasheets/austin-recordings.md) |
| Freesound sax instrument samples | 495 single-note and phrase clips by sax type (originals, all downloaded 2026-11-09) | C | none | Range and technique checks, not-sax negatives later | CC0 and CC-BY (9 CC-BY-NC alto-with-band clips kept apart) | Mac `~/saxscribe-runs/sample-clips/`; manifest and credits in the project files (`datasets/freesound/`) |
| FiloBass | Jazz bass, no sax | — | none | Future bass instrument | CC BY 4.0 | listed in manifest only |

## Chart sources for answer keys

Printed or engraved transcriptions are tier E (labels without audio) until a
recording passes the line-up check (`keys/match_report.jsonl`,
`usable=true`). After that they are tier B, because they are read by a
score reader and aligned by machine. Nothing is filed under `keys/` without a
passing line-up. Paths are on Austin's Mac.

| Source (added) | What | Horn | Where | Status |
| --- | --- | --- | --- | --- |
| *25 Great Sax Solos* (Hal Leonard), Dexter Gordon, Coltrane and Phil Woods books, Sax Teacher UK, 7 more charts (earlier, log P8) | Split into one PDF per solo | alto, tenor | `keys/transcribed/`, `links.csv` | 8 of the 25 pop solos match so far (4 pass, 4 usable with a check); the rest wait on the 0% line-up check below |
| Academia.edu (2026-11-13) | 9 theses and papers with transcriptions: the Warne Marsh Copenhagen 1975 thesis (Petrucelli; 8 full solos plus All the Things You Are), the Joe Henderson thesis (Lopes; about 4 new solos), Dexter Gordon Lady Bird 1964 (all 9 choruses), Getz It Might As Well Be Spring, 5 Lee Konitz solos, Zé Bodega Catita, Paulo Moura Bicho Papão, and two excerpt-only papers (Coltrane One Down, One Up; Linda Érika) | tenor, alto | `sheet-music/academia/` | Downloaded; the excerpt-only ones can't be keys |
| Hal Leonard *John Coltrane Solos* (Artist Transcriptions) (2026-11-13) | 27 solos, split one per file | tenor | `sheet-music/` (catalog thread) | Split; not lined up yet |
| Michael Brecker book (2026-11-13) | 12 solos, split one per file | tenor | `sheet-music/` (catalog thread) | Split; not lined up yet |
| Free transcription sites (2026-11-13) | 109 PDFs: Andrew Frankhouse (70, including Coltrane Prestige, Rollins, and 9 Warne Marsh solos), Dave Doescher (14), Brandon Moore (17), jazzsaxophonelessons (4) | alto, tenor | `sheet-music/sites/<site>/` | Download script written (`catalog/_tools/download_site_pdfs.py`), Austin runs it; checked and catalogued after |
| jazzbarisax.com (2026-11-13) | About 105 baritone solos (Pepper Adams, Ronnie Cuber, Gerry Mulligan) | **baritone (new horn)** | to come, as a bari group per the naming standard | Listed, not downloaded |
| Falkowski excerpts (2026-11-13) | 88 one-page solo excerpts with the solo's start time printed | various | Mac, clip script written | Start times make the line-up easier; Austin runs the clip script |
| MuseScore, free (2026-11-13) | 5 MusicXML files: Getz Desafinado, Kamuf Alone Together, Coltrane Mr. P.C. (part 4), The Chicken, Bartley After You've Gone | tenor, alto | project files `datasets/musescore/` | Downloaded; MusicXML needs no score reader |
| MuseScore, paid (2026-11-13) | 23 community scores at $2.99 each (Pro includes them) | various | list in `datasets/musescore/musescore_status.md` | Back burner |

Wesley Chin's free store items (29) need a checkout with an email, so they are
skipped unless Austin gets them by hand. Saxopedia and the "best sax website"
guide are link directories that need their own pass. The 9 research papers
found on Academia (Abeßer, Frieler and others on score-informed analysis,
melody-extraction evaluation, jazz bass transcription, swing and expressive
sax) went to the reading list (`research/reading-list/jazz-transcription-academia.md`
in the project files), not here.

**Known issue (cause found):** many charts scored exactly 0% on the line-up check
(8 of the 11 rejected pop solos, and most of the Anderson charts). The 0% is a
display artifact (every section under the agreement bar; real agreement 19 to
51%). The cause was the pitch line being read from the full mix, so the
line-up landed in the wrong place. The key tools now also read the Filosax sax
stem and search near the book's printed start time; the 11 songs are being
re-checked. See P11 in the [evaluation log](../evaluation/log.md).

## Splits and leakage

- **By tune and by player, never by take.** `score/refs.py: split_of` hashes
  the tune name and puts about one tune in five in `test`. The same tune never
  appears on both sides.
- **20 of Austin's takes are frozen as a test set** and never train anything.
- **Same notes, different files**: OrchideaSOL's "ordinario" notes are the same
  99 performances as TinySOL, processed differently. Never put one in train
  and the other in test.
- **Same solo, two datasets**: 12 Weimar Parker solos (melids 52, 53, 55, 58–61, 63, 64, 66–68) are also Omnibook solos; the rhythm scorecard leaves them out.
- **Same solo, two versions**: `omnibook` and `omnibook-mix` are the same
  performances; both go on the same side of any split.
- **Thresholds are tuned on train splits only.**
- **Answer keys can be wrong too.** Some Omnibook keys are an octave off in long passages; the scorecard flags octave disagreements (PR #23) so they aren't counted as model errors without a check.
- **Pretrained models have seen some of our test sets.** CREPE trained on Bach10 and MedleyDB; Basic Pitch on MedleyDB-Pitch; Beat This! `final0` on Filosax and JAAH ([upstream review](../models/upstream-review.md)). Scores on those sets flatter the model; say so when reporting them, and use a held-out checkpoint where one exists.
- **Machine-made labels are never answer keys** (JazzSAMBA sax MIDI,
  MedleyDB-Pitch pYIN notes).

## Augmentation policy (from the requirements)

Pitch-shift and time-stretch within a semitone and 10%; add room reverb and
mix noise. Rendering MIDI through a sax soundfont only as a last resort:
synthetic sax trains models that fail on real tone.

## Pending (needs Austin)

- Filosax and MedleyDB-Pitch access (requested).
- Alto etude takes (first entries of the frozen test set).
- Scans of his paper transcriptions, one PDF per tune, noting which recording and which horn.
- Trash three duplicate dataset copies already verified as duplicates.
