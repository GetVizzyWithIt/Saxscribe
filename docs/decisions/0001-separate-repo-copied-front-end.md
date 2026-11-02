# ADR-0001: Separate repo; copy the game's front end, don't share it

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Austin
- **PR**: #1

## Context
The requirements doc suggested factoring Stage 1 of the Songs in the Key of
Life analyzer (decode, separate, beats, notes) into a package both projects
import. The two projects want opposite things: the game's chart model learns
to reduce a part to something playable; Saxscribe must stay faithful and must
never learn to omit notes. Austin felt the models should be isolated "for
integrity's sake".

## Decision
Saxscribe is its own private repo (GetVizzyWithIt/Saxscribe). The game's front
end is copied into `saxscribe/frontend.py` (from game commit `18a6548`) and
allowed to diverge. Nothing is imported from the game; nothing from its chart
model comes over.

## Alternatives considered
- Shared package: less duplicate code, but every change to the game's front
  end would move Saxscribe's scorecard, and the boundary would be harder to keep.

## Consequences
- Fixes found in one project are ported by hand (e.g. the torchaudio <2.9 cap).
- Saxscribe already diverged: Basic Pitch minimum note 50 ms (game 80 ms).
- Resolves the requirements doc's open question "factor out cleanly, or copy and diverge?".
