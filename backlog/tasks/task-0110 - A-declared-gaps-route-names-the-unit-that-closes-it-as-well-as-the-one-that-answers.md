---
id: TASK-0110
title: >-
  A declared gap's route names the unit that closes it as well as the one that
  answers
status: To Do
assignee: []
created_date: '2026-11-04T12:29:00Z'
labels:
  - gate
  - schema
milestone: m-8
dependencies:
  - TASK-0102
priority: low
type: task
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0102, chosen by the maintainer 2026-11-04. A declared gap's finding names in route the owner that answers (ORG-0002 for CargoQuote's OD-1); under decision-0002 the gap is closed by the unit its declaration names (compliance, ORG-0004; task-0054). The route names both: who answers and who closes. Additive, schema_version stays 2 (coordinator's practice: an optional field keeps the version).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 S2's OD-1 finding names ORG-0002 as answering and ORG-0004 as closing, from the declaration, not hard-coded
- [ ] #2 The schema validates reports with and without the new field; the record and the comparator are unchanged
- [ ] #3 The hook's summary and the page's gate box show the closing unit
<!-- AC:END -->
