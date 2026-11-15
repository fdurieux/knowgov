---
id: TASK-0353
title: >-
  Agent tool results clipped at RESULT_LIMIT, not each tool's own limit
  (decision-0045 Q10 i)
status: To Do
assignee: []
created_date: '2026-11-15T20:10:00Z'
updated_date: '2026-11-15T20:17:00Z'
labels: []
dependencies: []
ordinal: 341000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each tool result is clipped at its own limit: read_document and the readers at READ_LIMIT, run_suite at RESULT_LIMIT; the JSON wrapper does not cut a read below READ_LIMIT
- [x] #2 The trace records what was delivered: delivered length and whether clipped, additive, no pinned schema changed
- [x] #3 Regressions written first and shown failing: long document delivered to READ_LIMIT, long suite result clipped at RESULT_LIMIT, trace matches delivery
- [x] #4 Deterministic comparator on rdflib shows 0 differing leaves and KG_CLOCK=pinned python tests/run_tests.py passes
- [x] #5 CHANGELOG Unreleased line states reads reach the model at READ_LIMIT, future arms runs can differ, the record is unchanged
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fix in harness/agent.py (_deliver, ENVELOPE_LIMIT); trace tool rows gain delivered/clipped (no pinned schema). Regressions failed before the fix (read cut at 6000, no delivered field). Comparator rdflib: 7 scenarios, 0 differ. Suite: only demo-view tests that fail on main in this sandbox (TypeError, no stack) remain.
<!-- SECTION:NOTES:END -->
