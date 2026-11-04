---
id: TASK-0075
title: >-
  Pin the clock of the review walkthrough and every check that reads today's
  date
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - capture
  - ci
milestone: m-5
dependencies: []
priority: high
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0068: tools/check_review_walkthrough.py reads the wall clock for capture approvals, so the six-month lapse (decision-0002) will move its outcome after 2027-05-03 and CI turns red with no code change, as the record would have before task-0068 pinned it. Any other check reading today's date has the same fault.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every CI check that reads the date reads a pinned one (KG_TODAY or the subject's record date), found by a search of harness/ and tools/
- [ ] #2 A test fails if a check reads the wall clock where a pinned date exists
- [ ] #3 The walkthrough passes unchanged with the date pinned, on rdflib and Neo4j
<!-- AC:END -->
