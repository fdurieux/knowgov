---
id: TASK-0244
title: >-
  The gate's evidence-basis flags are deterministic: every inference basis
  named, in order, whatever the hash seed (R3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T07:58:00Z'
labels:
  - gate
  - determinism
dependencies: []
priority: medium
ordinal: 238000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
R3 of the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). harness/gate.py resolve_spec adds next(iter({r["basis"] for r in rows})) to a key's flags when every statement is inferred, assumed or hypothesised, so a key with mixed bases reports one chosen by PYTHONHASHSEED. The verdict is unaffected; the report is not reproducible. Every such basis is added, sorted (flags is already a sorted array of strings in the schema).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A key whose statements are all inference bases carries every basis among them in its flags, sorted; a single-basis key reads as today
- [x] #2 A test runs the reviewer's mixed-basis case in subprocesses under at least three PYTHONHASHSEED values and holds the flags equal
- [x] #3 The deterministic comparator on both subjects passes with the record unchanged; CHANGELOG Unreleased › Changes names the fix
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate.inference_flags(rows): every inference basis when all rows are inference-based; resolve_spec uses it.
2. tests/test_inference_flags.py: subprocesses under five PYTHONHASHSEED values.
3. CHANGELOG line; comparator on both subjects.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-09 evidence.
- AC1: harness/gate.py inference_flags(rows) returns {basis for each row} when every row is inferred, assumed or hypothesised, else the empty set. resolve_spec ORs it into a key's flags, which stay sorted. A single-basis key gives that one flag, as before. A key with any other basis gets none (tested).
- AC2: tests/test_inference_flags.py runs the reviewer's mixed case (inferred, assumed, hypothesised, assumed) in subprocesses under PYTHONHASHSEED 0, 1, 2, 3 and 12345; all five print ["assumed", "hypothesised", "inferred"]. The test asserts next(iter({r["basis"]...})) is gone from gate.py, so it fails on the old code.
- AC3: comparator CQ 0 differences over 7 scenarios and J-F 0 over 6, so the record does not move. CHANGELOG Unreleased > Changes; 0.8.0 byte-identical.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A key resting only on inference carries every basis among its statements in its flags, sorted, through gate.inference_flags (doc-0033 R3), no longer the one a set's iteration order picked. Flags are now equal under any PYTHONHASHSEED, proven in subprocesses under five seeds. The verdict never depended on it, and the record is unchanged on both subjects.
<!-- SECTION:FINAL_SUMMARY:END -->
