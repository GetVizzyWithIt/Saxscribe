# ADR-0015: Documentation follows model cards, datasheets, ADRs and CRISP-DM

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Austin (asked for industry-standard data-science docs)

## Context
Austin asked for project, product, model, requirements and data documentation
kept to data-science industry standards, maintained as the project moves.

## Decision
`docs/` holds a PRD and roadmap, a system doc, model cards (Mitchell et al.
2019), datasheets (Gebru et al. 2021), an evaluation protocol and dated log,
ADRs (Nygard), and a glossary, mapped to CRISP-DM phases in `docs/README.md`.
PRs that change behaviour update the docs in the same PR.

## Consequences
Numbers in the docs must trace to a scorecard run; unknowns are marked *to verify*.
