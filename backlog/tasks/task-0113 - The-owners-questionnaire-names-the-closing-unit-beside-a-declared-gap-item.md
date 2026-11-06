---
id: TASK-0113
title: The owner's questionnaire names the closing unit beside a declared-gap item
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T14:55:00Z'
updated_date: '2026-11-06T03:19:00Z'
labels:
  - gate
  - capture
milestone: m-8
dependencies:
  - TASK-0110
priority: low
type: task
ordinal: 113000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0110; chosen by the maintainer 2026-11-04. harness/capture.py's questionnaire lists a declared gap for the answering owner; it should also name the unit that closes it (the closer, from the declaration), so the owner knows who must close it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 S2's questionnaire for ORG-0002 names ORG-0004 as closing OD-1
- [x] #2 Ingest is unchanged; a questionnaire from before still ingests
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.questionnaires: capture.gap_closers over the result's declared_gaps (the gate finding's closer, task-0110); an item on a declared gap gains gap, closed_by, closed_by_name and a comment line; ingest untouched. 2. Tests: S2 with OD-1 for ORG-0002 names ORG-0004; the same answers ingest to the same capture with and without the fields. 3. CHANGELOG: a new Unreleased section, Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: no schema or golden pins the questionnaire; the change is additive in the item table (three fields and a comment before it). Evidence: tests/test_capture.py test_s2s_questionnaire_for_org_0002_names_org_0004_as_closing_od_1 (gap:declared:OD-1, ORG-0004, Compliance (stand-in); ORG-0001's questionnaire byte-equal; an item without a gap carries none) and test_ingest_is_unchanged_and_a_questionnaire_from_before_still_ingests (capture_toml equal with and without the fields). On the store: harness.yml's capture step locally (example instance, KG_STORE=rdflib, S2) writes closed_by = ORG-0004 on OD-1's item; check_answers reads only key, answer, nobody_knows, note. run_tests.py 535/551 stdlib (16 skipped), 550/551 with rdflib/pyshacl pins and KG_TEST_REQUIRE=rdflib (1 skipped), 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
harness/capture.py's questionnaire names the unit that closes a declared gap: an item on one carries gap, closed_by and closed_by_name from capture.gap_closers, the same unit the gate's key finding names in closer (task-0110), and a comment that an answer does not close it. S2's questionnaire for ORG-0002 names ORG-0004 as closing OD-1. Ingest is unchanged; a questionnaire written before still ingests to the same capture. CHANGELOG: a new Unreleased section, under Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
