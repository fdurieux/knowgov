---
id: TASK-0076
title: The page shows the as-of date and the lapsed statements
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:53:00Z'
labels:
  - page
  - gate
milestone: m-5
dependencies:
  - TASK-0068
priority: low
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0068 added gate_cli --as-of and the lapsed finding (decision-0005); the page shows neither, so a viewer cannot see when a review falls due or what lapsed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The gate panel names the as-of date it read
- [x] #2 Lapsed verifications are listed with the date they lapsed and the kind's review months
- [x] #3 The stack job asserts both on S1 as of a date after 2027-08-07
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. cadence.lapse carries lapsed_on (valid_until + 1 day), months and kind (the register kind the key's months come from; kind_for).
2. run.py --as-of (record by default) threads the date into every resolve, so a run records as_of.
3. The app's POST /api/run takes as_of (YYYY-MM-DD, else 400) and passes --as-of; the menu has a Reviews as of date.
4. views: as_of_view (the run's as_of, else the subject's record date); gate box line 'as of DATE' and the lapse count; gate panel 'Review currency' section with the lapsed table; narrative sentences; a run not as of the record date is said not to be measured by it. Glossary: as-of date, lapsed.
5. tests/test_page_as_of.py; demo.yml step runs S1 through the app as of 2027-09-01 and asserts the page.
6. Prove on rdflib and Neo4j 5.26 locally.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Merged in #127 (e758654). The stack job's task-0076 step, green on the PR head 64dc555: S1 run through the app as of 2027-09-01 is BLOCKED, with 19 reviews on 10 keys lapsed on 2027-08-07 at 12 months; the record reads as of 2026-10-30 with none lapsed; a bad date gets a 400. Locally on rdflib and on Neo4j 5.26: the comparator shows 0 differences over 7 scenarios and the step's script passes against the app. The gate panel renders in Chromium. The kind column says 'default' for keys whose register kinds have no review months of their own (CargoQuote's response|*).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page shows when reviews fall due. cadence.lapse also returns lapsed_on, months and kind (kind_for). run.py --as-of (record by default) and the app's POST /api/run as_of, plus a menu date, name the date a run reads. views.as_of_view: the gate box shows 'as of DATE' and the lapse count; the gate panel's Review currency section lists each lapse (assertion, key, was, current until, lapsed on, review months, kind). The narrative names the date and says a run read as of another date is not measured against the record. Glossary: as-of date, lapsed. Proof: tests/test_page_as_of.py; a demo.yml stack step on S1 as of 2027-09-01; the comparator unchanged on both stores. Follow-up: task-0086 (S6 stage-2 panels).
<!-- SECTION:FINAL_SUMMARY:END -->
