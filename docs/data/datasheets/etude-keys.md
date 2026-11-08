# Datasheet: alto etude answer keys (Ferling Op. 31, Luft Op. 1 No. 2)

Format: Gebru et al., "Datasheets for Datasets" (CACM 2021), trimmed. Written
2026-11-08 from the build note and the set's README. First scores: log E75.

## Motivation
Austin asked for alto etude answer keys (2026-11-08). They test the tool on
written classical studies played on real alto, where the score is the answer.

## Composition
- **Scores**: Ferling, 48 Studies Op. 31 (IMSLP #16933, Spehr 1837) and Luft,
  Op. 1 No. 2 (IMSLP #94059, Bleuzet 1926). Both are public domain.
- **Takes**: 52 alto recordings, mostly Wonki Lee, plus Voxman, Nabb and UT
  studio takes. 31 fast studies and 21 slow ones; 14,443 key notes.
- **Labels**: written pitch and rhythm per bar (`keys/<study>_bars.txt`), and
  per take a key lined up with the audio (`aligned/<study>_<player>_key.json`,
  concert pitch = written − 9).

## Labelling
- Scores read with the homr score reader into MusicXML (`omr/`). Page 17 was
  read in two crops.
- Lined up with each recording by the etude aligner, onsets snapped to heard
  attacks. Where a player took a passage an octave from the page, the key
  follows the ear (`resolved="ear_octave"`).
- **Quality**: on average 92% of key notes agree with the heard pitch line.
  The rest are score-reader slips, ornaments and trills, or edition
  differences. Not checked by ear yet. Treat as tier B.

## Uses
- Written-music test on real alto: notes, held notes, vibrato splits.
- Not for training while it is a test set.

## Distribution and licence
- Scores: public domain. Recordings: rights *to verify*. Audio stays on the
  Mac and off the repo.
- Location: `/mnt/project-files/datasets/etude-keys/` (keys, aligned keys,
  scorecard, tools); Mac copy `~/saxscribe-runs/keys/etudes/`.
