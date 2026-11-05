# ADR-0035: Plan for a sax-trained note model: fine-tune Basic Pitch first

- **Date**: 2026-11-05
- **Status**: Proposed (plan; no training run yet)
- **Decided by**: Claude (note-model thread), plan for Austin's review
- **Plan**: https://claude.ai/artifact/9oPaB15bENmCzL49qAnb1Q
- **Relates to**: [ADR-0016](0016-notation-never-drops-notes.md), [ADR-0026](0026-adaptive-minimum-note-length.md)

## Context
Settings and rule changes have stopped paying off (onset tests E44, E45 and E47; separators E30 and E51). The tool reaches 76–97% note F1 on clean solo sax but the mid-50s to low 60s on band records. Off-the-shelf note models were not trained on sax in a band.

## Options, in order
1. **Fine-tune Basic Pitch** (Apache 2.0, under 20k weights). Training code ships in basic-pitch 0.4.0 (`basic_pitch/train.py`), and it trains on the Mac.
2. **Test YourMT3+ as it is**, in Colab (GPL-3, about 45M weights). It labels the instrument of each note.
3. **Fallback**: our own small model on top of CREPE and onset model v2.

## Data
- About 4 hours of real, labelled sax on hand, mostly solo.
- **Filosax** moves to top priority: about 24 hours of jazz tenor, 5 players, restricted, non-commercial terms; the Aebersold backings are bought separately. Austin has to request it.
- Band training audio is built by mixing clean labelled sax over band audio with no sax.
- Weimar's 271 sax solos, rendered with MIDI-DDSP sax, are used only for warm-up. Same-player, same-tune leakage is removed.
- Austin's six answer keys (3,298 notes, about 11 minutes of sax, beat-level timing; pitch agreement with the mix 32–87%) stay test-only. A leave-one-out final tune may use them at the end.

## Validation
- Train, dev and locked test piles split by tune (Filosax: by player).
- Add a bar-level metric (bars written right) and an ear check of each key's noise floor.

## Stages and gates (about 5 weeks)
- Stages 0–4.
- Stage 1, solo: +2 points note F1.
- Stage 2, jazz band: +3 points note F1 and +5 points bars right.
- Stage 3, cloud GPU (roughly $50–150 per run, prices approximate): only if stage 2 stalls.
- Every stage also has to pass the never-drop rule (ADR-0016).

## Consequences
- Basic Pitch stays the default until a stage clears its gate.
- Filosax and GRFIA terms make any trained weights personal-use only.
- Austin's own recordings remain out of training, as he decided on 2026-11-04.
