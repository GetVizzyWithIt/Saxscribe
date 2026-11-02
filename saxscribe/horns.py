"""Saxophone ranges and transpositions. Everything is stored at concert pitch."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Horn:
    name: str
    key: str            # the horn's key, for transposed display
    written_shift: int  # semitones to add to concert pitch to get written pitch
    written_interval: str  # the same, as an interval name for music21
    min_hz: float       # a little below the lowest concert note
    max_hz: float       # high enough for altissimo


HORNS = {
    # Alto sounds a major sixth below written: written Bb3 (low Bb) is concert Db3.
    "alto": Horn("alto", "Eb", 9, "M6", 125.0, 1600.0),
    # Tenor sounds a major ninth below written: low Bb is concert Ab2.
    "tenor": Horn("tenor", "Bb", 14, "M9", 95.0, 1100.0),
    # Baritone sounds an octave and a major sixth below written: low A is concert C2.
    "baritone": Horn("baritone", "Eb", 21, "M13", 60.0, 800.0),
}
