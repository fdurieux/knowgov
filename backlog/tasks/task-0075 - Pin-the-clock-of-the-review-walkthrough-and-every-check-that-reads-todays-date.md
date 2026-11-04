---
id: TASK-0075
title: >-
  Pin the clock of the review walkthrough and every check that reads today's
  date
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:16:00Z'
labels:
  - capture
  - ci
milestone: m-5
dependencies: []
priority: high
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0068: tools/check_review_walkthrough.py reads the wall clock for capture approvals, so the six-month lapse (decision-0002) will move its outcome after 2027-05-03 and CI turns red with no code change, as the record would have before task-0068 pinned it. Any other check reading today's date has the same fault.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every CI check that reads the date reads a pinned one (KG_TODAY or the subject's record date), found by a search of harness/ and tools/
- [ ] #2 A test fails if a check reads the wall clock where a pinned date exists
- [ ] #3 The walkthrough passes unchanged with the date pinned, on rdflib and Neo4j
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/review.py today() stays the one clock (KG_TODAY, else wall); KG_CLOCK=pinned makes it raise WallClock instead of reading the wall clock; review.pinned(env, day) and cadence.pin_record(env) build a check's environment.
2. Every date read in harness/, tools/, demo/: capture.py questionnaire -> review.today(); load.now() honours KG_TODAY; the rest are named stamps.
3. Pin each check tool: the review walkthrough to its reviews' day (ON 2026-11-03, the lapse derived from it), the transcript route to its day, the others (trace, capture pairing, MCP, round trip, gate after change, CI wrappers) to the subject's record date; minimal gets a [record] as_of.
4. KG_CLOCK=pinned in the test runner and the rdflib job; the capture step and the composite action's steps get KG_TODAY; gate_cli in workflows always with --as-of.
5. tests/test_clock.py: the named reads, the refusal, every check tool pinned, every workflow gate command dated.
6. Prove: walkthrough on rdflib and Neo4j 5.26; a faked wall clock past 2027-05-03 reddens main's walkthrough and not this branch's.
<!-- SECTION:PLAN:END -->
