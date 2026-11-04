---
id: TASK-0084
title: >-
  Keep the CI jobs short: a J-F scenario subset where the round trip and the
  rehearsal run
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - ci
milestone: m-6
dependencies: []
priority: low
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Turtle round trip (task-0070) added about 7 minutes to stack and the lighthouse rehearsal (task-0069) about 7 to rdflib, most of it J-F. Every PR waits on these jobs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 stack and rdflib each run under a stated budget with J-F on a named subset, the full set kept in a scheduled or release run
- [ ] #2 The subset and the full run are both named in harness.yml/demo.yml and in CLAUDE.md
<!-- AC:END -->
