---
id: TASK-0333
title: >-
  A later decided ruling clears an opposed act, approved or rejected (task-0331
  re-check)
status: To Do
assignee: []
created_date: '2026-11-11T18:01:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 325000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes task-0331 (task-0328, doc-0038 §4 P5), pulled before the cut under decision-0032. Group C's re-check at main 11218a5 (session_01HTAA1R97DK5D3Q1B1z6cKo), on rdflib and Neo4j alike: R1 (approval settles), R2, R3, R4, R5 FIXED, no regression.
- R1' (medium): a later decided rejection never clears the opposed acts. In case D2 (employee-2 approves and boss rejects on 11-06, carol rejects on 11-08) the key reads from the new ruling (absent), as the route asked, but both acts stay major for good ('the key was ruled by … (rejected)'), so a pipeline on --fail-on major stays red after a legitimate rejection; the only exit is an approval that reverses the owners. task-0331's AC 'a later rejection leaves it major' was the coordinator's error: task-0322's review.settling already settles a legacy act on any later ruling of the same statement, and task-0323 L1 settles on a decided ruling, approved or rejected. Fix: an opposed act settles (info, 'settled by <file>') on any later applied decided ruling (approved or rejected) of the same statement; a later referral leaves it major. instance/README's remedy sentence follows.
- R6 (low): a settled opposed act still carries the route 'the owners rule again in one review, on a later day'; a settled act names no route (or 'none: settled by <file>').
- R7 (low): capture.py review's warning on a write that joins a cancelled set says 'is opposed by <files>, a ruling of another reviewer … the load applies neither'; with three rulings, name them as 'cancelled with <file> (<outcome>), …; none applies', matching the act's reason.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 R1': an opposed pair then a later rejection of the same statement reads info 'settled by <file>' on both acts and the key from the rejection; a later referral leaves them major; tests and check_act_binding cases on both stores
- [ ] #2 R6, R7: a settled act carries no 'rule again' route; the warning names the cancelled set; tests
- [ ] #3 instance/README states the remedy for both outcomes; every existing case keeps its outcome; the record holds
<!-- AC:END -->
