---
id: TASK-0306
title: >-
  An execution verification holds only for the document Versions it was attested
  on (decision-0036)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T21:32:00Z'
updated_date: '2026-11-09T23:24:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0036
  - backlog/decisions/decision-0019
  - backlog/docs/doc-0037
priority: high
ordinal: 299000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0036, accepted 2026-11-09 ("Agreed", doc-0037 §3.1). Found by the functional review, groups A (F1) and C (C2-2), at main f194aac, and confirmed by the coordinator.

`harness/load.py` `load_verifications` writes `verify_by_execution` (`outcome: pass`, `evidence_sha256` the reference code's digest) for every live statement whose (key, value) the pristine kit states. No suite runs. On an instance the pristine kit is the documents on disk, so an edited value inherits "verified by execution".

Repro, the example instance's S1 with P2's surcharge changed from 316.00 to 341.00 in decision_table.md:
- with the shipped `versions`: QUALIFIED, and P2|surcharge reads VERIFIED at 341;
- with `versions` removed: PROCEED.

`docs/guide.md:686` says "the oracle runs again on every load".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An execution verification is written only for a statement whose document Version digest the subject's execution attestation lists (decision-0019's `versions`, extended to the execution declaration); an unlisted Version is not verified by execution.
- [x] #2 Every other verification kind written per load (review, wherever not yet version-bound) follows the same rule, or the task records why it already does.
- [x] #3 Both repros are tests. The edited P2 falls below verified and is not approved, so the gate is not PROCEED on it; the pristine documents read as before.
- [x] #4 The record does not move: the public subjects' attestations list their Versions where needed. Both comparators, the round trip and `check_mcp_server` hold.
- [x] #5 `docs/guide.md` §9 and :686 say what an execution verification is (the subject's attested result, bound to the Versions it lists; no oracle runs at load), and a CHANGELOG line names it under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port: verify_by_execution and verify_by_review take the stored artefacts their declaration attests (both adapters).
2. load.load_verifications: bound_artefacts reads [verification] execution's and review's versions; no list verifies nothing (decision-0036, no read rule).
3. Stage 2: withdraw_construction also takes back ver:exec: verifications; the load calls it before it verifies, over every bound declaration's unlisted Versions.
4. The public subjects list in execution and review the Versions authored lists, so the record holds.
5. check_subject notes a bound declaration with no list; checks that edit a copy list their edit (example_instance.attest, check_ledger_binding, check_stage2_reload's synthetic plants).
6. tests/test_execution_binding.py: both repros, the pristine reading, the stage-2 withdrawal.
7. docs/guide.md §2 and §9, instance/README.md, subjects/README.md; CHANGELOG under Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Bound kinds (AC 2): the two verification kinds the load writes per statement, execution (verify_by_execution) and review (verify_by_review), each take the stored artefacts their declaration's versions lists (load.bound_artefacts). decision-0036 says 'review included'; read here as no read rule for either: a declaration listing no Version verifies nothing, and a subject with a verification map and no [verification] execution writes no execution verification (check_subject notes both, naming decision-0036). authored and approval keep decision-0019's read rule unchanged; an approval still applies only to a verified assertion (approve_verified reads status verified).
Stage 2: withdraw_construction (both adapters) also deletes a statement's ver:exec: verifications, and load_verifications calls it before it verifies, over the union of every bound declaration's unlisted Versions, so what is still listed is written again as a fresh load writes it.
The record: cargo_quote and jef_data_load list in execution and review the same Versions authored lists (23 and 89 digests). Comparators 0 leaves on S1-S7 and J-F; check_round_trip --chain both subjects on rdflib and Neo4j; check_mcp_server cargo_quote, J-F and minimal.
Checks that edit a copied instance list the edit: example_instance.attest now writes all four lists; check_ledger_binding lists its P2 edit (it measures the ledger); check_stage2_reload lists each synthetic plant for its case (listed()). Repro tests in tests/test_execution_binding.py fail on main with ('QUALIFIED','verified') and ('PROCEED','approved').
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Execution and review verifications are bound to the Versions [verification] execution and review list (decision-0036): an edited, unlisted document Version is neither verified by execution nor approved, and a declaration listing none verifies nothing. Stage 2 takes back an unlisted Version's execution verifications before it verifies. The public subjects list their Versions, so the record does not move (both comparators, round trips, check_mcp_server). Both functional-review repros, the pristine reading and the stage-2 withdrawal are tests. Guide §2/§9, the glossary, instance/README.md and subjects/README.md say what an execution verification is; CHANGELOG under Contract changes. Risk: an adopter instance without an execution declaration loses its execution verifications until it lists its Versions; check_subject notes it.
<!-- SECTION:FINAL_SUMMARY:END -->
