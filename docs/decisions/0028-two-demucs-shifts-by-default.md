# ADR-0028: Run Demucs with two averaged shifts by default

- **Date**: 2026-11-04
- **Status**: Proposed (PR #61 open)
- **Decided by**: Claude (build thread), from separator round 2; Austin asked the question
- **PR**: #61
- **Refines**: [ADR-0027](0027-keep-htdemucs-6s.md)

## Context
ADR-0027 kept Demucs `htdemucs_6s` and left two averaged shifts as a possible
quality setting. Austin asked (2026-11-03) whether that was right, or whether
another tool should run after Demucs or replace it. Round 2 tested ten
alternatives on the Parker band records and Blues for Mary Jane ([log E30](../evaluation/log.md)).

## Decision
Keep `htdemucs_6s` as the only separator, and run it with two averaged shifts
by default.

## Consequences
- Note F1 57.1% → 57.9% (Parker), 53.1% → 55.0% (Blues for Mary Jane); more notes found on both; separation takes about 50% longer.
- Not adopted: the UVR woodwind model and the pitch-guided filter each scored higher on one set but lost real notes or pitch accuracy on the other; AudioSep and a BS-RoFormer cascade added nothing; Demucs twice was slightly worse; Banquet was worst by far.
- Better isolation still needs a sax-specific separator; none of the off-the-shelf tools gets there.
