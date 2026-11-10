# ADR-0040: Adopt the bias checks standard

- **Date**: 2026-11-10
- **Status**: Accepted
- **Decided by**: Austin
- **PR**: this docs PR

## Context
Austin wrote a draft "Bias checks" standard (2026-11-09) for all his projects. Its 11 checks are meant to show both the builder's habits and the owner's. They cover naming options, building the simplest thing, proving claims, checking facts that move, questioning the ask, arguing against big plans, naming blind spots, stopping experiments that stop paying, outside review and looking back. He asked to adopt it in this repo on 2026-11-10.

## Decision
Add the standard as [docs/standards/bias-checks.md](../standards/bias-checks.md) and link it from CLAUDE.md. From now on, decision records include "Options considered" and "Case against" sections. Big choices also get a "Reviewed by" line and a later "Look back".

## Options considered
- **Adopt as written (chosen):** one shared standard across Austin's projects.
- **Fold the checks into CLAUDE.md:** they'd be loaded every session, but the file would get longer and drift away from the shared copy.
- **Keep it as a draft:** no cost now, but nothing would change.

## Case against
Extra process on a project that already moves step by step. This breaks if checks turn into boilerplate: "Case against" sections nobody reads, or every small change treated as big. Watch for ADRs whose case against is a stock phrase. Check 9's stop rule could also cut off a line of experiments that was about to pay off. The quiet-low-sax work had several losing rounds (E70, E72, E74) before E77 gained ground.

## Consequences
- Older ADRs keep "Alternatives considered". New ones use the new template.
- Experiment streaks now have a stop rule (three without beating the best).

## Look back
To fill in after a few months.
