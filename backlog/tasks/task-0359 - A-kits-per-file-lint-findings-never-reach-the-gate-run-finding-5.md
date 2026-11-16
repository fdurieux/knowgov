---
id: TASK-0359
title: A kit's per-file lint findings never reach the gate (run finding 5)
status: To Do
assignee: []
created_date: '2026-11-16T04:37:00Z'
labels:
  - finding
  - reverse-engineering
  - decision
dependencies: []
type: task
ordinal: 349000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-11-16 by the first private reverse-engineering runs (decision-0018's process on a private demonstration case, task-0220): kits written to subjects/README.md by a clean-room extraction session, then loaded by the instance tooling. The maintainer, 2026-11-16: "mint tasks for the five knowgov findings".

A kit is a directory artefact. preload.py records a directory artefact as unchecked by design (task-0312 R1: a directory is never one file a linter judged), so the per-file findings that preload_check.py and pumllint produce on a kit's diagrams and prose do not become lint gaps the gate names, while the same findings on a single-file artefact do. In both runs the kits carried real findings (pumllint critical and minor, markdownlint major) that the gate could not see.

This is a design question before any build: a decision with the four parts precedes it. Placement: 1.1.0 at the earliest (it changes what the gate reports).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts (canvas, fit/gap, SWOT, advice) precedes any build
- [ ] #2 If built: a directory artefact's per-file verdicts reach the gate as lint gaps on the files they judged, the directory still unchecked as a whole
- [ ] #3 The scored record is unchanged, or its change approved by the maintainer
<!-- AC:END -->
