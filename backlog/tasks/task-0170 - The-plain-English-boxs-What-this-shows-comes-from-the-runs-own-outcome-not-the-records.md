---
id: TASK-0170
title: >-
  The plain-English box's 'What this shows' comes from the run's own outcome,
  not the record's
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T12:34:00Z'
updated_date: '2026-11-06T12:35:00Z'
labels:
  - demo
dependencies: []
priority: medium
ordinal: 172000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Reported by the arms-host session from the maintainer's EC2 run and relayed by the coordinating session. After an arms run whose model calls failed (a 401: decisions [None], code [False]), S1's plain-English box still ended 'What this shows: ... both arms wrote working code', which is the record's sentence. demo/app/views.py narrative() printed the scenario's 'plain' sentence for every source that had arm runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The record, and a source whose every arm run has an outcome the record's same arm had, with no failed call, end with the record's sentence
- [x] #2 A run whose model calls all failed says so plainly, with the first error quoted as data, and never the record's sentence
- [x] #3 A run that did not reproduce the record (one arm's calls failed, or code that failed oracle scenarios) says what happened and that the record's conclusion does not apply
- [x] #4 The deterministic source (no arm) and the replay (the record) are unchanged; the new sentences keep to the glossary and the 20-word limit
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence.
- demo/app/views.py: the narrative's last word is now _conclusion().
  - reproduces_record() is true for the record, and for a source with no failed call in which each arm run's outcome matches some run of the record's same arm. The outcome compared is the decision, the code written, whether the code passed every oracle scenario, and the planted targets failed.
  - Otherwise the box says what happened: every call failed (the first error quoted as data), one arm's calls failed, or code that failed oracle scenarios. It then says the record's conclusion does not apply.
- Every record source with arms reproduces, S6's rerun included.
- tests/test_what_this_shows.py covers:
  - the record, and a run copied from the record's run 1 (reproduces);
  - a run whose calls all failed with a 401;
  - one arm failed and the other's code at 9/11;
  - a deterministic run, and every scenario's replay (unchanged);
  - the new sentences against the glossary and the 20-word limit.
- Suite: stdlib 608/629, 21 skipped, 0 failed; J-F 607/629, 22 skipped, 0 failed; with the pins and KG_TEST_REQUIRE=rdflib,node 628/629, 1 skipped, 0 failed. The diff is confined to the box (views.py narrative), as the coordinator asked, since a parallel session is editing the page.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The plain-English box's 'What this shows' now speaks for the source on screen. The record's sentence appears only for the record, and for a run whose every arm outcome the record also had and whose calls all succeeded. A run whose model calls failed says so, quotes the first error and says the record's conclusion does not apply. A run that did not reproduce the record names what happened per arm. Deterministic runs and the replay are unchanged. Tests cover the failed, the partly failed, the reproducing, the deterministic and the replay cases, plus the glossary and length limits.
<!-- SECTION:FINAL_SUMMARY:END -->
