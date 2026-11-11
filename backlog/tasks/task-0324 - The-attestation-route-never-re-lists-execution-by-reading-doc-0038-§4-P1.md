---
id: TASK-0324
title: The attestation route never re-lists execution by reading (doc-0038 §4 P1)
status: Done
assignee: []
created_date: '2026-11-11T13:34:00Z'
updated_date: '2026-11-11T15:47:00Z'
labels:
  - integrity
  - 0.9.0
dependencies: []
priority: high
ordinal: 316000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled before the 0.9.0 cut under decision-0032 (fails open). Redo group A's N1 and group C's N3 (doc-0038 §4 P1). After an edit (P2 316 -> 341), the gate's attestation finding routes 'agent:maintainer reads the document and lists sha256 <new> under [verification] approval, authored, execution and review versions', and check_subject's fix says 'replace the old digest with the new one'. Followed verbatim, that gives PROCEED with 341.00 approved and verified by execution, while reference_impl.py still holds 316.0. That is doc-0037 §3.1's false PROCEED, which decision-0036 closed. Fix the route and fix text per declaration: execution is re-listed only after the suite passes on the new Version, with the implementation and suite digests (decision-0038 N-b); approval is the approver's own act; review is the reviewer's; authored is the author's. Contracts unchanged: route is a string.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The attestation finding's route names one step per declaration; execution's says run the suite on the Version, then list it with the implementation and suite digests; a test asserts it never tells one reader to list all four
- [x] #2 check_subject's fix text for an edited document under execution says the same; a test
- [x] #3 The record holds; every existing case keeps its outcome
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1UxBF2zxSbQtTZDKCD (#480, merged as 5555343 on a whole green matrix with stack); recorded by the coordinator, the builder having no backlog CLI. gate_cli.attestation_route gives one step per declaration; check_subject._relist_fix the same. Re-checked: group C FIXED (N3); group A wording FIXED, substance NOT FIXED: CargoQuote's suite never reads the document, so 'run the suite on this Version' passes on an edited value. Completed by task-0330.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The attestation finding's route and check_subject's fix name one step per declaration; execution is listed only after the suite runs on the Version, with the implementation and suite digests (decision-0038 N-b). Tests: test_route_names_one_step_per_declaration_and_never_one_reader_for_all_four, test_unattested_artefact_finding_route_is_per_declaration (AC1), test_check_subject_fix_for_execution_says_run_the_suite (AC2); the record holds (AC3). What makes the run mean something, and the limit when it cannot, is task-0330.
<!-- SECTION:FINAL_SUMMARY:END -->
