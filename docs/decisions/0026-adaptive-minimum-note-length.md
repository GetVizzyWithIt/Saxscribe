# ADR-0026: Basic Pitch's shortest note follows the take's tempo

- **Date**: 2026-11-03
- **Status**: Proposed (PR #52 open; full scorecards pending)
- **Decided by**: Claude (build thread), from a settings sweep
- **PR**: #52

## Context
Basic Pitch keeps notes down to a fixed minimum length; Saxscribe used 50 ms
(the library default is 127.7 ms) so fast bebop runs survive. On slower
material that lets through short ghost and split notes: 55 extra notes on 136
in Blues for Mary Jane (log E19), and many on GRFIA takes.

## Decision
Set the minimum per take: 0.4 × the median gap between note starts, clamped
to 50–128 ms. Turn the melodia trick off. Keep the fixed 50 ms behaviour as
`--notes-tool basic_pitch_fixed`.

## Consequences
- Note F1: GRFIA alto +9.0, tenor +10.5; Blues for Mary Jane +2.0; Omnibook −0.2 ([log E23](../evaluation/log.md)).
- **Fidelity cost**: on the Omnibook it drops 473 of 15,206 notes that matched the answer key. These are real played notes, so this trades a few true notes for many fewer ghosts. The project rule is fidelity over playability; accept only if the full scorecards show the lost notes are rare and confined to the fastest passages, and consider a safeguard (keep a short note when the pitch line or an onset confirms it).
- Every take's chosen minimum should be recorded in `take.json` so a lost note can be traced to the setting.
