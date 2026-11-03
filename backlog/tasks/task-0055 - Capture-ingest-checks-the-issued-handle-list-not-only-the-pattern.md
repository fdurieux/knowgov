---
id: TASK-0055
title: Capture ingest checks the issued-handle list, not only the pattern
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:50:00Z'
updated_date: '2026-11-03T23:31:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0037
priority: medium
type: bug
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0037 (#82): harness/capture.py ingest checks answered.from against the handle pattern only; decision 0009 (register v0.2.4) lists issued handles in people/handles.toml and its checker refuses an unissued handle. Ingest should refuse the same: a handle not issued, issued after the answer's date, or withdrawn by then. The capture CI step currently answers as steward-1, which is not issued.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ingest refuses an unissued, not-yet-issued or withdrawn handle, naming the rule, when the register lists issued handles; the pattern alone applies when it lists none
- [x] #2 The CI capture step and the docs use an issued handle (employee-1)
- [x] #3 Tests cover each refusal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. check_answers takes the register's issued list (review.issued_handles) and refuses an unissued, not-yet-issued or withdrawn handle; pattern alone when the list is absent or empty.
2. _ingest passes it.
3. CI capture step and instance/README answer as employee-1.
4. Tests per refusal.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ran the CI capture step locally (rdflib, example instance): steward-1 refused 'not an issued handle (decision 0009)', exit 1; employee-1 captured, exit 0. A name is refused once, by the pattern, not again by the list.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
capture.py check_answers gains handles= (the issued list review.py already reads); ingest refuses a handle not issued, issued after answered.on, or withdrawn on or before it, each naming decision 0009. No list, or an empty one: the pattern alone. CI capture step, instance/README and tests answer as employee-1. tests/test_capture.py covers each refusal, the late withdrawal that stands, and the no-list case.
<!-- SECTION:FINAL_SUMMARY:END -->
