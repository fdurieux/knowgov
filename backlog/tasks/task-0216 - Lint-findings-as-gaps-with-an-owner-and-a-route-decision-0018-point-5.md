---
id: TASK-0216
title: Lint findings as gaps with an owner and a route (decision-0018 point 5)
status: To Do
assignee: []
created_date: '2026-11-08T11:17:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - preload
  - gate
dependencies:
  - TASK-0201
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: high
type: feature
ordinal: 216000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 5 (doc-0032 §2 step 5; Dominique's attribute and route steps). Today the pre-load verdict reaches the gate at info only (task-0064), as form, and nobody is asked to resolve a finding. Each finding of tools/preload_check.py on a loaded document becomes a gap with an owner and a route from capture.routing (task-0201 G8): the document's owning unit, its questionnaire. A resolution (slip, choice, exception, open) is recorded through the existing routes: a slip is a new document version, a choice a decision record and an approval, an exception an elicited statement, an open item a gap with its owner. The info listing of task-0064 stays. A lint gap sits on its document; whether it lowers a key's level is the build's to show and state. A contract change (the gate report; a resolution record), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each pre-load finding on a loaded document is a gap in the store and a gate finding naming the document's owner and route; the baseline (--baseline) holds a finding without raising it
- [ ] #2 A finding's resolution (slip, choice, exception, open) is recorded and a re-lint at the same tool versions shows the delta
- [ ] #3 Whether a lint gap lowers a key's level is stated in the PR, and the record's verdicts are unchanged
- [ ] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
