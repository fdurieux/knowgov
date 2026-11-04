---
id: TASK-0093
title: knowgov-trace register takes --as-of
status: To Do
assignee: []
created_date: '2026-11-04T07:29:00Z'
labels:
  - trace
milestone: m-7
dependencies:
  - TASK-0089
priority: low
ordinal: 96000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0089: knowgov-trace register still reads today when it picks the statements the gate serves; check takes --as-of (task-0089) but register does not, so a registration made while rehearsing a future date mixes two clocks.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register takes --as-of (and KG_AS_OF through the wrappers) and records the date it read in the ledger
- [ ] #2 check_trace_walkthrough proves a registration as of a date after 2027-08-07; test_clock holds it
<!-- AC:END -->
