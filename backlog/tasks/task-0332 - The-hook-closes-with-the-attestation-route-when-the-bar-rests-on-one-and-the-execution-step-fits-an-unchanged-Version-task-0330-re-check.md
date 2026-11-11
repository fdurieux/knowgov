---
id: TASK-0332
title: >-
  The hook closes with the attestation route when the bar rests on one, and the
  execution step fits an unchanged Version (task-0330 re-check)
status: Done
assignee: []
created_date: '2026-11-11T16:52:00Z'
updated_date: '2026-11-11T19:49:00Z'
labels:
  - integrity
  - 0.9.0
dependencies: []
priority: high
ordinal: 324000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes task-0330's H1 (doc-0038 §4 P2), pulled before the cut under decision-0032. Group C's re-check at e8ac07c (session_01HTAA1R97DK5D3Q1B1z6cKo): H2 and H3 FIXED, H1 PARTLY FIXED, no regression.
- H1' (medium): knowgov_hook.py _route_for (about :443) picks ATTESTATION_ROUTE only when every blocker or critical finding shown is kind attestation. The gate never emits an attestation above major, so in the upgrade ('lists no Version') and re-version ('is not attested') cases the only blocker is the bar (kind task). The hook still closes 'Route to approval: the owner of each blocking key answers it (harness/capture.py questionnaire, then ingest)', which contradicts the attestation route printed two lines above. tests/test_claude_hook.py (about :412) reaches ATTESTATION_ROUTE only with a forged blocker-severity attestation finding. Fix: when the blockers are only the bar and an attestation finding is shown, close with ATTESTATION_ROUTE; keep ROUTE whenever a key blocker is present (S2 shows that is right). The test uses a report the gate produces.
- H4 (low-medium, wording): the execution step and ATTESTATION_ROUTE presume the values changed ('changed to this Version's values and run'). In the upgrade case and for an editorial edit the documents' values did not change; the step is: bring the implementation and suite in line with this Version where its values differ, run the suite on it, then list it with the implementation and suite digests.
- H5 (low): 'behind N required key(s)' counts the keys resting on the documents, not those the declaration's absence lowers (review stripped: 10 fall below verified, the finding says 36). Say 'of which M now read below verified'.
- H6 (low): _shown keeps two attestation/lapsed slots whenever more than four blockers exist, even with one such finding; fill the spare slot.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 H1': on the example instance with execution's versions stripped, and with decision_table.md edited, the hook at plan, spec and push closes with the attestation route; with a key blocker present it closes with the questionnaire route; tests on real gate reports
- [x] #2 H4: the execution step and ATTESTATION_ROUTE read correctly for an unchanged Version; a test
- [x] #3 H5, H6: the count names the keys now below verified; the spare slot is used; tests
- [x] #4 The record holds; pristine S1..S7 unchanged
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1UxBF2zxSbQtTZDKCD (#489, merged as 06fa20c on a whole green matrix with stack; main merged in by the coordinator after #488); recorded by the coordinator, the builder having no backlog CLI. The hook tests run on real gate reports of the example instance; each fails on main except the S2 guard. Re-checked by group C at 06fa20c: H1', H4, H5, H6 FIXED, no regression; H7-H9 to task-0329.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The hook closes with ATTESTATION_ROUTE when the only blockers are the bar and an attestation finding is shown, and with the questionnaire route when a key blocks; the execution step reads 'brought in line with this Version where its values differ, the suite run on it, then listed', in the gate route, the hook, check_subject and guide §9; 'lists no Version' adds 'of which M now read below verified'; the hook's summary holds a bar slot only per bar finding present. Tests: tests/test_hook_route.py on real gate reports (execution stripped, decision table edited, S2, review stripped, slot logic) and tests/test_attestation_route.py's wording assertions; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
