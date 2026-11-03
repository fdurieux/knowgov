---
id: TASK-0049
title: The gate command brings in an artefact's later version
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T23:28:00Z'
labels:
  - gate
milestone: m-7
dependencies:
  - TASK-0048
priority: medium
type: feature
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 5: gate_cli.py loads stage 1 only, so it never sees a changed document (S6's stage 2). Add an option that loads a scenario's later version (or a named changed artefact) the way run.py's stage2 does, so the command reports invalidations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 gate_cli.py --stage 2 (or an equivalent option) reproduces run.py's stage 2 for S6: four invalidated statements, BLOCKED before re-verification
- [x] #2 The JSON report names the version loaded
- [x] #3 harness.yml runs it on S6
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Split run.py's stage2 into harness/change.py: apply_change (derived, re-ingest, R-STALE, R-STRUCT) and reverify; run.stage2 composes them, record unchanged (comparator).
2. gate_cli.py --stage 2 [--reverify]: stage 1, then apply_change with the subject record's derived output, optionally reverify; exit 2 on an incoherent ask.
3. Report: version (the version loaded) and change (artefact, invalidated, reverified, derived), additive in schema v2.
4. Shrink tools/check_gate_after_change.py to three gate_cli runs held to the scored record; harness.yml runs --stage 2 on S6.
5. Docs: demo/README.md, docs/guide.md. CHANGELOG: test_release.py forbids an Unreleased top section, so noted in the PR instead.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/change.py shared by run.py and gate_cli.py; comparator identical on rdflib (7 scenarios, 0 differing leaves). gate_cli --scenario S6 --stage 2 (rdflib): BLOCKED on P2|threshold, P2|surcharge; change.invalidated = the record's four (A:dt:P2|surcharge@v1, A:dt:P2|threshold@v1, A:dt:P3|order@v1, A:dt:worked_example|price@v1); version v2; exit 1. --stage 2 --reverify: PROCEED, exit 1, blocker derived:S1:G:run1 alone. Stage 1: PROCEED, v1, exit 0. version and change added to schema v2 as optional properties (a report without them still validates). CHANGELOG: tests/test_release.py holds the top section to VERSION, so no ## Unreleased; left to the release PR.

CI on ec73f68 green: tests, rdflib (gate step: --scenario S6 --stage 2 exits 1, the three refusals exit 2; check_gate_after_change.py), stack (the same script on Neo4j). Coordinator: no CHANGELOG entry; the 0.2.0 release PR records --stage/--reverify and the report's version/change. #94 (task-0056) moves run()'s tail into evaluate(): whichever merges second routes --stage through it.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
gate_cli.py --stage 2 [--reverify] brings in a scenario's later version through harness/change.py, the two steps run.py's stage2 now composes (record unchanged, comparator 0 differing leaves). S6 --stage 2: v2, the record's four invalidated statements, BLOCKED, exit 1; --reverify: PROCEED, exit 1 on derived:S1:G:run1. The report names version and change (additive in schema v2). tools/check_gate_after_change.py is three runs of the command held to the scored record; harness.yml runs --stage 2 on S6. Follow-up: CHANGELOG in the 0.2.0 release PR.
<!-- SECTION:FINAL_SUMMARY:END -->
