---
id: TASK-0103
title: The pilot adds a gate-unavailable case and the block measures
status: To Do
assignee: []
created_date: '2026-11-04T09:47:00Z'
labels:
  - lighthouse
  - gate
milestone: m-8
dependencies:
  - TASK-0099
priority: medium
type: task
ordinal: 106000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C6, C9). docs/lighthouse-evaluation.md gains a rehearsed scenario where the store is unreachable and the hook stops the transition. The pilot checklist gains missed blocks, owner-resolution time and wait per gate; task-0057's pre-registration points at them. The gate report gains the task-profile digest and the register tag, so a retained report is the stage's decision record (no new folders).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The rehearsal shows exit 2 stopping the hook on both subjects
- [ ] #2 The checklist lists correct, missed and false blocks and owner time, each with its source
- [ ] #3 The report carries the two digests and the round trip holds them
<!-- AC:END -->
