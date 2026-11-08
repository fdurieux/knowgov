---
id: TASK-0223
title: Conflict gap ids content-derived over a defined order (decision-0020)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:56:00Z'
updated_date: '2026-11-08T12:59:00Z'
labels:
  - store
  - rules
  - contract
  - record
dependencies:
  - TASK-0202
references:
  - >-
    backlog/decisions/decision-0020 -
    Conflict-gap-ids-are-content-derived-as-person-pairs-already-are-over-a-defined-order-one-id-per-conflict-on-every-store.md
priority: high
type: feature
ordinal: 223000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0020, accepted (the maintainer, 2026-11-08: accept decision-0020's advice; task-0202, doc-0030 S2). R-CONFLICT (harness/rules.py r_conflict) names a person's conflict gap:conflict:<key>:<a>~<b> but numbers a document conflict :<n> in candidate_pairs' undefined store order, so one S4 conflict is :0 on Neo4j and another on rdflib, and the default gate (rdflib scratch, decision-0017) and the page (Neo4j) disagree. Name every document conflict gap:conflict:<key>:<a>~<b> with its assertion ids sorted; order candidate_pairs and conflict_gaps by key then id on both adapters; extend demo/tools/compare_deterministic.py's CONFLICT_ID normaliser to both forms per key; re-pin deliberately, and name, the bundle bytes and fixtures that carry :<n> (test_arms, S4). The vendored results keep :0..3 and are never edited; subjects/README.md notes the form change. A contract change (the gate report's conflict ids), for 0.9.0 (doc-0028 G9-14).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 r_conflict names every document conflict gap:conflict:<key>:<a>~<b> with its assertion ids sorted; person pairs are unchanged
- [x] #2 candidate_pairs and conflict_gaps answer ordered by key then id on rdflib and Neo4j, and one conflict has one id on both (S4 shown)
- [x] #3 Adding an unrelated conflict on the key leaves every other conflict's id unchanged, by a test
- [x] #4 compare_deterministic.py normalises both forms per key; the scored record (S1 to S7), the deterministic run and the comparator stay equal
- [x] #5 Every re-pinned byte or fixture is named in the PR; no vendored file is edited; subjects/README.md notes the form
- [x] #6 CHANGELOG.md carries the line under Unreleased's contract heading
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. r_conflict: every conflict gap:conflict:<key>:<a>~<b>, ids sorted. 2. candidate_pairs by key then id, conflict_gaps by id, on rdflib and Neo4j. 3. compare_deterministic CONFLICT_ID reads :<n> and <a>~<b> as one per key. 4. tools/check_conflict_ids.py: fresh loads on the named stores, one id per conflict, ordered, S4 required; stack job Neo4j vs rdflib, harness.yml rdflib. 5. Re-pin test_pairing; tests for the form and stability. 6. subjects/README.md, CHANGELOG contract line, CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence: #1 tests/test_pairing.py test_every_conflict_id_names_its_two_statements_sorted_a_person_s_and_two_documents_alike (person pairs unchanged in form, document pairs now a~b, no :<n>). #2 tools/check_conflict_ids.py --stores neo4j,rdflib --require S4 on a local Neo4j 5.26: S4's four conflicts one id each on both, conflict_gaps by id and candidate_pairs by key then id; the old code fails it 12 ways. #3 test_adding_an_unrelated_conflict_on_the_key_leaves_every_other_conflict_s_id_unchanged, both store orders; fails on the old rule. #4 comparator OK, 0 differing leaves: CargoQuote S1-S7 and J-F, on rdflib and on Neo4j; round trip --chain rdflib,rdflib and neo4j,rdflib,neo4j on both subjects; check_mcp_server (rdflib S1,S2,S4,S6; Neo4j S4); check_gate_after_change; check_stage2_reload on both subjects. #5 re-pinned: tests/test_pairing.py only (the documents-conflict test held gap:conflict:k|v:0); no other pinned byte moved (test_arms' bundle tests use synthetic results with no document conflict); no vendored file edited; subjects/README.md notes the form. #6 CHANGELOG Unreleased > Contract changes. Suites: stdlib 720/757 (37 skipped), pins 755/757 (2 skipped), KG_SUBJECT=subjects/jef_data_load 754/757 (3 skipped).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0020 built. R-CONFLICT names every conflict `gap:conflict:<key>:<a>~<b>` with its two assertion ids sorted, so a conflict between two documents takes the content-derived form a person's conflict already had and the positional `:<n>` is gone. `candidate_pairs` answers ordered by key then id and `conflict_gaps` by id on rdflib and Neo4j, so one conflict has one id on both stores (S4's four, shown by the new `tools/check_conflict_ids.py`, run Neo4j against rdflib in the stack job and on rdflib in harness.yml) and a new conflict on a key renames none of the others. `compare_deterministic.py` reads the vendored record's `:<n>` and the new form as one per key: the scored record, the deterministic run and the comparator stay equal on both subjects and both stores. Re-pinned: tests/test_pairing.py's document-conflict id test. A contract change for 0.9.0 (doc-0028 G9-14).
<!-- SECTION:FINAL_SUMMARY:END -->
