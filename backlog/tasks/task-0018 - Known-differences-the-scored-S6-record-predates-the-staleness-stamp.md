---
id: TASK-0018
title: 'Known differences: the scored S6 record predates the staleness stamp'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T16:55:00Z'
updated_date: '2026-11-01T16:58:00Z'
labels:
  - comparator
  - record
milestone: m-1
dependencies: []
priority: medium
type: bug
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A deterministic S6 re-run that registers S1's derived output is compared by the page against the scored record results/S6, and three leaves differ: the ended verifications' valid_until is empty in the record and v2 in every re-run. Both scored folders (S6, rerun/S6) predate the staleness stamp; the record's own deterministic re-establishment (d3check/S6) carries v2. The record is pumllint's and frozen by the pre-registration; it is not regenerated and not edited. Instead the subject's scenario data names the known difference (the record folder, the leaf prefix, the field, why), the comparator strips that field on both sides when comparing against that folder and reports the known difference by its reason, and the page says so in words. Everything else stays strict. Decided with the maintainer on 2026-11-01.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 scenarios.toml for S6 names the known difference: the scored record folder, the leaf prefix, the field valid_until and the reason pointing at the pre-registration's run notes
- [x] #2 The comparator applies known differences only against the named record folder, reports each applied reason, and counts no difference for them; d3check stays strict
- [x] #3 A unit test shows d3check/S6 against results/S6 losing exactly the valid_until differences and no other
- [x] #4 The page's record check names the known difference in its sentence instead of counting fields as differing
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. scenarios.toml S6: [[scenario.known_differences]] with the record folders (S6, rerun/S6), the leaf prefix, the field valid_until and the reason. 2. The comparator takes known differences (the CLI reads them from the subject), applies them only against the named record folder by dropping the field under the prefix on both sides, and prints 'known: <why>'. 3. views.record_check passes the subject's known differences and the narrative names the reason instead of counting fields. 4. Tests on the real record and on a synthetic pair; a deterministic S6 through the page on Neo4j.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Both scored folders (S6, rerun/S6) carry no valid_until on the three ended verifications; d3check/S6 carries v2: the scored runs predate the staleness stamp. Implemented as the subject's [[scenario.known_differences]] (records, prefix, field, why); the comparator drops the field under the prefix on both sides against the named folders only, prints 'known: <why>', counts nothing; the CLI reads the subject's entries, the page passes them and its sentence names the reason. Proof: 55/55 tests (d3check against S6 loses exactly the three valid_until leaves and keeps the derived-node difference; a synthetic pair; the strict path untouched); S6 deterministic through the page on Neo4j: 179 leaves identical against results/S6, one difference recorded as the record's own and named in the sentence. The record is unchanged.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The three valid_until fields in which every S6 re-run differs from the scored record are now a recorded difference of the record's own, named in the subject's scenario data with its reason: the scored run predates the staleness stamp. The comparator applies it only against the scored folders and reports it by its reason; the page says so in words; the record's deterministic folder stays strict and the record itself is untouched. Verification: 55/55 tests, S6 through the page identical on 179 leaves with the known difference named.
<!-- SECTION:FINAL_SUMMARY:END -->
