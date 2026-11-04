---
id: TASK-0091
title: Capture ingest refuses a handle without the gives role
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T03:18:00Z'
updated_date: '2026-11-04T04:17:00Z'
labels:
  - capture
  - security
milestone: m-5
dependencies:
  - TASK-0059
priority: medium
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0059: capture.check_answers checks that a handle is issued (task-0055) but never that it holds the gives role (ieam-register decision 0009), so a handle issued only to approve can give knowledge.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ingest refuses an answer whose handle lacks gives on the answer's date
- [x] #2 A test covers it; docs/security.md's permission matrix and gap list move with the fix
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.check_answers: a handle on the issued list without gives is refused, with a message naming the role (roles are per handle; the date rule is the existing issued/withdrawn check).
2. tests/test_capture.py::test_ingest_refuses_a_handle_without_gives: a handle with approves and closes only is refused; the same with gives answers; every handle the vendored register issues holds gives, so the CI capture steps (employee-1) stay valid.
3. docs/security.md: Gap 2 removed and the rest renumbered; the matrix row and its evidence row cite the test; instance/README.md's ingest paragraph names the rule.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proved locally on rdflib with the record's pins: harness.yml's capture step, extracted and run as written (KG_STORE=rdflib, KG_CLOCK=pinned), passes answering as employee-1; the same answers with employee-1's roles set to approves only in a copy of the example register: capture.py ingest exits 1, 'answered.from employee-1 lacks the role gives, which an answer needs (decision 0009)'. run_tests 285/285 plain and with KG_SUBJECT=subjects/jef_data_load. Every handle the vendored register issues holds gives, so the CI capture steps stay valid.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
capture.check_answers refused a handle the register had not issued, or had withdrawn by the answer's date, but not one issued without gives (ieam-register decision 0009); it now refuses that too, naming the role. tests/test_capture.py::test_ingest_refuses_a_handle_without_gives covers it (approves and closes only: refused; gives added: answers) and holds every vendored handle to gives. docs/security.md: the gives gap is gone, the matrix row and its evidence cite the test, the handle paragraph names the role; instance/README.md's ingest paragraph too. Roles carry no dates in the register, so 'on the answer's date' is the existing issued/withdrawn window.
<!-- SECTION:FINAL_SUMMARY:END -->
