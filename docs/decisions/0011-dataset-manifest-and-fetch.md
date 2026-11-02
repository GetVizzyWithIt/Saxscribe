# ADR-0011: Dataset manifest in the repo, `fetch` rebuilds the data folder

- **Date**: 2026-11-02
- **Status**: Accepted
- **Decided by**: Claude (routine); merged by Austin
- **PR**: #11

## Context
Datasets can't live in the repo, but results must be reproducible on another
machine (e.g. a Colab GPU).

## Decision
`datasets/manifest.json` (byte-identical to the Mac's `~/mir_datasets/MANIFEST.json`;
20 datasets, 217 files) lists every source with page, licence, access and md5.
`python -m saxscribe fetch` downloads, verifies and unpacks; manual datasets
are listed with their page.

## Consequences
- Failed checksums are never unpacked; unsafe archive paths are refused.
- The manifest is now the place to record licence facts; datasheets link to it.
