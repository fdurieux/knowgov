---
id: TASK-0180
title: >-
  The record's round trip runs as its own parallel job, so each harness job fits
  the 12-minute budget (task-0163 AC #2 follow-up)
status: To Do
assignee: []
created_date: '2026-11-06T15:57:00Z'
labels:
  - ci
dependencies: []
priority: low
type: task
ordinal: 181000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0163 split harness.yml's rdflib job into rdflib (the record and its round trip) and rdflib-readers. The coordinator's quiet-slot measurement on 2026-11-06 (4 other runs active) gave rdflib-readers 10.1 min, under budget, but rdflib 17.2 min, over task-0084's 12-minute budget for a pull request: today's checks (SNAP-08, task-0172's schema tests) landed in it. The record is never subset (CLAUDE.md), so the lever is parallelism. Move the Turtle round trip (tools/check_round_trip.py, about 6.35 min) into a third job, rdflib-round-trip, with tests/test_rdflib_split.py extended so every step runs in exactly one of the three jobs. Adding the job to the ruleset's required checks is the maintainer's; until then it does not gate. Minted by the coordinator under doc-0029, not started.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 harness.yml runs rdflib, rdflib-readers and rdflib-round-trip in parallel; tests/test_rdflib_split.py holds that every step of the old single job runs in exactly one of them, and the subsets and the record are unchanged
- [ ] #2 A PR run in a slot with few other runs gives each of the three jobs under 12 minutes, recorded with the overlap count; if any is over, the figures are recorded and the AC stays open
- [ ] #3 CLAUDE.md names the three jobs; the maintainer is asked to add rdflib-round-trip (and rdflib-readers) to the ruleset
<!-- AC:END -->
