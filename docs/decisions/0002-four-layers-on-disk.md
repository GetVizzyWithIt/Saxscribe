# ADR-0002: Four layers, each on disk, never discarded

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: requirements doc
- **PR**: #1

## Context
Austin wants to fix any layer by hand and see what lies beneath a note (the
bend, the vibrato), and edits are future training data.

## Decision
Isolate, contour, notes and notation are separate files in a take folder.
A layer re-runs only if missing, named by `--redo`, or a lower layer just ran.
No layer deletes a lower one. `take.json` records which tool made each layer.

## Consequences
- A hand-fixed `notes.json` survives `--redo notation`.
- Scorecards reuse lower layers across settings, so comparing note tools is cheap.
- Disk use per take is larger (stems, contour CSV); acceptable on the Mac.
