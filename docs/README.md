# Saxscribe documentation

The living record of what Saxscribe is for, how it works, what models and data
it uses, how well it does, and why it was built this way. The requirements doc
("Sax Transcription Tool — Requirements and Project Instructions", 2 Nov 2026)
stays the source of truth for intent; these pages turn it into something that
can be checked against the code and the scorecards.

Last full review: 2026-11-03. PR state 2026-11-06: everything through #127 merged. #124–#127 are tooling, not model changes: numpy 2 safe-loader test fix, pinned Python and `requirements.lock`, CI running pytest on every PR, and development standards ([development-standards.md](development-standards.md), ADR-0038). #84 stays closed; its change merged as #93.

**To run the tool**, see [Quick start](../README.md#quick-start-copy-and-paste) in the repo README.

## Map

The folders follow the phases of CRISP-DM, the standard data-science project
cycle (business understanding, data understanding, data preparation, modeling,
evaluation, deployment).

| CRISP-DM phase | Page | What it answers |
| --- | --- | --- |
| Business understanding | [product/prd.md](product/prd.md) | Who it's for, what it must do, how we know it's good enough |
| | [product/roadmap.md](product/roadmap.md) | Phases, their gates, and where we are |
| Data understanding | [data/README.md](data/README.md) | Every dataset, its labels, licence and role |
| | [data/datasheets/](data/datasheets/) | One datasheet per dataset (Gebru et al. "Datasheets for Datasets" format) |
| Data preparation | [data/README.md#splits-and-leakage](data/README.md#splits-and-leakage) | Splits, pairing, what may never be graded against |
| Modeling | [architecture/system.md](architecture/system.md) | The four-layer pipeline and every file it writes |
| | [models/](models/README.md) | One model card per model (Mitchell et al. "Model Cards" format) |
| Evaluation | [evaluation/protocol.md](evaluation/protocol.md) | Metrics, tolerances, test sets, targets |
| | [evaluation/log.md](evaluation/log.md) | Every scorecard run, dated, with settings and commit |
| Deployment | [architecture/system.md#deployment](architecture/system.md#deployment) | Mac-local CLI now; local web app for v1 |
| Across all phases | [decisions/](decisions/README.md) | Architecture decision records (ADRs): one page per lasting choice |
| | [glossary.md](glossary.md) | Music, signal and ML terms in plain language |

## How these docs are kept up to date

- **Every PR that changes behaviour updates the docs in the same PR.** A new
  model or tool gets a model card; a new answer-key set gets a datasheet; a
  scorecard run gets a row in the evaluation log; a lasting choice gets an ADR.
- **Numbers come only from scorecard runs.** Each figure in the evaluation log
  names the date, commit, set, settings and the machine it ran on. If a number
  can't be traced to a run, it doesn't go in.
- **Decisions are append-only.** An ADR that stops being true is marked
  "Superseded by ADR-NNNN", not deleted, so the reasoning stays readable.
- **Unknowns are written down, not guessed.** Anything not yet checked is
  marked *to verify* and listed under "Open documentation items" below.
- **Papers are summarised, not quoted.** Cite the paper; describe the method
  in our own words.

## Open documentation items

- GRFIA audio-to-score: confirm the paper, the exact licence terms, the
  alto/tenor split and the manifest entry.

- Bach10 licence: read `Dataset_v1.0.pdf` inside the download and record it.
- Weimar Jazz Database licence: the dataset search noted ODbL; the manifest
  says "not stated on the download page". Confirm on jazzomat.hfm-weimar.de.
- Filosax record number: the manifest points at Zenodo 6335779; earlier notes
  used 5643843 (full) and 5643734 (lite). Confirm which is current once access
  is granted.
- Omnibook manifest entry says "no isolated stems", but the loader reads
  `audio_stems/` and grades 46 stems. The manifest description should be fixed.
- Vibrato Dataset licence: manifest says AGPL-3.0, the search report says GPL.
  Either way, use it for evaluation only, never ship code from it.
- The project folder's SMC 2023 PDF (pages 72-78) holds the Järveläinen et al.
  vibrotactile paper, not CREPE Notes. The CREPE Notes paper (Riley & Dixon,
  SMC 2023, Zenodo 8315899) should be added if a local copy is wanted.
