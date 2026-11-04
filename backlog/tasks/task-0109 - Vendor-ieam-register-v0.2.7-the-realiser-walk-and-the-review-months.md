---
id: TASK-0109
title: 'Vendor ieam-register v0.2.7: the realiser walk and the review months'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T12:03:00Z'
updated_date: '2026-11-04T12:31:00Z'
labels:
  - register
  - vendor
milestone: m-8
dependencies: []
priority: medium
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ieam-register v0.2.7 (2b9e093) carries decision 0012 (`tools/impact.py --walk realisers`, PR #18) and decision 0013 (`[review.kinds]` review months: step 6, touchpoint 6, module 12, business_entity 12; PRs #19, #22). The page reads the register vendored at a tag, so the cadence the gate applies under decision-0005 only changes once it is re-vendored; tasks 0081 and 0087 wait on it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `demo/register` is vendored at ieam-register `v0.2.7` (2b9e093) by `tools/vendor_register.py`; its SOURCE note and digest test agree.
- [x] #2 The comparator and the deterministic record are unchanged at the record's `as_of` 2026-08-06.
- [x] #3 CargoQuote S1–S7 gate verdicts as of 2027-02-07 are recorded in the task notes, with the three `response|*` keys lapsing at 6 months.
- [x] #4 Tasks 0081 and 0087 are closed, citing ieam-register #18, #19 and #22 and this vendoring.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Clone ieam-register at v0.2.7 (2b9e093) and vendor it with tools/vendor_register.py.
2. Update the tests and CI steps that pin v0.2.6 or a uniform 12-month cadence (test_vendor_register, test_register_view, test_cadence, test_page_as_of; harness.yml gate block, demo.yml projection/store tag and the task-0076/0086 as-of steps).
3. Run both suites, the deterministic comparison on both subjects (rdflib, pinned venv), the harness.yml gate block and the demo.yml as-of snippets against a local run.
4. Gate S1-S7 as of 2027-02-07; record verdicts.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Vendored v0.2.7 (2b9e0936, merge of #22): 98 files; changed metamodel/lifecycle.toml ([review.kinds] step 6, touchpoint 6, module 12, business_entity 12; decision 0013) and tools/impact.py (`--walk realisers`, decision 0012; default walk unchanged); added decisions 0012, 0013. v0.2.6 moves to the note's earlier copies.

Cadence effect on CargoQuote: 12 of 36 keys now take 6 months (each rests on a step); among the ten review-only keys the three `response|*` (statuses, price_presence, quote_id_presence) are due 2027-02-06 and lapse 2027-02-07; the other seven stay at 12 months (2027-08-06 / 2027-08-07). On a tie at 12 months the kind shown is the first named alphabetically, so shipper_id|present now shows `business_entity` (was `capability`). J-F: 22 keys at 6 months (the 21 product keys still at 6).

Deterministic record (KG_STORE=rdflib, pinned venv, CPython 3.12): CargoQuote 0 differing leaves over 7 scenarios; J-F 0 over 6. Unchanged; nothing re-recorded.

Gate as of 2027-02-07 (rdflib, exit, verdict, lapsed assertions):
- S1: 0 QUALIFIED; 3 keys below verified (response|price_presence, response|quote_id_presence, response|statuses); 5 lapsed
- S2: 1 BLOCKED (QuoteAPI|on_screening_outage declared_gap, response|hold_presence absent); 3 lapsed (price_presence, quote_id_presence)
- S3: 0 QUALIFIED; 7 below verified, 13 flagged; 5 lapsed
- S4: 1 BLOCKED (QuoteAPI|on_screening_outage disputed); 5 lapsed
- S5: 1 BLOCKED (as S2); 3 lapsed
- S6: 0 QUALIFIED; 3 below verified (the three response keys); 5 lapsed
- S7: 1 BLOCKED (36 of 36 below verified); 0 lapsed
As of 2027-02-06 and as of the record: S1 PROCEED, S2 BLOCKED, S3 QUALIFIED, S4 BLOCKED, S5 BLOCKED, S6 PROCEED, S7 BLOCKED, none lapsed. As of 2027-09-01 S1 and S6 (both stage-2 gates) BLOCKED with 19 lapsed assertions on 10 keys: seven on 2027-08-07 at 12 months, three on 2027-02-07 at 6.

CI expectations moved with the cadence: harness.yml S1 `--as-of 2027-02-06 --baseline record` = 0, `2027-02-07` = 0, `2027-02-07 --baseline record` = 1 (was 2027-08-06 = 0); demo.yml tag v0.2.7 and the as-of steps take each lapse's day and months by key. Both suites 316/316 (CargoQuote, J-F); harness.yml gate block run locally, exit 0; demo.yml task-0076/0086 snippets run against a local as-of run, pass.

AC #2 was checked as of the record's `as_of`, 2026-10-30 (subjects/cargo_quote/subject.toml `[record] as_of`); the "2026-08-06" in its wording is the kit's review date, an error in the brief the coordinator confirmed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Vendored ieam-register v0.2.7 (2b9e093) with tools/vendor_register.py: decision 0012 (the realiser walk, impact.py `--walk realisers`) and decision 0013 (review months for step, touchpoint, module, business_entity). The deterministic record is unchanged on both subjects (rdflib; 0 differing leaves). The three CargoQuote `response|*` review-only keys now lapse at six months (2027-02-07); gate verdicts S1-S7 as of 2027-02-07 in the notes. Tests and CI steps that pinned v0.2.6 or a uniform 12 months follow the register. Tasks 0081 and 0087 closed. Follow-up proposed to the coordinator: offer the realiser walk on the page's impact view.
<!-- SECTION:FINAL_SUMMARY:END -->
