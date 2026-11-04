---
id: TASK-0089
title: knowgov-gate.sh forwards --as-of (KG_AS_OF) to the gate and trace calls
status: To Do
assignee: []
created_date: '2026-11-04T03:06:00Z'
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
