---
id: TASK-0330
title: >-
  The re-attest route names what makes a run mean something, and the limit when
  it cannot (task-0324 re-check)
status: To Do
assignee: []
created_date: '2026-11-11T14:48:00Z'
labels:
  - integrity
  - 0.9.0
dependencies: []
priority: high
ordinal: 322000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes task-0324 (doc-0038 §4 P1), pulled before the cut under decision-0032. Group A's re-check at main 5555343 (session_01HTAA1TXUvboU1nXJwqR1gs): the wording is fixed, N1 is not, on rdflib and Neo4j alike.
- CargoQuote's suite never reads the document. It runs reference_impl.py (HEAVY_SURCHARGE = 316.0) against its own expectation (price_exact_heavy 3186.00), so after the 316 -> 341 edit it passes 11/11.
- Following only the execution step, with the implementation and suite digests unchanged, gives QUALIFIED and P2|surcharge 341.00 verified by execution. Adding the approver's step gives PROCEED.
- 'The suite is run on this Version' is satisfied by a run that never tested the Version.
Fix, behind unchanged contracts:
- (1) The route and check_subject's fix say what makes the run mean something: change the reference implementation and the suite to the new Version's values, run them, then list all three digests (document Version, implementation, suite). They also say plainly that if the implementation and suite are unchanged, re-listing only asserts the old result for the new values (the known limit: no oracle at load, re-listing re-verifies).
- (2) check_subject notes, as a note and never an error, when [verification] execution lists a document digest that no earlier listed Version of the same document shares while its implementation and suite digests equal the files on disk. knowgov cannot know whether the suite covers the edited value, so the note names that.
- (3) docs/guide.md §9 (about :690) names the limit beside 'until the attestation lists the new Version's digest'; the CHANGELOG line for task-0324 likewise.
- (4) R-b: the attestation finding's consequence clause names only the declarations actually bound. When only review is bound, the consequence is the lost review verification, under decision-0036, not 'authored statements read proposed … nothing approved'.
- (5) The gate's and check_subject's wording for the review step agree.
- (6) Each step that names an approver or reviewer adds that they must not be the author (decision-0002), as the capture routes do.
R-a (one 'at' per [verification] declaration cannot date one document's re-review) goes to Known limits with one line in the review step pointing to capture.py review for a single document; the shape is a 1.0 gap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The execution step says change the implementation and suite to the new values, run them, then list the three digests, and names the limit when they are unchanged; a test on the route and on check_subject's fix
- [ ] #2 check_subject notes a newly listed document digest whose implementation and suite digests are unchanged, naming that knowgov cannot know whether the suite covers the change; a test
- [ ] #3 guide §9 and the CHANGELOG name the limit; tests/test_docs_* hold
- [ ] #4 The consequence clause names only the bound declarations; the review step's wording agrees between gate and check_subject; approver and reviewer steps name decision-0002; tests
- [ ] #5 The record holds
<!-- AC:END -->
