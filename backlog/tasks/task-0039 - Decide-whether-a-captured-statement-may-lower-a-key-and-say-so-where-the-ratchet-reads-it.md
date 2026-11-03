---
id: TASK-0039
title: >-
  Decide whether a captured statement may lower a key, and say so where the
  ratchet reads it
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T23:46:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: low
type: task
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 F4: a key's level is the lowest of its live statements, so John's correct but unreviewed answer on response|statuses lowered the key from validated to proposed in S2, and `gate_cli.py --baseline record` then exits 1 (REGRESSION). A pipeline that ratchets on the record after a capture fails and is likely switched off. Either the behaviour is right and documented, or an elicited statement beside validated document statements is not counted in the level until reviewed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The choice is recorded as a decision in backlog/decisions, with the S2 case as its example
- [x] #2 gate.resolve and its tests follow the decision; the comparator stays green
- [x] #3 instance/README.md and the gate_cli docstring say what a capture does to a ratchet against the record
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. decision-0004 drafted and merged by the maintainer (#100): option B.
2. gate.resolve: an elicited statement at proposed is left out of the min when the key holds a validated, verified or approved live statement; kept in assertions, listed in pending_review, marked in render_key.
3. Tests (stand-in store through the rules): agreeing capture keeps statuses validated; contradicting one disputed; alone it sets proposed; approved counts.
4. instance/README and gate_cli docstring.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
decision-0004 drafted (proposed): options A (min rule, documented) and B (an unreviewed elicited statement does not lower a key holding a validated-or-better statement); recommends B. S2 case run by command: a capture agreeing on response|statuses gives REGRESSION validated -> proposed, exit 1. Implementation waits for the maintainer's merge.

On rdflib: S2 with an agreeing capture on response|statuses, --baseline record: no regression, exit 0 (was exit 1). check_review_walkthrough, check_capture_pairing, check_gate_after_change pass; comparator 0 differing leaves over 7 scenarios (run.py's gate_keys records level, flags, n only). Contract change for 0.2.0, left to the release PR.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Under decision-0004 (option B, merged by the maintainer in #100), gate.resolve leaves an unreviewed elicited statement out of a key's level when the key holds a validated-or-better statement. The statement stays in the key's assertions, is listed in pending_review and is marked PENDING REVIEW in the bundle. A contradicting capture still makes the key disputed through R-CONFLICT. A capture alone on a key still sets it to proposed. S2's agreeing capture no longer trips --baseline record. The README and the gate_cli docstring explain this. Tests and the comparator are green. This is a contract change for the 0.2.0 release PR.
<!-- SECTION:FINAL_SUMMARY:END -->
