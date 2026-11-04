---
id: TASK-0113
title: The owner's questionnaire names the closing unit beside a declared-gap item
status: To Do
assignee: []
created_date: '2026-11-04T14:55:00Z'
labels:
  - gate
  - capture
milestone: m-8
dependencies:
  - TASK-0110
priority: low
type: task
ordinal: 113000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0110; chosen by the maintainer 2026-11-04. harness/capture.py's questionnaire lists a declared gap for the answering owner; it should also name the unit that closes it (the closer, from the declaration), so the owner knows who must close it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 S2's questionnaire for ORG-0002 names ORG-0004 as closing OD-1
- [ ] #2 Ingest is unchanged; a questionnaire from before still ingests
<!-- AC:END -->
