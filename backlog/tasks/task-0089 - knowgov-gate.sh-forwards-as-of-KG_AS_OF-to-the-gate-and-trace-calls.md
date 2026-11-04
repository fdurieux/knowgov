---
id: TASK-0089
title: knowgov-gate.sh forwards --as-of (KG_AS_OF) to the gate and trace calls
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T03:06:00Z'
updated_date: '2026-11-04T03:59:00Z'
labels:
  - ci
milestone: m-7
dependencies:
  - TASK-0068
  - TASK-0052
priority: low
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by the task-0075 session: an instance pipeline can only read the gate as of today, because knowgov-gate.sh does not forward gate_cli's --as-of (decision-0005, task-0068). A pipeline checking a release as of its cut date, or rehearsing a future lapse, needs it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 KG_AS_OF, when set, reaches gate_cli and knowgov-trace check as --as-of in the shell script, the GitHub action input and the GitLab include
- [ ] #2 tools/check_ci_wrappers.py proves it on S1 as of a date after 2027-08-07
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. trace.py check takes --as-of (cadence.as_of, CannotRun on a bad date), passes it to gate.resolve; its report's gate names as_of (optional in trace-report.schema.json).
2. knowgov-gate.sh: KG_AS_OF -> --as-of on gate and trace-check; action.yml input as-of -> KG_AS_OF; GitLab include variable KG_AS_OF (empty: today).
3. tools/check_ci_wrappers.py: S1 as of the record day exit 0; KG_AS_OF=2027-08-08 exit 1 BLOCKED with lapsed findings; trace-check with KG_AS_OF reads its gate as of that day with gate:lapsed findings.
4. harness.yml: the action run for real with as-of on S1, asserted BLOCKED with lapses.
5. instance/README.md, docs/guide.md name KG_AS_OF.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Local proof (rdflib, pinned venv): check_ci_wrappers passes: S1 as of 2026-10-30 PROCEED exit 0; KG_AS_OF=2027-08-08 BLOCKED, 19 lapsed findings, exit 1; trace-check KG_AS_OF=2027-08-08 gate BLOCKED as of 2027-08-08, 19 gate:lapsed; unset it reads the pinned KG_TODAY. check_trace_walkthrough passes. run_tests 282/282 plain, with KG_SUBJECT=subjects/jef_data_load, and in the pinned venv. trace-register keeps today: its statement selection is the gate's served set, outside the brief.
<!-- SECTION:NOTES:END -->
