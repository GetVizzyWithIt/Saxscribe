# Datasheet: single-note sample sets

Five sample libraries, one note (or one run) per file. Tier C. Grouped
because they serve the same purpose: checking the pitch tracker across the
range and techniques, and augmentation.

| Set | Sax content | Labels | Licence | Folder |
| --- | --- | --- | --- | --- |
| TinySOL (Ircam, Zenodo 3685367) | 99 alto notes, C#3–A5 × pp/mf/ff | Pitch, dynamic | CC BY 4.0 | `TinySOL/` |
| OrchideaSOL (Ircam Forum) | 377 alto notes in 14 techniques (ordinario, slap, flutter, bisbigliando, key click, aeolian, ...) | Pitch, dynamic, technique | Ircam Forum licence (audio); metadata CC BY 4.0 | `OrchideaSOL/` |
| University of Iowa MIS | 82 alto + 88 soprano files; newer set one note per file, older set chromatic runs | Pitch in filename | Free, no restrictions per the site | `IowaMIS/` |
| Philharmonia | 733 sax MP3s | Pitch, length, dynamic, technique in filename | Philharmonia terms: free to use, no resale | `Philharmonia/` |
| GoodSounds (MTG, Zenodo 820937) | 3,360 single notes and scales, alto/tenor/soprano/bari, one player | Pitch, technique, "goodness" ratings | CC BY 4.0 | `GoodSounds/` |

## Known issues
- OrchideaSOL "ordinario" = the same 99 performances as TinySOL, processed
  differently (not byte-identical). Never split them across train and test.
- 45 OrchideaSOL notes are marked "needed digital retuning": treat their pitch as approximate.
- Iowa's older runs need segmenting into notes before use.
- OrchideaSOL's zip is over 4 GB; on macOS unpack with `ditto -x -k`.

## Uses
- Pitch accuracy by register (low Bb to altissimo) and technique.
- Technique classifiers (slap, flutter, growl) for articulation tags.
- Augmentation material. Not answer keys for note segmentation.
