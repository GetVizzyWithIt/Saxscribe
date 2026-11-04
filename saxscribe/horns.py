"""Instrument ranges and transpositions. Everything is stored at concert pitch.

Each horn has three written notes (MIDI numbers, the note as the player reads it):
  low        the lowest key (low Bb on most saxes, low A on a modern baritone)
  top        the top of the keyed range (high F#; some horns have a high G key)
  altissimo  the highest altissimo note a strong player reaches on that horn.
             Above it nothing is a sax note: the detector heard an overtone.
Notes between top and altissimo are altissimo: real, played with special
fingerings, and never moved. The concert range is the written one minus the
horn's transposition.

The table is per instrument so other instruments can join it later (a
trumpet, a flute...) with the same three numbers. Range rules that use it are
in layers/ranges.py.
"""
from __future__ import annotations

from dataclasses import dataclass

CREPE_MAX_HZ = 2000.0  # torchcrepe can't look above about 2006 Hz
BEND_ROOM = 2          # semitones searched below the lowest note: a lipped-down low note or flat tuning


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


@dataclass(frozen=True)
class Horn:
    name: str
    key: str               # the horn's key, for transposed display
    written_shift: int     # semitones to add to concert pitch to get written pitch
    written_interval: str  # the same, as an interval name for music21
    low_written: int       # lowest written note (MIDI)
    top_written: int       # top of the keyed range, written
    altissimo_written: int  # highest altissimo note, written
    family: str = "sax"

    # Concert pitch (what the notes layer stores).
    @property
    def low(self) -> int:
        return self.low_written - self.written_shift

    @property
    def top(self) -> int:
        return self.top_written - self.written_shift

    @property
    def altissimo(self) -> int:
        return self.altissimo_written - self.written_shift

    # What the pitch tools search: a little below the lowest note, a semitone above the altissimo.
    @property
    def min_hz(self) -> float:
        return round(hz(self.low - BEND_ROOM), 1)

    @property
    def max_hz(self) -> float:
        return round(hz(self.altissimo + 1), 1)

    def register(self, concert: int) -> str:
        """'below', 'standard', 'altissimo' or 'above' for a concert MIDI note."""
        if concert < self.low:
            return "below"
        if concert <= self.top:
            return "standard"
        if concert <= self.altissimo:
            return "altissimo"
        return "above"

    def playable(self, concert: int) -> bool:
        return self.low <= concert <= self.altissimo


# Written notes: Bb3 = 58, A3 = 57, F#6 = 90, F7 = 101, A7 = 105.
LOW_BB, LOW_A, HIGH_FS = 58, 57, 90

HORNS = {
    # Soprano sounds a major second below written. Altissimo is hard on soprano: to written F7.
    "soprano": Horn("soprano", "Bb", 2, "M2", LOW_BB, HIGH_FS, 101),
    # Alto sounds a major sixth below written: written Bb3 (low Bb) is concert Db3.
    # Keyed range to concert A5, altissimo to written A7 = concert C7.
    "alto": Horn("alto", "Eb", 9, "M6", LOW_BB, HIGH_FS, 105),
    # Tenor sounds a major ninth below written: low Bb is concert Ab2.
    # Keyed range to concert E5, altissimo to written A7 = concert G6.
    "tenor": Horn("tenor", "Bb", 14, "M9", LOW_BB, HIGH_FS, 105),
    # Baritone sounds an octave and a major sixth below written: low A is concert C2.
    # Altissimo to written F7 = concert Ab5.
    "baritone": Horn("baritone", "Eb", 21, "M13", LOW_A, HIGH_FS, 101),
}
