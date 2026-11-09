---
id: TASK-0244
title: >-
  The gate's evidence-basis flags are deterministic: every inference basis
  named, in order, whatever the hash seed (R3)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
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
- [ ] #1 A key whose statements are all inference bases carries every basis among them in its flags, sorted; a single-basis key reads as today
- [ ] #2 A test runs the reviewer's mixed-basis case in subprocesses under at least three PYTHONHASHSEED values and holds the flags equal
- [ ] #3 The deterministic comparator on both subjects passes with the record unchanged; CHANGELOG Unreleased › Changes names the fix
<!-- AC:END -->
