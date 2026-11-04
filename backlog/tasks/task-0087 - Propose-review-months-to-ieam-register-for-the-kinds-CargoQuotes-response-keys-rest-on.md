---
id: TASK-0087
title: >-
  Propose review months to ieam-register for the kinds CargoQuote's response
  keys rest on
status: Done
assignee: []
created_date: '2026-11-04T01:31:00Z'
updated_date: '2026-11-04T12:19:00Z'
labels:
  - register
milestone: m-4
dependencies:
  - TASK-0068
priority: low
ordinal: 91000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0076: three CargoQuote keys (response|*) name no kind with registered review months in lifecycle.toml, so decision-0005's lapse falls back to a default. The months are the register's to set.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An ieam-register proposal names the kinds and the months, with the effect on CargoQuote as of 2027-08-07
- [x] #2 Nothing in knowgov changes until approved and vendored
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proposed and accepted as ieam-register #19 (decision 0013: `[review.kinds]` step 6, touchpoint 6, module 12, business_entity 12); #22 the follow-up merge carrying it at v0.2.7 (2b9e093), vendored here by task-0109. Effect on CargoQuote: the three `response|*` keys rest on a step, six months, so reviewed 2026-08-06 they lapse on 2027-02-07, not 2027-08-07; S1 as of 2027-02-07 is QUALIFIED (exit 0, 1 with `--baseline record`), as of 2027-08-07 BLOCKED. The record as of 2026-10-30 unchanged (comparator 0 differing).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The register now names review months for the kinds the response keys rest on (ieam-register #19, decision 0013; carried at v0.2.7 with #22). Vendored by task-0109; the three response keys lapse at six months.
<!-- SECTION:FINAL_SUMMARY:END -->
