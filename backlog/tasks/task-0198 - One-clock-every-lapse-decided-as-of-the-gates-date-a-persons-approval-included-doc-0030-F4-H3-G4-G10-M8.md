---
id: TASK-0198
title: >-
  One clock: every lapse decided as of the gate's date, a person's approval
  included (doc-0030 F4: H3, G4, G10, M8)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T00:19:00Z'
labels:
  - review
  - cadence
dependencies:
  - TASK-0193
priority: high
type: bug
ordinal: 198000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

H3 (high, two reviewers): a person's six-month approval lapses at load against review.today() (load.py:294,321; gate_cli.py:517 passes no date) while cadence.lapse skips elicited statements, so one --as-of reads PROCEED or QUALIFIED by the calendar and the report names an as_of it did not read. Contradicts decision-0005 points 3 and 5. G4: a review-file approval with no verification never lapses (cadence.py:158). G10: approvals and verifications dated after --as-of count. M8: three_valued_answer ignores currency. A fix with an additive `lapsed` entry; doc-0028 G9-11.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 For one --as-of the gate report is identical under any KG_TODAY, by a test with two KG_TODAY values on a subject holding a person's approval and a review-file approval
- [x] #2 A person's approval past its months reads proposed as of the date, with a lapsed finding; a review-file approval with no verification lapses at its date plus the key's months
- [x] #3 Approvals and verifications dated after the as-of date are not counted
- [x] #4 three_valued_answer marks a lapsed statement as of the session date
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. load_reviews reads no clock: every accepted approval applied with its until (six months after the answer); the future-date refusal only where a caller passes now (capture.py review). 2. cadence.lapse decides every lapse against on: review verifications and review-file approvals counted only when dated on or before on (G10); a person's approval current until its until (H3), reading proposed after; a document statement's review-file approval current for the key's months from its date, with or without a verification (G4); approved only after the date reads verified. The lapse names the status it reads (to). 3. key_evidence returns an approval's until on both adapters; gate.resolve applies to; findings and the bundle say why (the plain review lapse renders as before, the bundle's bytes pinned). 4. three_valued_answer marks lapses as of the session date (M8), as_of in its output, schema additive. 5. tools/check_one_clock.py on the example instance, both stores; CI and a suite test; unit tests in test_cadence. 6. Record, walkthroughs, stage-2 check, round trips; suite both ways.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified locally on rdflib and on Neo4j 5.26.16. tools/check_one_clock.py on the example instance holds every check on both stores, and fails six on the old code: --as-of 2026-11-03 and --as-of 2027-05-03 each differed between KG_TODAY 2026-11-03 and 2027-05-03 (H3, the reviewer's probe), the answers never lapsed at the gate, three_valued_answer had no as_of and marked nothing (M8), the review-file approval with no verification never lapsed (G4), and the approval dated after the as-of counted (G10). Now: PROCEED as of ON under both days, identical reports; QUALIFIED as of LAPSED with the three answers lapsed to proposed under both days; A:spec:response|statuses@v1 approved 2026-11-03 for 6 months lapses on 2027-05-04, and as of 2026-11-02 is not counted. Unit tests in test_cadence for H3, G4, G10 and the load reading no clock. The record: S1-S7 0 differing leaves on rdflib and Neo4j, J-F 0 over 6. Both stores: check_review_walkthrough, check_gate_after_change, check_stage2_reload, check_mcp_server (S1,S2,S6), round trips (rdflib; neo4j,rdflib,neo4j). Suite: plain 716/718 (2 skipped), J-F 715/718 (3 skipped), 0 failed. Known limit, not widened here: a subject that leaves its review undated ([verification] review at) is dated by the load's day (load.now(), KG_TODAY else the clock), so for such a subject an --as-of before the load day still depends on the day. CargoQuote dates its review. The bundle's bytes for a plain review lapse are unchanged (tests/test_arms pins them); only a person's lapse and an event after the date use the new wording. The maintainer's open question (an idempotent close so reviews can be re-read at stage 2) is not built: the review check here still refuses a close of a gap that is no longer open; this change makes it a small, separate edit in review.check's closes loop, since load_reviews no longer carries a clock.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every lapse is now decided against the gate's date: load_reviews applies each accepted approval with its until and reads no clock; cadence.lapse counts only what is dated on or before the as-of date, lapses a person's approval to proposed past its until (H3), a review-file approval with no verification at its date plus the key's months (G4), and does not count events after the date (G10); the lapse names the status it reads. key_evidence returns an approval's until; three_valued_answer marks lapses as of the session date (M8). tools/check_one_clock.py proves one --as-of gives one report under two KG_TODAY values, on both stores, and fails on the old code; the record is unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
