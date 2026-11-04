---
id: TASK-0085
title: The Turtle round trip carries the pre-load verdicts on each Version
status: To Do
assignee: []
created_date: '2026-11-04T01:31:00Z'
labels:
  - store
milestone: m-8
dependencies:
  - TASK-0064
  - TASK-0070
priority: medium
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the task-0064 session: export_turtle/import_turtle (task-0070) may not carry the preload_* properties task-0064 records on a Version, so a round-tripped store from an instance with a pre-load report could lose them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A store loaded with a pre-load report keeps every Version's preload verdict across both round-trip chains
- [ ] #2 tools/check_round_trip.py compares the gate's preload bundle and info findings across the hops
<!-- AC:END -->
