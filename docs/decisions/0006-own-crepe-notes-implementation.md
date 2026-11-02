# ADR-0006: Reimplement CREPE Notes from the paper instead of using the GPL package

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Claude (routine)
- **PR**: #6

## Context
CREPE Notes (Riley & Dixon, SMC 2023) reports note F-measure 82.3 vs Basic
Pitch's 75.5 on Filosax. Its package (`crepe-notes`) is GPL-3 and needs madmom.

## Decision
Write our own implementation from the paper's description as
`--notes-tool segment`, working on the saved contour layer. No code copied
from the package.

## Consequences
- Keeps the repo free of GPL obligations.
- Our version lost to Basic Pitch on URMP (46.7 vs 64.4) and ChoraleBricks
  (60.3 vs 77.8). Whether that's our implementation or the data can only be
  settled on Filosax. Parked until then.
