# saxscribe

Turns a saxophone performance into notes you can read and fix, and keeps
everything underneath them: the continuous pitch line, the note events, and
the timing against the beat. Alto first.

It is a sibling of Songs in the Key of Life, not part of it. The audio front
end (decoding, Demucs, Beat This!, Basic Pitch) was copied from the game's
analyzer and is kept as a private copy, because the two tools want opposite
things: the game reduces a part into something playable, this tool stays
faithful to it.

## Quick start (copy and paste)

**After merging PRs: update and start the app.** In the Terminal window where
the app is running, press Ctrl-C to stop it, then:

```bash
cd ~/Desktop/saxscribe && git checkout main && git pull && source .venv/bin/activate && pip install -r requirements.txt && python -m saxscribe app
```

**Start the app with no update:**

```bash
cd ~/Desktop/saxscribe && source .venv/bin/activate && python -m saxscribe app
```

On the Mac it opens a browser tab at http://localhost:8765. On the iPad
(same Wi-Fi), open the address it prints: "On your iPad: http://…:8765/".
Results page: the same address with `/results`. Finished sheet music is also
copied to `~/Desktop/Saxscribe`.

**Transcribe from the Terminal** (after `source .venv/bin/activate`):

```bash
python -m saxscribe transcribe ~/Music/take.wav                      # solo alto take
python -m saxscribe transcribe ~/Music/take.wav --horn tenor         # solo tenor (soprano, alto, tenor or baritone)
python -m saxscribe transcribe ~/Music/record.mp3 --mix --horn tenor # sax inside a full band
```

**Run a scorecard** (results also appear on the Results page):

```bash
python -m saxscribe score grfia-alto --note "what changed"
```

Sets: `omnibook`, `omnibook-mix`, `urmp`, `urmp-mix`, `bach10`, `bach10-mix`,
`choralebricks`, `grfia-alto`, `grfia-tenor`, `filosax`, `pairs`. Add
`--limit 10` for a quick run.

**Run the tests:** `python -m pytest`

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
| `--stem other` | Force a stem (or a sum such as `other+guitar`); the default, `auto`, picks the stem holding the sax |
| `--horn tenor` | Soprano, tenor or baritone instead of alto (default): pitch range and written key |
| `--range-rules flag` | How notes outside the horn's range are handled: `out` (default) moves notes no sax can play by octaves into range and tags altissimo; `overtones` also checks every note for a likely overtone and moves it down (tested 2026-11-04: wrong far more often than right, so off by default); `flag` only tags, overtones included; `off` skips it. Nothing is ever deleted; a moved note keeps its `detected_pitch`. See `saxscribe/layers/ranges.py` |
| `--redo LAYER` | Remake a layer and the ones above it; the ones below are left alone |
| `--contour-tool pyin` | Use pYIN instead of CREPE for the pitch line |
| `--notes-tool contour` | Cut notes from the pitch line instead of Basic Pitch |
| `--swing 2` | Swing ratio for the notation (`auto` detects it, `straight` turns it off) |

## The app

```bash
python -m saxscribe app
```

This opens a page in the browser where you upload a recording (alto or
tenor, solo or with a band) and get back:

- **Sheet music**: PDF, MusicXML and MIDI, written for alto, tenor or concert.
  The PDF comes from MuseScore when it's installed. Without it, the PDF
  button opens the score as letter pages to print or save as PDF from the browser.
  Every PDF carries the song's title, "As played by" the artist, and
  "Transcribed with Saxscribe". Title and artist come from the file's tags
  unless you type them at upload.
- **A play-along**: the score scrolls with the recording, the note being
  played lights up, and tapping a note jumps there. You can play at 50 to
  100% speed with the pitch kept. For a band recording you can switch to the
  sax alone or the band alone. A− and A+ make the notes smaller or bigger.

It runs on the Mac. To use it on an iPad on the same Wi-Fi, open the address
it prints ("On your iPad: http://…:8765/"). Uploads and their take folders
live in `~/saxscribe-library/` (change it with `--library`). While a take runs, the page shows its progress lines; Stop ends it, Run again restarts it and Remove deletes it. Each take folder
is the same as one made by `transcribe`. Use `--host 127.0.0.1` to keep the
app to this Mac only.

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
python -m saxscribe score grfia-alto --tag altissimo              # only takes with a technique tag
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

## Documentation

Product requirements, architecture, model cards, datasheets, the evaluation
log and the decision log are in [docs/](docs/README.md).
