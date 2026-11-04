---
id: TASK-0075
title: >-
  Pin the clock of the review walkthrough and every check that reads today's
  date
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:48:00Z'
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
- [x] #1 Every CI check that reads the date reads a pinned one (KG_TODAY or the subject's record date), found by a search of harness/ and tools/
- [x] #2 A test fails if a check reads the wall clock where a pinned date exists
- [x] #3 The walkthrough passes unchanged with the date pinned, on rdflib and Neo4j
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Found and pinned beyond the walkthrough: capture.py questionnaire read dt.date.today() directly; check_mcp_server's stage 2 and the MCP default read today; the transcript route (#122), the CI wrappers (#123, including the composite action's steps) and the pre-load verdict step (#118) read today, each caught by tests/test_clock.py as it merged. The datetime monkeypatch used to fake a wall clock segfaults inside the Neo4j driver, so on Neo4j the proof is KG_CLOCK=pinned (any unpinned read raises) rather than a faked date.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
today() in harness/review.py stays the one clock (KG_TODAY, else the wall clock). Under KG_CLOCK=pinned it raises WallClock instead of reading the wall clock. review.pinned and cadence.pin_record build a check's environment. The review walkthrough runs on its reviews' day (2026-11-03), with the lapse day derived from it. The other check tools run on the record date, or on the transcript route's own day. The test runner and the rdflib job set KG_CLOCK=pinned, and every workflow gate command names --as-of. tests/test_clock.py holds it: every other wall-clock read is named, the refusal is checked, every check tool must pin and every gate command must carry a date. Proof: a wall clock faked to 2027-06-01 turns main's walkthrough red (QUALIFIED where PROCEED is wanted) but not this branch's. 224/224 tests, plain and on J-F. The rdflib job was replayed in full and the Neo4j 5.26 checks all pass under KG_CLOCK=pinned. PR #128 merged on a green matrix.
<!-- SECTION:FINAL_SUMMARY:END -->
