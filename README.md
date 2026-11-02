# saxscribe

Turns a saxophone performance into notes you can read and fix, and keeps
everything underneath them: the continuous pitch line, the note events, and
the timing against the beat. Alto first.

It is a sibling of Songs in the Key of Life, not part of it. The audio front
end (decoding, Demucs, Beat This!, Basic Pitch) was copied from the game's
analyzer and is kept as a private copy, because the two tools want opposite
things: the game reduces a part into something playable, this tool stays
faithful to it.

## Setup (Mac)

```bash
bash setup_mac.sh
source .venv/bin/activate
python -m saxscribe check
```

For PDF sheet music, also install MuseScore (free): `brew install --cask musescore`.
Without it everything else works and you get MusicXML only.

## Use

```bash
python -m saxscribe transcribe ~/Music/take.wav               # a solo take
python -m saxscribe transcribe ~/Music/record.mp3 --mix       # sax inside a full band
python -m saxscribe transcribe ~/Music/Takes/                 # a whole folder
python -m saxscribe transcribe ~/Music/take.wav --redo notes  # remake notes and notation
```

Results go in a folder next to the file (`take.saxscribe/`), or wherever `-o` says.

| Option | What it does |
| --- | --- |
| `--mix` | Separate stems with Demucs first. All six stems stay in `stems/` to listen to |
| `--stem piano` | Use another stem if the sax landed somewhere else (default `other`) |
| `--horn tenor` | Pitch range for tenor (default alto) |
| `--redo LAYER` | Remake a layer and the ones above it; the ones below are left alone |
| `--contour-tool pyin` | Use pYIN instead of CREPE for the pitch line |
| `--notes-tool contour` | Cut notes from the pitch line instead of Basic Pitch |
| `--swing 2` | Swing ratio for the notation (`auto` detects it, `straight` turns it off) |

## What's in a take's folder

Four layers, each its own file, so you can fix one by hand and re-run only
what sits above it. Pitch is stored at concert pitch.

| Layer | File | What it holds |
| --- | --- | --- |
| 1. Isolate | `source.wav`, `stem.wav`, `accompaniment.wav`, `stems/` | The original, and the sax on its own (a copy for solo takes) |
| 2. Contour | `contour.csv` | Pitch every 10 ms with a confidence, from CREPE |
| 3. Notes | `notes.json` | Notes (onset, offset, pitch, cents off, articulation tags), beats, tempo |
| 4. Notation | `score.musicxml`, `score-alto.musicxml`, `score.pdf`, `score-alto.pdf`, `score.mid`, `notation.json` | Readable notation at concert pitch and written for the horn, as MusicXML and as PDF (when MuseScore is installed); MIDI at the exact played times, lined up with the audio; and each note's bar and beat |

`take.json` records which tool made each layer and when.

Open the `.musicxml` files in MuseScore. How the notation is made (beat grid,
swing, sixteenths or triplets, key and spelling) is described at the top of
`saxscribe/layers/notation.py`.

## Scorecard

Every model change is measured on recordings with known answers, using
mir_eval (the standard music-transcription scores), so numbers compare with
published ones.

```bash
python -m saxscribe score omnibook                 # Charlie Parker Aligned Omnibook
python -m saxscribe score filosax --split test     # Filosax (needs access, and pip install mirdata)
python -m saxscribe score pairs --data ~/Music/saxscribe-etudes   # your own takes
python -m saxscribe score omnibook --notes-tool contour           # compare another setting
```

Each run keeps its take folders and writes `scorecard.md` and `scorecard.json`
under `~/saxscribe-runs/<set>/<settings>/`, with the v1 targets from the
requirements alongside. Dataset folders come from `--data`, else
`config.local.toml` (see `config.local.example.toml`), else `~/mir_datasets/`.
Train and test splits go by tune, never by take.

| Set | What it is | Where to get it |
| --- | --- | --- |
| omnibook | 46 Charlie Parker solos: separated alto stems with performance-aligned MIDI | [Zenodo 14628467](https://zenodo.org/records/14628467), open |
| omnibook-mix | the same solos from the full records, separated by Demucs first | same download |
| filosax | 48 tunes, 5 players, solo sax over backing tracks, note annotations | [Zenodo 5643843](https://zenodo.org/record/5643843), on request |
| pairs | any folder of audio files, each with a same-named .mid | your own takes |

### Answer keys for your own playing

Record yourself playing something written down, then line the score up with
the take:

```bash
python -m saxscribe answer-key take.wav etude.musicxml   # writes take.mid next to it
```

It assumes the score is written for alto in E-flat; add `--score-pitch concert`
if it is not. It stretches the score onto the recording (dynamic time warping
on pitch-class content), then nudges each note to the nearest attack heard.
Put the takes and their .mid files in one folder and score it as `pairs`.

## Tests

```bash
python -m pytest
```

The tests build a 10-second synthetic alto phrase (slurs, tongued repeats,
vibrato, rests) and check each layer on it. No audio files live in the repo.
