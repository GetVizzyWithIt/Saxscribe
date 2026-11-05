"""saxscribe: transcribe a saxophone performance and keep every layer of it.

A take's folder holds four layers, each saved to disk so any one can be re-run
or fixed by hand without redoing the ones below it:

  1. isolate   stem.wav            the sax on its own (a copy for solo takes)
  2. contour   contour.csv         pitch every 10 ms, with a confidence
  3. notes     notes.json          note events, beats, tempo
  4. notation  score.mid           the notes as MIDI (MusicXML comes next)

take.json records which tool made each layer. Pitch is always stored at
concert pitch.
"""

LAYOUT_VERSION = 1
LAYERS = ("isolate", "contour", "notes", "notation")

import warnings

# resampy (used by CREPE) imports pkg_resources, and setuptools warns about that
# on every run. requirements.txt pins setuptools<81 so it keeps working; this
# just keeps the warning out of the progress log.
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)
