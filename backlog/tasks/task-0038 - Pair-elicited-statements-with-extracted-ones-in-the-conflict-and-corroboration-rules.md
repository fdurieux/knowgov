---
id: TASK-0038
title: >-
  Pair elicited statements with extracted ones in the conflict and corroboration
  rules
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T23:06:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: medium
type: bug
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 F3: `candidate_pairs` (both store adapters) pairs only assertions of the same `version`; a capture's version is `capture`, the documents' `v1`. So a person contradicting a document (S2: John's status list includes held_unscreened, the contract's does not) raises no conflict gap, and a person agreeing with one corroborates nothing. A person contradicting a document is exactly what a reviewer needs to see.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An elicited statement whose value conflicts with an extracted one on the same key produces a conflict gap naming both, on both adapters
- [x] #2 An elicited statement equal to an extracted one is recorded as agreeing, without raising either above its status (elicited stays proposed)
- [x] #3 The deterministic record for S1 to S7, which has no captures, is unchanged: the comparator stays green
- [x] #4 A test covers both cases with a capture on S2
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port: candidate_pairs(across) pairs across versions when exactly one side carries the named basis; corroborate(promote); mark_conflict(text). Both adapters, neither naming the basis.
2. rules.py: pairs() feeds R-CORROBORATE and R-CONFLICT with document pairs as before and person-vs-document pairs; an agreement corroborates without promote; a contradiction raises a conflict gap with a pair id and its own wording; nobody-knows pairs with nothing; a person is not weighed against a model.
3. Review: a dispute settled on a person's side stays settled when the approval lapses; the statement reads proposed (apply_ruling 'lapsed').
4. Walkthrough S2' now passes through the dispute; tools/check_capture_pairing.py on the example instance (rdflib in harness.yml, Neo4j in the stack job); tests/test_pairing.py.
5. Comparator on S1-S7 (rdflib, Neo4j) and the J-F record unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (local, CPython 3.13 with the record's pins; Neo4j 5.26 community tarball):
- AC1: tools/check_capture_pairing.py on the example instance, S2, employee-1's status list with held_unscreened: gap:conflict:response|statuses:<cap>~A:oas:...@v1 and ~A:spec:...@v1, each concerning both, text naming the capture's record and the document; all three disputed; the gate reads the key disputed. OK on rdflib and on Neo4j.
- AC2: same check, quote_api|technology 'Python 3.12, FastAPI' agreeing with the C4 model: CORROBORATES recorded, both still proposed; an answer equal to the documents' validated list leaves them validated and the capture proposed (tests/test_pairing.py).
- AC3: compare_deterministic.py: 0 differing leaves over S1-S7 on rdflib and on Neo4j (D1 compared there); J-F subject 0 over 6.
- AC4: tests/test_pairing.py (stdlib, S2's values), 143/143 with and without KG_SUBJECT=subjects/jef_data_load; harness.yml capture step still passes.
- Side effects named: the review walkthrough's S2' now meets the dispute (BLOCKED, disputed) and settles it whole through employee-3 (approves + closes); a lapsed approval on a settled dispute leaves the dispute settled and the person's statement proposed (apply_ruling 'lapsed', both adapters). 'Nobody knows' (empty value) pairs with nothing; a person is not weighed against a model (inferred).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
R-CONFLICT and R-CORROBORATE now weigh a person's statement (basis elicited, version capture) against the documents' extracted statements of any version (doc-0007 F3). The port's candidate_pairs takes `across`, the basis that pairs across versions, so neither adapter names it; corroborate takes `promote` and mark_conflict an optional text. A contradiction disputes both sides and raises a conflict gap with a pair id (gap:conflict:<key>:<a>~<b>, so the documents' numbered ids are untouched) worded 'a person and a document state different values'; an agreement is recorded as CORROBORATES and raises neither side. The review step settles such a dispute as any other: employee-3 (approves, closes) rules on every side; an approval that lapses leaves the dispute settled and the statement proposed. Record unchanged (comparator 0 differing leaves, rdflib and Neo4j); tools/check_capture_pairing.py shows both cases on the example instance in harness.yml and the stack job; the review walkthrough's S2' now passes through the dispute. Follow-up worth considering, not done: doc-0007's F3 row and §11 still say 'not built'.
<!-- SECTION:FINAL_SUMMARY:END -->
