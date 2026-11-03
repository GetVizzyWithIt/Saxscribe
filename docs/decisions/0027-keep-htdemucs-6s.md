# ADR-0027: Keep Demucs htdemucs_6s as the separator

- **Date**: 2026-11-03
- **Status**: Accepted (no code change)
- **Decided by**: Claude (build thread), from the separator comparison
- **PR**: none

## Context
Phase 2 planned to measure newer separators against Demucs `htdemucs_6s`,
which has no sax stem and leaves other instruments in the stem the sax lands in.

## Decision
Keep `htdemucs_6s`. Two averaged shifts are a candidate optional quality
setting, not the default.

## Consequences
- Note F1 on 10 Parker band records / Blues for Mary Jane: htdemucs_6s 56.4% / 51.0%; two shifts 57.0% / 54.3% (+50% time); htdemucs_ft 52.2% / 32.3%; BS-RoFormer 52.7% / 39.8%, both 3–4× slower ([log E25](../evaluation/log.md)).
- The separator is not the cheap win; better sax isolation needs a sax-specific model (sax-vs-rest fine-tune) or a transcriber that tolerates bleed.
- The weights' likely non-commercial licence (see the [Demucs card](../models/demucs.md)) stays a limit for any public release.
