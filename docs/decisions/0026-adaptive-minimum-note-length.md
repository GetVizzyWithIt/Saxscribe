# ADR-0026: Basic Pitch's shortest note follows the take's tempo

- **Date**: 2026-11-03
- **Status**: Accepted, conditional on restoring URMP onset recall (PR #52 merged; fix in progress)
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
- **Full scorecards** ([log E26](../evaluation/log.md)): Bach10 87.5% → 97.3%, ChoraleBricks 77.8% → 91.8%, GRFIA alto 66.5% → 75.8%, URMP 64.4% → 69.0%, Parker band records 56.4% → 57.8%, Omnibook flat. **But URMP onset recall fell 89% → 75%**: real short notes are dropped. That breaks the fidelity rule, so this ADR stays accepted only on condition the follow-up fix restores onset recall.
- PR #57 restores re-tongued repeats (a loudness dip of 10 dB or more just before the attack): the URMP onset-recall loss shrinks from 15 to 8 points, about 80% of restored notes real ([log E27](../evaluation/log.md)). Still conditional on closing the rest.
- Every take's chosen minimum should be recorded in `take.json` so a lost note can be traced to the setting.
