# Data

Every dataset Saxscribe uses or plans to use, what its labels are worth, and
the rules for using it. Detail per dataset is in [datasheets/](datasheets/).
Last updated 2026-11-03.

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
| GRFIA audio-to-score | 1,026 short alto and tenor takes (~3 h), written score per take, technique tags | B once aligned; C (techniques) | none yet | Notation and rhythm answer key; technique tags; tenor | Non-commercial | [grfia-audio-to-score](datasheets/grfia-audio-to-score.md) |
| Austin's recordings and answer keys | Etude takes; records paired with his paper transcriptions | A (once aligned and checked) | `pairs` | Frozen 20-take test set; fine-tuning; personal answer keys | Private | [austin-recordings](datasheets/austin-recordings.md) |
| FiloBass | Jazz bass, no sax | — | none | Future bass instrument | CC BY 4.0 | listed in manifest only |

## Splits and leakage

- **By tune and by player, never by take.** `score/refs.py: split_of` hashes
  the tune name and puts about one tune in five in `test`. The same tune never
  appears on both sides.
- **20 of Austin's takes are frozen as a test set** and never train anything.
- **Same notes, different files**: OrchideaSOL's "ordinario" notes are the same
  99 performances as TinySOL, processed differently. Never put one in train
  and the other in test.
- **Same solo, two versions**: `omnibook` and `omnibook-mix` are the same
  performances; both go on the same side of any split.
- **Thresholds are tuned on train splits only.**
- **Answer keys can be wrong too.** Some Omnibook keys are an octave off in long passages; the scorecard flags octave disagreements (PR #23) so they aren't counted as model errors without a check.
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
