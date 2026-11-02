# Datasheet: JazzSAMBA

## Motivation
A jazz multitrack dataset with isolated stems and mixes, released on Zenodo
(record 22943963) for separation and transcription research.

## Composition
- **async**: 25 alto + 25 tenor songs (2 takes each) plus 50 extra alto takes; stems recorded separately.
- **sync**: 16 alto songs played live as a band, with debleeded stems.
- Mixes for every song.
- Sax notes: **machine transcription only** (`*.transcribed.derived.mid`). Ground-truth MIDI only for piano and drums.
- Tier D for sax notes.

## Collection process
See the dataset's own documentation.

## Preprocessing and labelling
No Saxscribe loader yet.

## Uses
- **Role**: separation training and testing (stem vs. mix pairs, alto and tenor); tenor transfer checks; drafts to hand-correct into answer keys.
- **Do not use for**: grading notes. Its sax MIDI is another model's output ([ADR-0008](../../decisions/0008-grade-only-against-human-checked-notes.md)).

## Distribution
Zenodo 22943963, open, MIT-style licence in the dataset's LICENSE file (keep
the copyright notice; derived files are estimates), 21.8 GB. Folder `JazzSAMBA/`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
None yet.
