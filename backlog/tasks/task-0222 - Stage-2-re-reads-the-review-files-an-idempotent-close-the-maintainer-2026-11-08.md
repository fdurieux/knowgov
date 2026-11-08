---
id: TASK-0222
title: >-
  Stage 2 re-reads the review files: an idempotent close (the maintainer,
  2026-11-08)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T11:50:00Z'
labels:
  - stage2
  - reviews
dependencies:
  - TASK-0199
references:
  - >-
    backlog/tasks/task-0197 -
    Stage-2-as-a-whole-re-load-rules-across-versions-reviews-re-applied-gaps-kept-closed-doc-0030-F3-H2-H4-I5-I6-G5.md
priority: medium
type: bug
ordinal: 222000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08 (Build it, as suggested): task-0197 (F3) made stage 2 re-read the whole later kit as a fresh load would, with one accepted deviation: reviews are not re-read at stage 2, since re-applying a close of an already-closed gap was not harmless. Since task-0198 (F4) the loader reads no clock, and since task-0199 (F2) every act binds by content, so the close becomes idempotent in review.check (closing an already-closed gap with the same digest is a no-op) and stage 2 re-reads the review files, so a person's answer written for the later version counts in the same run. A fix, not a contract change. If the record moves, it comes back to the maintainer before the merge.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Closing an already-closed gap whose declaration digest matches is a no-op; one whose text changed is not applied and is an act finding (task-0199)
- [ ] #2 Stage 2 re-reads every review file, and a review written for the later version applies in the same run, on both stores
- [ ] #3 tools/check_stage2_reload.py gains the case and fails it on the old code
- [ ] #4 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
review.check: a close of a gap already closed on the same digest is a no-op (gap_brief, a new port read); one closed on another declaration is set aside, changed. load_reviews(again=True) at stage 2: clear_act_findings (a new port write), then every review file read again, closes included, the review's activity kept when stage 1 recorded it. check_stage2_reload: R1 (a ruling written for v2 applies at stage 2, no act left from stage 1), R2 (an idempotent close through S2's own stage 2), R3 (a close of a restated declaration, changed at both stages).
<!-- SECTION:PLAN:END -->
