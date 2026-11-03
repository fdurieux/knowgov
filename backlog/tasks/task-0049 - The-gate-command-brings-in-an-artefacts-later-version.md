---
id: TASK-0049
title: The gate command brings in an artefact's later version
status: To Do
assignee: []
created_date: '2026-11-03T22:40:00Z'
labels:
  - gate
milestone: m-7
dependencies:
  - TASK-0048
priority: medium
type: feature
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 5: gate_cli.py loads stage 1 only, so it never sees a changed document (S6's stage 2). Add an option that loads a scenario's later version (or a named changed artefact) the way run.py's stage2 does, so the command reports invalidations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 gate_cli.py --stage 2 (or an equivalent option) reproduces run.py's stage 2 for S6: four invalidated statements, BLOCKED before re-verification
- [ ] #2 The JSON report names the version loaded
- [ ] #3 harness.yml runs it on S6
<!-- AC:END -->
