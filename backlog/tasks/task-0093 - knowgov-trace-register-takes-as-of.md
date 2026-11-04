---
id: TASK-0093
title: knowgov-trace register takes --as-of
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T07:29:00Z'
updated_date: '2026-11-04T08:01:00Z'
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
- [x] #1 register takes --as-of (and KG_AS_OF through the wrappers) and records the date it read in the ledger
- [x] #2 check_trace_walkthrough proves a registration as of a date after 2027-08-07; test_clock holds it
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. trace.py register --as-of (today|record|YYYY-MM-DD, today by default as check's): the gate read on it picks the statements; each ledger entry and registered row record as_of (with --assertion too); older ledgers still read.
2. trace-report schema: optional as_of on a registered row (additive, v1).
3. knowgov-gate.sh forwards KG_AS_OF to trace-register as well; action, GitLab include and instance README say so.
4. check_trace_walkthrough registers and checks as of 2027-09-01 into a second ledger; check_ci_wrappers proves the KG_AS_OF pass-through; test_trace and test_clock hold both.
5. Prove on rdflib and Neo4j 5.26; tests plain and under J-F.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proven locally: rdflib and Neo4j 5.26.0 community (Java 21): check_trace_walkthrough passes (registered and checked as of 2027-09-01: gate BLOCKED, 19 gate:lapsed findings; the first registration records the record's day 2026-10-30), check_ci_wrappers passes (trace-register records 2026-10-30 unset, 2027-08-08 with KG_AS_OF). tests/run_tests.py 287/287 plain and with KG_SUBJECT=subjects/jef_data_load. Before this, register read resolve(st, task), i.e. the record date (today where none), not today: either way not the caller's date.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov-trace register takes --as-of, as check does (task-0089): today by default, record or YYYY-MM-DD; the task's gate is read on it to pick the statements, so a rehearsal of a later date reads one clock. Each ledger entry records the date read as as_of (also with --assertion); register and check rows carry it, the text names it; older ledgers still read. trace-report schema: optional as_of on a registered row, additive, version 1 (CHANGELOG left to the release PR). knowgov-gate.sh forwards KG_AS_OF to trace-register too; the action, the GitLab include and instance/README.md say so. check_trace_walkthrough registers and checks as of 2027-09-01 (BLOCKED, gate:lapsed findings); check_ci_wrappers proves the pass-through; test_trace covers the field, test_clock holds the walkthrough's date after 2027-08-07 and the wrapper's pass-through. Proven on rdflib and Neo4j 5.26.0; tests 287/287 plain and under J-F. PR #162.
<!-- SECTION:FINAL_SUMMARY:END -->
