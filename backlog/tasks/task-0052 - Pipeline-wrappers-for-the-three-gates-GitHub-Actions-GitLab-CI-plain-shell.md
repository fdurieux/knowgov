---
id: TASK-0052
title: 'Pipeline wrappers for the three gates: GitHub Actions, GitLab CI, plain shell'
status: To Do
assignee: []
created_date: '2026-11-03T22:41:00Z'
labels:
  - ci
milestone: m-7
dependencies: []
priority: low
type: feature
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 11: thin per-platform wrappers that map platform variables to the core commands' flags (gate_cli.py now; the pre-load check and knowgov-trace when they exist), selected by the client. Run on the example instance.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A GitHub Actions composite action, a GitLab CI include template and a shell snippet, each calling the core with the same flags
- [ ] #2 Each is exercised on the example instance in CI where the platform allows (GitHub here; the others by a shell run of the same command line)
<!-- AC:END -->
