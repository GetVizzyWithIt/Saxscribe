# ADR-0038: Adopt Austin's development standards (lockfile, CI, branch names)

- **Date**: 2026-11-06
- **Status**: Accepted
- **Decided by**: Austin
- **PR**: lockfile and Python pin, CI, numpy 2 loader fix, this docs PR

## Context
Austin set one list of development standards for all his repos. Saxscribe met
most (README commands, setup with health check, tests, ADRs, glossary, secrets
out of git) but had no lockfile, no pinned Python file, no CI, and branch names
like `claude/project-thread-xxxx` that say nothing about the change. Main also
had a failing test on numpy 2.

## Decision
Pin Python in `.python-version`, install from a committed `requirements.lock`,
run the tests on every PR in GitHub Actions, and name branches
`claude/<type>-<what>`. The standards and their status are tracked in
[docs/development-standards.md](../development-standards.md).

## Alternatives considered
- A uv or Poetry project instead of a requirements lock: would change Austin's
  update command and add a tool; pip with a lock keeps it the same.
- A universal (all-platform) lock: Demucs 4.1 can't resolve on Intel Macs with
  torch 2.8, and Linux needs different torch builds, so the lock is for Apple
  Silicon and CI adapts it (CPU torch, no Core ML).
- Migrations and automatic deploys: no database and no server, so they don't
  apply (see the standards page).

## Consequences
Installs are repeatable and a relock can't move the scorecard model versions by
accident. A red CI check now blocks a merge once Austin turns on the branch
rule. Upgrading a pinned model version is a deliberate PR with a scorecard.
