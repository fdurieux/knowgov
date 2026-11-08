---
id: TASK-0198
title: >-
  One clock: every lapse decided as of the gate's date, a person's approval
  included (doc-0030 F4: H3, G4, G10, M8)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T00:01:00Z'
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
- [ ] #1 For one --as-of the gate report is identical under any KG_TODAY, by a test with two KG_TODAY values on a subject holding a person's approval and a review-file approval
- [ ] #2 A person's approval past its months reads proposed as of the date, with a lapsed finding; a review-file approval with no verification lapses at its date plus the key's months
- [ ] #3 Approvals and verifications dated after the as-of date are not counted
- [ ] #4 three_valued_answer marks a lapsed statement as of the session date
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. load_reviews reads no clock: every accepted approval applied with its until (six months after the answer); the future-date refusal only where a caller passes now (capture.py review). 2. cadence.lapse decides every lapse against on: review verifications and review-file approvals counted only when dated on or before on (G10); a person's approval current until its until (H3), reading proposed after; a document statement's review-file approval current for the key's months from its date, with or without a verification (G4); approved only after the date reads verified. The lapse names the status it reads (to). 3. key_evidence returns an approval's until on both adapters; gate.resolve applies to; findings and the bundle say why (the plain review lapse renders as before, the bundle's bytes pinned). 4. three_valued_answer marks lapses as of the session date (M8), as_of in its output, schema additive. 5. tools/check_one_clock.py on the example instance, both stores; CI and a suite test; unit tests in test_cadence. 6. Record, walkthroughs, stage-2 check, round trips; suite both ways.
<!-- SECTION:PLAN:END -->
