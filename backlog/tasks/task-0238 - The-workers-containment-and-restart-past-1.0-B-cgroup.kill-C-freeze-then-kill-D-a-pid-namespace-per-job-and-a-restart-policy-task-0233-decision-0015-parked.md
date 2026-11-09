---
id: TASK-0238
title: >-
  The worker's containment and restart past 1.0: (B) cgroup.kill, (C) freeze
  then kill, (D) a pid namespace per job, and a restart policy (task-0233,
  decision-0015; parked)
status: To Do
assignee: []
created_date: '2026-11-08T23:46:00Z'
updated_date: '2026-11-08T23:53:00Z'
labels:
  - worker
  - containment
milestone: m-4
dependencies:
  - TASK-0233
priority: low
ordinal: 233000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0233 fixed the reaper's race (A, #389) and, on the maintainer's word (2026-11-08: "(A') yes"), made the worker exit with code 4 past REAP_S: recovery is a manual restart, listed as K22 in doc-0028 §10 and tasked here. (B) cgroup.kill, (C) freeze then kill and (D) a pid namespace per job each change decision-0012/0015's container settings; an automatic restart is a container setting too (decision-0015). Parked until the lighthouse shows the rate of a reap past the bound (once in 260 hostile jobs under load before the fix); each option needs a decision with the four parts first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts chooses among (B), (C), (D) and none, and on an automatic restart, citing the pilot's observed rate
- [ ] #2 If one is chosen, EXEC-14 or its successor proves it in the stack job, and K22 is closed or restated
<!-- AC:END -->
