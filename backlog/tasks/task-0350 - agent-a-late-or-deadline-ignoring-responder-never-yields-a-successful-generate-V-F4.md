---
id: TASK-0350
title: >-
  agent: a late or deadline-ignoring responder never yields a successful
  generate (V-F4)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-15T19:51:00Z'
updated_date: '2026-11-15T19:51:00Z'
labels:
  - review
  - runs
  - agent
dependencies: []
priority: high
type: bug
ordinal: 341000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The external validation of 0.9.1 (538618f), V-F4: `agent.run` called a responder without a `deadline` parameter synchronously, for compatibility, and trusted a responder that takes one to honour it; nothing bounded the call and an answer returned after the deadline was accepted as a successful final answer. Reproduced: a callback without `deadline` sleeps 0.35 s and returns a generated answer under a 0.05 s budget; the run returns `finished: true`, `decision: generate`, `stopped_by: null` after about 0.58 s. The default streamed responder ends its own work at the deadline (`bounded`, task-0141.05); the injected-callback path did not. The maintainer approved fixing the fix-validation report residuals in 0.9.x on 2026-11-15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A responder that cannot take `deadline=` by keyword is refused with a TypeError before any work: no sandbox, no call
- [ ] #2 Every responder call is supervised: the run returns at its deadline as the seconds ceiling, however long the call blocks, and the abandoned call is never read (its work is abandoned, not cancelled, which the docstring states)
- [ ] #3 Expiry is re-checked before an answer is accepted: an answer returned at or past the deadline ends the run at the seconds ceiling, `finished` false, never a successful generate
- [ ] #4 EXEC-08 in `tests/test_execution.py` covers a blocked callback, a callback that accepts but ignores its deadline, a late final answer and a deadline-less callback, beside the stalled and trickling stream tests
- [ ] #5 The suite passes under KG_CLOCK=pinned and the rdflib deterministic run compares with 0 differing leaves
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Regressions in EXEC-08 first (blocked, deadline-ignoring, late final, deadline-less). 2. agent.run refuses a responder that cannot take deadline= before any work. 3. Every call runs in a supervised thread on copies of messages and tools; the run returns at the deadline as the seconds ceiling, the abandoned answer never read. 4. An answer back at or past the deadline is the ceiling, never a finish. 5. Test helpers move to the three-argument form. 6. Suite pinned, rdflib deterministic run and comparator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-minted from TASK-0349 (a sibling's id). Red before the fix: the blocked responder's run returned decision generate. Green after; the rdflib deterministic run against the record: 0 differing leaves over 7 scenarios.
<!-- SECTION:NOTES:END -->
