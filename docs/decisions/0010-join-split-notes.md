# ADR-0010: Join notes Basic Pitch splits, unless the audio shows a re-attack

- **Date**: 2026-11-02
- **Status**: Superseded by [ADR-0019](0019-split-note-join-off-by-default.md)
- **Decided by**: Claude (routine); merged by Austin
- **PR**: #10

## Context
On every solo set the biggest loss was Basic Pitch cutting one held note in
two (URMP: 5–45% too many notes; Omnibook 1.5–3.2×).

## Decision
After Basic Pitch, join same-pitch neighbours under 30 ms apart, unless the
stem shows a re-articulation (a level dip, or a strong attack where the sound
swells), the same tests the segmenter uses to split repeats. On by default;
`--notes-tool basic_pitch_raw` keeps the old output. The join count goes in `take.json`.

## Consequences
- Tongued repeats must stay two notes; the fixture checks this and still scores 100%.
- If the before/after runs show a loss anywhere, tune or revert in a follow-up.
- Fidelity check: the join never drops a note's time span; it only merges.
