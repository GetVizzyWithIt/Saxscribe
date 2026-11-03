# ADR-0026: Basic Pitch's shortest note follows the take's tempo

- **Date**: 2026-11-03
- **Status**: Accepted, with the fidelity caveat below (PR #52)
- **Decided by**: Claude (build thread), from a settings sweep
- **PR**: #52

## Context
Basic Pitch keeps notes down to a fixed minimum length; Saxscribe used 50 ms
(the library default is 127.7 ms) so fast bebop runs survive. On slower
material that lets through short ghost and split notes: 55 extra notes on 136
in Blues for Mary Jane (log E19), and many on GRFIA takes.

## Decision
Set the minimum per take: 0.4 × the median gap between note starts, clamped
to 50–128 ms. Turn the melodia trick off. On fast passages (onsets under
200 ms apart), bring back a removed short note when it has its own attack and
a pitch different from both neighbours. Keep the fixed 50 ms behaviour as
`--notes-tool basic_pitch_fixed`.

## Consequences
- Note F1: GRFIA alto 67.4% → 76.3%, tenor 56.8% → 67.4%; Blues for Mary Jane 53.6% → 56.2%; Omnibook 64.2% → 64.2% ([log E23](../evaluation/log.md)).
- **Fidelity caveat**: on the Omnibook, the fastest material we have, about 350 notes that match the answer key are no longer written (490 before the safeguard, 134 recovered). The same change removes about 350 ghost notes there, so the score is flat, but these are real played notes. Accepted because the gain on every other set is large; revisit with a trained onset model, and check the lost notes by hand on one Parker solo.
- Every take's chosen minimum should be recorded in `take.json` so a lost note can be traced to the setting.
