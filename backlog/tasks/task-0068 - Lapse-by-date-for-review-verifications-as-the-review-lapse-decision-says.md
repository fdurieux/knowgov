---
id: TASK-0068
title: Lapse by date for review verifications, as the review-lapse decision says
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:35:00Z'
labels:
  - gate
milestone: m-5
dependencies:
  - TASK-0067
references:
  - backlog/docs/doc-0013
priority: medium
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P2: build what the decision in TASK-0067 settles. Today valid_until carries no date on a review verification, so a document's review never falls due.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 valid_until carries a date on review verifications where the decision says so, in both adapters
- [x] #2 A lapsed verification lowers the key and the gate report names it as a finding
- [x] #3 The deterministic record is unchanged, or the comparator's change is recorded with its reason
- [x] #4 instance/README.md and docs/guide.md say when a review falls due
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/cadence.py: the register's review months per key (lifecycle.toml [review.kinds], shortest among the key's register_map nodes, else default_months); due date; lapse as of a date; renewal by a later ruling approval.
2. Port: review_verifications and set_valid_until, both adapters; load_verifications dates every review.
3. gate.resolve_spec(as_of): a lapsed statement reads validated, listed in lapsed; gate_cli --as-of (today|record|date), finding kind lapsed (major); schema additive in v2; MCP gate_verdict as_of.
4. subject.toml [record] as_of pinned (cargo 2026-10-30, J-F 2026-10-24); run.py records as_of, the comparator holds it to the pin.
5. Tests (tests/test_cadence.py), CI expectations pinned --as-of record plus the lapse shown in harness.yml; docs.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proven locally: rdflib S1-S7 and J-F 0 differing leaves; Neo4j 5.26.0 community (Java 21) S1-S7 and J-F 0 differing leaves (D1 compared), saved queries, MCP check, round trip neo4j,rdflib,neo4j. As of 2027-08-06 S1 PROCEED, as of 2027-08-07 S1 BLOCKED 10 keys below verified (19 statements lapsed), S3 BLOCKED 13, S6 BLOCKED 10; --baseline record exits 1 naming approved -> validated. J-F --as-of 2030-01-01 --baseline record exits 0. tests/run_tests.py 206/206 plain and with KG_SUBJECT=subjects/jef_data_load.
Choices: valid_until is the last current day (lapse the day after); a source change's tag still overwrites a date (the statement is invalidated either way); a replacement whose own review lapsed still supersedes the invalidated statement (it reads validated, not invalidated); renewal is an approval in a person's review file (appr:review:*) after the latest review; approving a document's statement needs closes (decision-0002), so the docs say so rather than 'approves'. A run naming no as_of (older runs) is not held to the pin by the comparator.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0005 built. A review verification's valid_until is its date plus the review months of the kind its key concerns (register lifecycle.toml [review.kinds], shortest among the key's register_map nodes, else default_months), written at load in both adapters through two new port operations (review_verifications, set_valid_until; harness/cadence.py). The gate reads currency as of a date: a statement whose reviews have all passed their date, not renewed by a later ruling approval, reads validated with its approval, is listed in lapsed, and gate_cli reports a lapsed finding (major); --as-of today|record|YYYY-MM-DD, today by default; the MCP gate_verdict takes as_of. Schema: as_of, lapsed and the finding kind lapsed, additive in v2 (a contract change for 0.2.0 under decision-0003; CHANGELOG left to the release PR). subject.toml [record] as_of pins the record (CargoQuote 2026-10-30, J-F 2026-10-24); run.py records as_of and the comparator holds a run to it, so the record never moves by the clock: 0 differing leaves on rdflib and Neo4j 5.26, both subjects. As of 2027-08-07 CargoQuote S1 and S6 read BLOCKED (10 keys), S3 BLOCKED (13), as the decision measured; J-F does not move. CI's fixed gate expectations now read --as-of record, and harness.yml shows the lapse. Docs: guide §9, instance README, demo README, glossary crosswalk row 'review lapsed'. Follow-up candidates: the page could show the as-of date and lapsed statements; check_review_walkthrough still reads the wall clock for capture approvals (its six-month lapse will move it after 2027-05-03).
<!-- SECTION:FINAL_SUMMARY:END -->
