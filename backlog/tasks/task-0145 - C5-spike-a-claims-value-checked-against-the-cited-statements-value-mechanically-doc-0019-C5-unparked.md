---
id: TASK-0145
title: >-
  C5 spike: a claim's value checked against the cited statement's value,
  mechanically (doc-0019 C5, unparked)
status: To Do
assignee: []
created_date: '2026-11-05T21:11:00Z'
labels: []
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0019 -
    GraphRAG-read-against-knowgov-the-paper-verified-against-its-tables-fit-gap-opportunity-canvas-SWOT-candidates.md
priority: low
type: spike
ordinal: 151000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
M5 counts a reply's refs that resolve, not whether the value the reply uses matches the cited statement. task-0140 measured the blind spot (doc-0019 §7): on S3 the compact bundle lost the planted accept_boundary_41 in 3 of 5 runs while every failing run cited the right boundary keys, so M5 stayed 1.0 with the wrong value in the code. Claims and assumptions are prose with a ref (A:dt:S-accept|max@v1); the value may sit in the text, in the generated code, or nowhere, so what counts as "the claim's value" is part of the spike. Unparked by the maintainer on 2026-11-05.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Before any measurement, the hypothesis and the bar are recorded in this task through the CLI: recall, every governed run whose M4 fails a planted value target while citing that target's key is flagged; precision, no flag on any of the record's 35 governed replies (S1-S7, five runs) whose M4 targets pass; a claim that states no value is counted unvalued, never matched
- [ ] #2 The check reads replies, generated code and the store's statements as a measurement outside the record: no field added to the record's run files, the comparator and the deterministic results unchanged, value normalisation (numbers, units, booleans, enumerations) documented
- [ ] #3 Measured on the record's governed replies and on a compact-form S3 re-run labelled a deviation (n = 5, effort as task-0140, raw outputs outside the repository), with the per-run table
- [ ] #4 A dated doc-0019 entry gives the outcome against the bar and the decision: fold it into the measures (and where: M5, a new measure, or trace's check on hand-written code), or park it with the reason
<!-- AC:END -->
