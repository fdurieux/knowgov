---
id: TASK-0302
title: >-
  A review's approval binds to its own giver's answer only; a capture's sha256
  is documented (FR-12)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T21:25:00Z'
updated_date: '2026-11-09T22:04:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/docs/doc-0037
  - backlog/decisions/decision-0019
priority: high
ordinal: 295000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the functional review of the 0.9.0 release candidate, group C at main f194aac (C2-1), recorded in doc-0037 §3.2. Fix-only, behind an unchanged contract. It breaks FR-12's binding claim, so the coordinator pulls it before the 0.9.0 cut.

`harness/review.py` `bind()`: when the named assertion id is gone, exactly one statement with the same key, value and sha256 wins ("repaired"). For a captured answer, sha256 is the empty-text digest e3b0c442…, so binding is by key and value only.

Repro:
1. employee-1 answers response|hold_presence; employee-2 approves A:cap:2026-11-05-ORG-0002-employee-1:1@capture.
2. Delete that capture file.
3. employee-3 ingests the same value.
4. The gate reads the key approved, with no act finding.

The self-review rule still holds: the reviewer as the new giver is refused.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A repair re-binds only to a statement from the same capture giver (the same capture stem); any other candidate leaves the approval unbound, with a finding that names the vanished id.
- [x] #2 The repro is a test, and so is the reverse (the same giver's re-ingested answer still repairs).
- [x] #3 The docs state that a captured answer's sha256 is the digest of empty text, and that binding is by giver, key and value.
- [x] #4 The record does not move; a CHANGELOG line under the leading Unreleased.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. review.bind: a captured answer repaired only by the same giver's answer (_holding, _same_giver, _giver from the capture stem, the candidate's agent). 2. Else the ruling reads gone, the existing major act naming the vanished id. 3. Unit tests and the end-to-end repro and reverse in check_act_binding. 4. Docstring, CHANGELOG, comparators.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #1 reads 'the same capture giver (the same capture stem)'. A re-ingested answer is captured under a new stem (its date and file name differ), so AC #2's reverse case cannot hold by stem; the giver is the stem's handle, read whole from the vanished id's stem ({on}-{owner}-{handle}) and compared with the candidate's agent. A stem a second same-day capture renamed (-2) names no giver whole and repairs nothing.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
review.bind repaired a vanished ruling onto the one statement holding its key, value and digest; a captured answer has no fragments, so its digest is the empty text's and another person's identical answer inherited the approval (C2-1). A captured answer is now repaired only by the same giver's answer: _giver reads the handle whole from the id's capture stem (ASCII digits), and the candidate's agent must equal it; a -2 renamed stem repairs nothing. Any other candidate leaves the ruling gone, the existing major act finding naming the vanished id: no new why, the gate report's contract unchanged. Every other statement repairs by content as before. The review module's docstring records the empty-text sha256 and the binding by giver, key and value. Tests: two in test_act_binding.py, both failing on main; tools/check_act_binding.py giver_cases runs the repro (employee-3's identical answer: approved on nothing, a major gone act naming A:cap:2026-11-02-ORG-0002-employee-1:3@capture) and its reverse (employee-1's re-ingested answer approved, no act), on rdflib in CI and Neo4j in the stack job. The record held: comparator identical on CargoQuote S1-S7 and J-F's six scenarios. Complexity within the ratchet. CHANGELOG under Unreleased > Changes. run_tests: bare 1001/1063 (62 skipped), pins 1061/1063 (2 skipped), 0 failed.
<!-- SECTION:FINAL_SUMMARY:END -->
