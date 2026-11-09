---
id: TASK-0243
title: >-
  Exact numeric comparison: distinct values never corroborate, equal
  representations still do, non-finite values are incomparable (R2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T07:59:00Z'
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
- [x] #1 compatible() compares numbers exactly: 316.00 and 316 equal; 9007199254740992 and 9007199254740993 conflict; 1e309 and 2e309 conflict; inf, nan and their spellings are incomparable; a test holds each case
- [x] #2 The reviewer's probe cases are regression tests on R-CORROBORATE and R-CONFLICT through a store double, and a corroborating pair still promotes
- [x] #3 The deterministic comparator on both subjects and the round trip on both stores pass with the record unchanged; CHANGELOG Unreleased › Changes names the fix
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (branch over 6dcfe92): tests/test_exact_numeric.py, 7 tests, all pass; 4 fail on the old code (the 2**53 pair, the 1e309 pair, the non-finite spellings, the probes through the rules). Comparator 0 diffs on CargoQuote S1-S7 and J-F (6) on rdflib and on Neo4j 5.26. check_round_trip --chain rdflib,rdflib and neo4j,rdflib,neo4j hold on both subjects. check_conflict_ids --stores neo4j,rdflib holds. Suites: bare 849/905, J-F bare 849/905, pinned 903/905, pinned J-F 901/905, 0 failed. A non-finite value is incomparable even beside the same spelling (nan is not nan; inf is no measure).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
rules.compatible now compares numeric values exactly with decimal.Decimal, no tolerance: 316.00 equals 316, 9007199254740992 and 9007199254740993 conflict, 1e309 and 2e309 conflict. A non-finite value (inf, nan, their spellings) is incomparable, R-VAGUE's reading, and _is_num refuses it. One function serves the rules, review.py's dispute check, capture.py and load.py, so both stores are fixed. The reviewer's probes are regression tests on R-CORROBORATE and R-CONFLICT through a store double, beside a corroboration that still promotes. The record does not move: the comparator shows 0 diffs on both subjects and both stores. CHANGELOG has its line under Unreleased, Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
