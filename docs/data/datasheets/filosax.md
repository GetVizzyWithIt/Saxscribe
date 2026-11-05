# Datasheet: Filosax (pending access)

## Motivation
Made by Foster and Dixon (Queen Mary University of London, ISMIR 2021) for
jazz saxophone transcription and performance analysis. The requirements doc
names it the primary train and test set for solo-recording transcription.

## Composition
- About 48 tunes played by 5 tenor players over jazz backing tracks; Full and Lite versions.
- Note-level annotations (JSON) with onsets, offsets, pitch and more.
- Tier A.

## Uses
- **Role**: v1 gate 1 (solo targets on its test split); training for a note/onset head; like-for-like check against CREPE Notes' published 82.3 note F-measure.
- Loader ready: `python -m saxscribe score filosax --split test` (via mirdata).
- Check its terms before training on it.

## Distribution
Zenodo, on request. Manifest points to record 6335779; earlier notes used
5643843 (Full, 14.5 GB) and 5643734 (Lite, 558 MB). *To verify* once access is granted.

## Status
Requested by Austin, not granted as of 2026-11-02. Austin decided not to wait
([ADR-0009](../../decisions/0009-proceed-without-filosax.md)).

2026-11-05: now the top data ask. The sax-trained note model plan ([ADR-0035](../../decisions/0035-sax-trained-note-model-plan.md)) trains on it first, following Riley and Dixon (2024), with train/dev/test split by player. Austin has to request access again or chase the earlier request. Licence is non-commercial, so trained weights are personal-use only; the Aebersold backings are sold separately.
