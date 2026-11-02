"""Layer 4: notation.

For now this writes score.mid: every note at its exact time, no quantizing,
so it lines up with source.wav. Step 2 adds music21: quantized rhythm on the
beat grid, swing, key and spelling, and MusicXML export.
"""
from __future__ import annotations

from .. import frontend
from ..take import Take
from . import notes as notes_layer

TICKS = 960   # per beat
BPM = 120.0   # fixed, so a tick is an exact slice of a second (1/1920 s)


def run(take: Take) -> None:
    frontend.log("Layer 4/4: notation (MIDI)")
    data = notes_layer.read(take)
    write_midi(take.midi, data["notes"])
    take.record("notation", tool="mido", format="midi", quantized=False)
    frontend.log(f"  wrote {take.midi.name} with {len(data['notes'])} notes")


def write_midi(path, notes: list[dict]) -> None:
    import mido
    per_second = TICKS * BPM / 60.0
    events = []
    for n in notes:
        vel = int(max(1, min(127, round(40 + 87 * float(n.get("amp", 0.5))))))
        events.append((round(n["onset"] * per_second), 1, n["pitch"], vel))
        events.append((round(n["offset"] * per_second), 0, n["pitch"], 0))
    events.sort(key=lambda e: (e[0], e[1]))  # note-offs before note-ons at the same tick
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    track.append(mido.Message("program_change", program=65, time=0))  # alto sax
    now = 0
    for tick, on, pitch, vel in events:
        track.append(mido.Message("note_on" if on else "note_off", note=pitch, velocity=vel,
                                  time=tick - now))
        now = tick
    mid = mido.MidiFile(ticks_per_beat=TICKS)
    mid.tracks.append(track)
    mid.save(str(path))
