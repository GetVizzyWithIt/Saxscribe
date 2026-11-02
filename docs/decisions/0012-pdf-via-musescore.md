# ADR-0012: PDF sheet music engraved by MuseScore from the MusicXML

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Claude (routine) for Austin's v1 scope; merged by Austin
- **PR**: #12

## Context
v1 must hand Austin a downloadable PDF ([ADR-0013](0013-v1-ui-scope.md)).

## Decision
The notation layer runs the MuseScore command line on each MusicXML to write
`score.pdf` (concert) and `score-<horn>.pdf`. MuseScore is found via
`SAXSCRIBE_MUSESCORE`, `config.local.toml [tools] musescore`, standard Mac
install paths, or the PATH. Without it, nothing fails; MusicXML is still written.

## Alternatives considered
LilyPond (would need a MusicXML conversion step); Verovio (planned for the in-app view, not print).

## Consequences
- MusicXML stays the source of truth; PDFs can always be remade, for any horn, on demand.
- Austin installs MuseScore once: `brew install --cask musescore`.
