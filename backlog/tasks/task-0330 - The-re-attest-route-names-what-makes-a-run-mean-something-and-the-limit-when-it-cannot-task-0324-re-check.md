---
id: TASK-0330
title: >-
  The re-attest route names what makes a run mean something, and the limit when
  it cannot (task-0324 re-check)
status: Done
assignee: []
created_date: '2026-11-11T14:48:00Z'
updated_date: '2026-11-11T18:02:00Z'
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
- [x] #1 The execution step says change the implementation and suite to the new values, run them, then list the three digests, and names the limit when they are unchanged; a test on the route and on check_subject's fix
- [x] #2 check_subject notes a newly listed document digest whose implementation and suite digests are unchanged, naming that knowgov cannot know whether the suite covers the change; a test
- [x] #3 guide §9 and the CHANGELOG name the limit; tests/test_docs_* hold
- [x] #4 The consequence clause names only the bound declarations; the review step's wording agrees between gate and check_subject; approver and reviewer steps name decision-0002; tests
- [x] #5 The record holds
- [x] #6 H1: the hook's message carries the attestation finding and its route when the bar rests on it; a test on knowgov_hook.py
- [x] #7 H2, H3: the 'lists no Version' finding names each document and digest, is major, names what is lost and the key count; check_subject's note is complete; tests
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Group C's re-check of task-0325/task-0324 at 5555343 (session_01HTAA1R97DK5D3Q1B1z6cKo): N3 FIXED; N2 FIXED in the gate CLI, MCP gate_verdict and the annotations; NOT FIXED in the hook. Added to this task, as they complete the same pulled fix:
- H1: instance/ci/claude/knowgov_hook.py (about :428) passes only blocker and critical findings to the assistant, so the attestation finding (the cause and its route) never reaches it at plan, spec or push, and the closing 'Route to approval' names the questionnaire whatever the cause. Fix: include the findings the bar rests on (attestation, lapsed), or every finding kind other than key, below the blockers; the closing route follows the cause.
- H2: the 'lists no Version' route uses a '<digest>' placeholder and names no document; name each document and its digest as the edited-document finding does. check_subject's note for a declaration listing nothing ends mid-sentence ('…list the digest of each', tools/check_subject.py about :449).
- H3: a declaration that verifies nothing is info, while an unlisted edited Version is major. Raise it to major, as the cause of the BLOCKED. Its consequence clause names what is lost (approvals resting on execution read proposed too) and gives the count of keys behind it, as 'behind 31 required key(s)' does.

Re-checked by group A at e8ac07c: N1 FIXED (the honest path gives a genuine verification; the shortcut is named), R-a and R-b FIXED; residues N-1, N-3..N-5 to task-0329; N-2 to doc-0038 §3.5.

Re-checked by group C at e8ac07c: H2, H3 FIXED; H1 PARTLY FIXED (the cause and route reach the assistant; the closing route stays the questionnaire because ATTESTATION_ROUTE cannot fire on a real report): task-0332, with H4-H6.

Built by session_01HTAA1UxBF2zxSbQtTZDKCD (#485, merged as e8ac07c on a whole green matrix with stack), with group C's H1-H3; recorded by the coordinator, the builder having no backlog CLI. Each new test fails on main (failure lines in the builder's report). Re-checked: group A N1 FIXED (honest path genuine: impl 341 alone fails the suite 9/11, suite expectations updated pass 11/11, then PROCEED; the shortcut named), R-a, R-b FIXED; N-2 to doc-0038 §3.5; N-1, N-3..N-5 to task-0329. Group C: H2, H3 FIXED, H1 PARTLY (closing route) -> task-0332.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The re-attest route and check_subject's fix say what makes an execution listing mean something (bring the implementation and suite in line with the Version, run, list the three digests) and name the limit; check_subject notes an edited document listed with unchanged code (a digest replaced outright is not seen, guide §9 says so); the consequence clause names only bound declarations; review wording agrees; approver and reviewer steps name decision-0002; the review step points to capture.py review for one document; 'lists no Version' is major, naming documents, digests and the key count; the hook shows attestation findings. Tests in tests/test_attestation_route.py and tests/test_claude_hook.py; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
