# Decision log (ADRs)

Architecture decision records, after Michael Nygard's format: one page per
lasting choice, with the context, the decision and its consequences. Append
only. When a decision changes, add a new ADR and mark the old one
"Superseded by ADR-NNNN". Copy [_template.md](_template.md) for a new one.

| # | Decision | Date | Status |
| --- | --- | --- | --- |
| [0001](0001-separate-repo-copied-front-end.md) | Separate repo; copy the game's front end, don't share it | 2026-11-02 | Accepted |
| [0002](0002-four-layers-on-disk.md) | Four layers, each on disk, never discarded | 2026-11-02 | Accepted |
| [0003](0003-concert-pitch-storage.md) | Store concert pitch, transpose only for display | 2026-11-02 | Accepted |
| [0004](0004-mir-eval-scorecard.md) | Every model change is measured with mir_eval against fixed targets | 2026-11-02 | Accepted |
| [0005](0005-instrument-profiles-alto-first.md) | Alto first, tenor first-class, organised per instrument | 2026-11-02 | Accepted |
| [0006](0006-own-crepe-notes-implementation.md) | Reimplement CREPE Notes from the paper instead of using the GPL package | 2026-11-02 | Accepted |
| [0007](0007-omnibook-pairing-by-id.md) | Pair Omnibook stems with performance-aligned MIDI by ID | 2026-11-02 | Accepted |
| [0008](0008-grade-only-against-human-checked-notes.md) | Grade only against human-checked or aligned notes | 2026-11-02 | Accepted |
| [0009](0009-proceed-without-filosax.md) | Proceed with data on hand; Filosax and MedleyDB are later rounds | 2026-11-02 | Accepted |
| [0010](0010-join-split-notes.md) | Join notes Basic Pitch splits, unless the audio shows a re-attack | 2026-11-02 | Superseded by 0019 |
| [0011](0011-dataset-manifest-and-fetch.md) | Dataset manifest in the repo, `fetch` rebuilds the data folder | 2026-11-02 | Accepted |
| [0012](0012-pdf-via-musescore.md) | PDF sheet music engraved by MuseScore from the MusicXML | 2026-11-02 | Accepted |
| [0013](0013-v1-ui-scope.md) | v1 = upload audio, download PDF, optional play-along; local web app for iPad | 2026-11-02 | Accepted |
| [0014](0014-personal-answer-keys-from-paper.md) | Austin's paper transcriptions become personal answer keys via OMR | 2026-11-02 | Accepted, not started |
| [0015](0015-docs-standards.md) | Documentation follows model cards, datasheets, ADRs and CRISP-DM | 2026-11-02 | Accepted |
| [0016](0016-notation-never-drops-notes.md) | Notation never drops a detected note | 2026-11-02 | Accepted |
| [0017](0017-grade-within-answer-key-span.md) | Grade only inside the answer key's time span | 2026-11-02 | Accepted |
| [0018](0018-swing-aware-notation.md) | Readable notation over literal rhythm, without dropping notes | 2026-11-02 | Accepted |
| [0019](0019-split-note-join-off-by-default.md) | Split-note join off by default | 2026-11-02 | Accepted |
| [0020](0020-pick-sax-stem-automatically.md) | Pick the sax stem automatically, sum stems when split | 2026-11-03 | Accepted |
| [0021](0021-beat-from-notes-when-tracker-sparse.md) | Take the beat from the notes when the tracker finds too few beats | 2026-11-03 | Accepted |
| [0022](0022-blues-aware-key-finding.md) | Blues-aware key finding | 2026-11-03 | Accepted |
| [0023](0023-write-only-where-the-sax-plays.md) | On band records, write only where the sax plays (amends 0016) | 2026-11-03 | Accepted |
| [0024](0024-no-pdfs-in-test-and-scorecard-runs.md) | PDFs only for app runs, never in tests or scorecards | 2026-11-03 | Accepted |
| [0025](0025-scorecard-history-files.md) | Scorecard history kept as data files beside the log; app Results page | 2026-11-03 | Accepted |
| [0026](0026-adaptive-minimum-note-length.md) | Basic Pitch's shortest note follows the take's tempo | 2026-11-03 | Proposed (PR #52) |
