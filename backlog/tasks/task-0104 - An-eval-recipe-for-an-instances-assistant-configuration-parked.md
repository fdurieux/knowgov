---
id: TASK-0104
title: An eval recipe for an instance's assistant configuration (parked)
status: To Do
assignee: []
created_date: '2026-11-04T09:47:00Z'
labels:
  - ci
  - lighthouse
milestone: m-8
dependencies: []
priority: low
type: feature
ordinal: 107000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C8); parked until a pilot asks. An instance template workflow runs on a change to CLAUDE.md, .claude/** or the arms' model row, reruns a fixed set of the instance's governed tasks, and fails when verdict obedience or the oracle score is worse than the recorded baseline (playbook pp. 34-35).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The recipe runs on the example instance with the public subjects as cases
- [ ] #2 A baseline is recorded only by a deliberate act, never by the workflow
<!-- AC:END -->
