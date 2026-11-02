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

## What's in a take's folder

Four layers, each its own file, so you can fix one by hand and re-run only
what sits above it. Pitch is stored at concert pitch.

| Layer | File | What it holds |
| --- | --- | --- |
| 1. Isolate | `source.wav`, `stem.wav`, `accompaniment.wav`, `stems/` | The original, and the sax on its own (a copy for solo takes) |
| 2. Contour | `contour.csv` | Pitch every 10 ms with a confidence, from CREPE |
| 3. Notes | `notes.json` | Notes (onset, offset, pitch, cents off, articulation tags), beats, tempo |
| 4. Notation | `score.mid` | The notes as MIDI at their exact times |

`take.json` records which tool made each layer and when.

Coming next: MusicXML with quantized rhythm, swing, key and spelling (music21),
and a scorecard against a known answer key with mir_eval.

## Tests

```bash
python -m pytest
```

The tests build a 10-second synthetic alto phrase (slurs, tongued repeats,
vibrato, rests) and check each layer on it. No audio files live in the repo.
