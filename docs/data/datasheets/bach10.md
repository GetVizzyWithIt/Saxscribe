# Datasheet: Bach10

## Motivation
Made by Duan and Pardo (Northwestern / Rochester, 2010–2011) for
multi-pitch estimation and score following.

## Composition
- 10 four-part Bach chorales played by violin, clarinet, tenor saxophone and bassoon.
- The sax plays the tenor voice, Eb3 to Ab4 concert.
- Per chorale: each part's audio, the mix, ground-truth pitch (`GTF0s.mat`) and
  notes (`GTNotes.mat`) for all four parts, MIDI, score alignment.
- Tier A. Note frames are 10 ms apart, the first centred at 23 ms.

## Collection process
Parts recorded separately, then mixed.

## Preprocessing and labelling
Loader (`load_bach10`, PR #9) reads the sax part from `GTNotes.mat`; a note's
pitch is its median. Checked: onsets land within 15 ms of the dataset's own
alignment file.

## Uses
- **Role**: `bach10` = solo test (tenor range); `bach10-mix` = separation stress test.
- **Do not use for**: redistribution until the licence is confirmed.

## Distribution
https://labsites.rochester.edu/air/resource.html, behind a form (manual
access), 0.13 GB. Licence: see `Dataset_v1.0.pdf` inside the download, *not
yet checked*. Folder `Bach10/Bach10_v1.1`.

## Maintenance
Checksums in the manifest.

## Saxscribe results
2026-11-02: solo pitch 96.9%, onset F1 92.2%, note F1 87.5% (first set past the
onset and note targets); mix note F1 3.9%. See the [log](../../evaluation/log.md).
