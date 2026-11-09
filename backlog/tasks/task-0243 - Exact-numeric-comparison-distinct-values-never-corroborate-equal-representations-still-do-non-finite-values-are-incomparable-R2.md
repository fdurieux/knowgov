---
id: TASK-0243
title: >-
  Exact numeric comparison: distinct values never corroborate, equal
  representations still do, non-finite values are incomparable (R2)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - rules
  - correctness
dependencies: []
priority: high
ordinal: 237000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
R2 of the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). harness/rules.py compatible() compares numeric strings with float(a) == float(b), so 9007199254740992 and 9007199254740993, or 1e309 and 2e309, read equal: R-CORROBORATE promotes and R-CONFLICT stays silent. _is_num accepts inf and nan. The same function serves the rules, the review's dispute check, capture and load, and both adapters only supply candidate pairs, so one change covers both stores. Compare exactly (decimal.Decimal), keep 316.00 = 316, and read a non-finite value as incomparable (R-VAGUE's reading), with no tolerance added.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 compatible() compares numbers exactly: 316.00 and 316 equal; 9007199254740992 and 9007199254740993 conflict; 1e309 and 2e309 conflict; inf, nan and their spellings are incomparable; a test holds each case
- [ ] #2 The reviewer's probe cases are regression tests on R-CORROBORATE and R-CONFLICT through a store double, and a corroborating pair still promotes
- [ ] #3 The deterministic comparator on both subjects and the round trip on both stores pass with the record unchanged; CHANGELOG Unreleased › Changes names the fix
<!-- AC:END -->
