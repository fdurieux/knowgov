---
id: TASK-0318
title: >-
  The not-attested finding and its route name every declaration that omits the
  Version (decision-0036): execution and review too
status: Done
assignee: []
created_date: '2026-11-10T02:25:00Z'
updated_date: '2026-11-10T04:46:00Z'
labels:
  - integrity
  - routes
  - 0.9.0
dependencies: []
priority: high
ordinal: 311000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut: the documented route does not lead back (the coordinator, 2026-11-10). Found by group 3's re-check of task-0306 (session_01HTAA1RJ9Rg2FP5uZoxBXic, main e4f73e0); C2-2 itself is fixed.

After a document edit (S1, decision_table.md P2 316.00 to 341.00) the only document finding reads "contract/decision_table.md (sha256 3a1eec6f3c04), behind 31 required key(s), is not attested: [verification] approval and authored list(s) no digest of this Version... (decision-0019)", and its route says to list the digest under approval and authored. Following that route exactly leaves S1 BLOCKED (31 major, "31 of 36 required keys below verified") with no finding naming `execution`, `review` or decision-0036, since task-0306 binds those too. A comment-only edit to openapi.yaml shows the same with `review`. harness/gate.py has no decision-0036 path.

Fix: the not-attested finding (the same kind, so no contract change) names every `[verification]` declaration whose `versions` omits the Version (authored, approval, execution, review), cites decision-0036 beside decision-0019 where execution or review is among them, and stays while any of them omits it. Its route lists them all. check_subject's note agrees.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 After the P2 edit, the finding names authored, approval, execution and review (those declared), and its route lists all of them; a test reproduces it and fails on e4f73e0
- [x] #2 Following the route (the digest listed in every named declaration) brings S1 back to PROCEED, and no not-attested finding remains; a test
- [x] #3 A comment-only edit to a review-verified document names review; a test
- [x] #4 The record holds; the kind and the report shape are unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Record execution and review attestations at load and read all four declarations back on both adapters; the not-attested finding names every declaration omitting the Version and cites decision-0036 beside decision-0019; check_subject notes an empty versions list and reports an edited document once per artefact and declaration.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1UGCvzo1TX97UCuwsf (#463, head 53a91b2), with group 3's N1 and reviewer A's N-a and N-c from their re-checks of task-0306; merged through train claude/train-463 for a CHANGELOG conflict (GitHub ran no CI on the conflicted head); recorded by the coordinator, the builder having no backlog CLI. load.record_bound_attestations stores execution and review attestations; attestations() reads all four on rdflib and Neo4j; the Neo4j read is exercised in the stack job by tools/check_attestation_binding.py step 3 (names_every_declaration). Side effect: when a stale digest and an edit coexist, check_subject names the edit and does not separately name the stale digest; still an error, same exit. check_attestation_binding step 4 now restores the table before measuring the all-zero digest.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The way back after a document edit is complete: the not-attested finding names every [verification] declaration whose versions omit the Version (authored, approval, execution, review) and cites decision-0036 beside decision-0019 where execution or review is among them, and following its route brings S1 back to PROCEED. check_subject notes an empty execution or review versions list as verifying nothing, and reports an edited document once per artefact and declaration, naming it and its new digest. Tests in tests/test_execution_binding.py (each failing on the old code); the stack job's check_attestation_binding exercises the Neo4j read. Kind and report shape unchanged; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
