---
id: TASK-0086
title: Lapsed reviews on S6's stage-2 gate panels
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T01:31:00Z'
updated_date: '2026-11-04T02:59:00Z'
labels:
  - page
milestone: m-5
dependencies:
  - TASK-0076
priority: low
ordinal: 90000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0076 shows the as-of date and lapsed reviews on the gate panel; S6's stage-2 (after the change) panels do not yet show them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 S6's stage-2 gate panels list lapsed reviews as the stage-1 panel does
- [x] #2 The stack job asserts it on S6 as of a date after 2027-08-07
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. views.py: one _gate_lines helper for the stage-1 gate box and both stage-2 gate boxes (verdict, as of, N reviews lapsed on K keys, why); stage-2 gate colours from their verdict, not fixed.
2. Both stage-2 gate panels get _currency_section, as stage 1's.
3. Narrative: after re-verification, name the lapsed reviews it did not renew.
4. tests/test_page_as_of.py: S6 run folder with lapses, the record's S6, the stack step.
5. demo.yml: S6 through the app as of 2027-09-01, both stage-2 gates list ten keys lapsed on 2027-08-07 at 12 months.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Run data already carried lapsed in both stage-2 gate summaries (run.py gate_summary keeps it); only the view dropped it. The fixed colour of gate_after (ok) was wrong once reviews lapse: as of 2027-09-01 it is BLOCKED, so both colours now come from the verdict (the record's S6 keeps bad/ok).
Proven: tests/run_tests.py 261/261 plain and with KG_SUBJECT=subjects/jef_data_load; the new demo.yml step's script run against demo/app/server.py on rdflib and on Neo4j 5.26.0 community (Java 21): S6 as of 2027-09-01, stage 2 BLOCKED then BLOCKED, reviews on 10 keys lapsed on 2027-08-07 in both; the record none.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
S6's stage-2 gate boxes and panels, before and after re-verification, name the as-of date and list each lapsed review as stage 1's do (shared _gate_lines and _currency_section); their colours follow their verdict; the narrative says re-verification renewed none of the lapsed reviews. tests/test_page_as_of.py holds it on a run folder and on the record; the stack job runs S6 through the app as of 2027-09-01 and asserts both panels. Proven locally on rdflib and Neo4j 5.26.
<!-- SECTION:FINAL_SUMMARY:END -->
