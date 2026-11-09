---
id: TASK-0251
title: >-
  A complexity ratchet in the test suite: new functions stay under the
  threshold, today's hotspots may only shrink (doc-0033)
status: To Do
assignee: []
created_date: '2026-11-09T07:10:00Z'
labels:
  - quality
  - tests
  - tooling
dependencies: []
priority: medium
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-09: "yes, mint and dispatch both", on the coordinator's advice (doc-0033, Answered): the everyday control that keeps debt from growing between the per-release scans. A standard-library test (tests/test_complexity.py, with a small tools/complexity.py to measure and regenerate) computes each function's cognitive complexity by AST, following Sonar's published rules closely enough that the numbers read alike (documented). It covers harness, demo/app, tools (fixtures excluded) and instance/ci. A function not in the baseline must be at or under the threshold, 15 as in Sonar's default. A function in the baseline (today's hotspots, about 185 at Sonar's count) may not exceed its recorded value; a lower value lowers the baseline in the same pull request; a raised value is accepted only with a stated reason in the baseline entry, reviewed in the PR, so an urgent fix is never blocked. It runs in seconds in the tests job, with no dependency and no server. Not a cut condition.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 tests/test_complexity.py fails a new function over the threshold and a baseline function above its recorded value, and passes on main as committed
- [ ] #2 tools/complexity.py measures and regenerates the baseline; a raised entry needs a reason field, and the test reports stale entries (a function gone or lowered) so the baseline tightens
- [ ] #3 The measure is documented beside Sonar's (what it counts, where it differs), and the suite stays standard-library only and within the tests job's budget
<!-- AC:END -->
