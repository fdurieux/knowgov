---
id: TASK-0103
title: The pilot adds a gate-unavailable case and the block measures
status: To Do
assignee: []
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-08T23:53:00Z'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08 (coordinator): decision-0029, proposed for the maintainer, would bring AC #3 into 0.9.0 (after the cut it is a 0.10.0: gate-report.schema.json is additionalProperties false); task-0237 prepares the build and its PR waits for the maintainer's word. AC #1 and #2 stay at m-8 with the pilot. The v1.0 scope handover's GAP-04 (the composed delivery recipe) would extend AC #1 if decision-0031 (proposed) is accepted.
<!-- SECTION:NOTES:END -->
