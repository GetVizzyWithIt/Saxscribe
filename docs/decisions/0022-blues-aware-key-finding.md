# ADR-0022: Blues-aware key finding

- **Date**: 2026-11-03
- **Status**: Accepted (PR #34 merged)
- **Decided by**: Claude (routine, from scorecard evidence)
- **PR**: #34

## Context
The key sets the key signature and the spelling of every accidental, in
concert and on the horn's part. music21's key finder put Blues for Mary Jane
(concert C) in F major, because the blues flat seventh and the IV chord look
like F. Blues is a large share of what Austin will transcribe.

## Decision
Weight notes by how long they sound, and match them against a blues profile
as well as music21's major and minor keys. When the blues profile fits
better, its home note wins and the key is written as major, as blues charts
are.

## Consequences
- Weimar Jazz Database (429 solos with known keys): home note right 49% → 60% overall, 47% → 70% on 12-bar blues; Blues for Mary Jane F → C ([log E15](../evaluation/log.md)).
- Minor tunes lose about 4 points (58% → 54%). A guard was tried and dropped; revisit if Austin's minor tunes come out wrong.
- The Weimar Jazz Database becomes the key-finding test set. It also sets a ceiling below 100%, because its labels are the tune's key, not the key a solo stays in.
- Chord-aware spelling (roadmap) would build on this.
