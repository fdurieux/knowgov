---
id: TASK-0076
title: The page shows the as-of date and the lapsed statements
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - page
  - gate
milestone: m-5
dependencies:
  - TASK-0068
priority: low
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0068 added gate_cli --as-of and the lapsed finding (decision-0005); the page shows neither, so a viewer cannot see when a review falls due or what lapsed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The gate panel names the as-of date it read
- [ ] #2 Lapsed verifications are listed with the date they lapsed and the kind's review months
- [ ] #3 The stack job asserts both on S1 as of a date after 2027-08-07
<!-- AC:END -->
