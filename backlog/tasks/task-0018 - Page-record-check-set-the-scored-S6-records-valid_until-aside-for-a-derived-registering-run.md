---
id: TASK-0018
title: >-
  Page record check: set the scored S6 record's valid_until aside for a
  derived-registering run
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T16:56:00Z'
updated_date: '2026-11-01T17:00:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A deterministic S6 run that has S1/run1_G.py in its output folder registers the derived output, so the page's record_check (demo/app/views.py) reads it against the scored record results/S6 rather than d3check/S6. Three leaves differ, all stage2.gate_after_reverification.stale[*].verifications[*].valid_until: the record holds null, a re-run holds "v2" (r_stale ends the verification with the new tag). Reproduced with pumllint's original harness and comparator too, so it predates task-0001 and task-0002. Finding: the record is the artefact of a loader defect, by its own account. pumllint kg_experiment/PREREGISTRATION.md, run notes 2026-10-30, "a third harness defect": R-STALE set valid_until = v2, then the scored run's stage-2 verification loader re-merged the same Verification records (its match did not exclude invalidated assertions) and reset the field to null; the loader was fixed, D3 was re-established in results/d3check/S6 (valid_until = v2) and results/S6 was kept as the first run was. d3check/S6 has no Derived node (the deterministic branch passed none until 2026-11-01), so a derived-registering run has no record that is right on every leaf: the scored one is wrong on valid_until, the deterministic one lacks the Derived. Regenerating results/S6 would rewrite a frozen scored record against the record's own procedure (SHA256SUMS, the vendoring digest test), so the page sets the leaf aside instead, as it does the timestamps, and says so.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 record_check reads a derived-registering S6 run against the scored record (results/S6) and reports no differing leaf; valid_until is set aside in that comparison only, the view names it ("aside") and the narrative says it beside the timestamps
- [x] #2 The comparator's command line is unchanged: such a run against results/S6 still reports the three valid_until leaves, and the record compared with itself is identical on every leaf, valid_until included (tests/test_demo.py::test_compare_tool_finds_the_record_identical_to_itself keeps that meaning)
- [x] #3 The leaves set aside are subject data (scenarios.toml, beside deterministic_record) with the why written next to them and documented in subjects/README.md; nothing under demo/ names the subject or the scenario
- [x] #4 python tests/run_tests.py passes and a deterministic S6 run started through the page (POST /api/run) reports the record check identical against results/S6
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Thread an ignore_keys parameter through compare_deterministic.compare/_leaves/_strip, default none, CLI untouched. 2. scenarios.toml S6: scored_record_volatile = ["valid_until"] with the why as a TOML comment; subjects/README.md documents the key. 3. views.record_check passes it when the run is read against the scored record, returns "aside", the narrative says "timestamps and valid_until aside". 4. Tests: the CLI still shows the three leaves; record_check on a synthesised derived-registering run is identical; a run without the Derived still goes to d3check with nothing aside. 5. Full suite, then server.py with KG_STORE=rdflib, POST a deterministic S6, read /api/results/S6?source=demo-runs/<id>.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Finding: the scored record is wrong on that leaf, by its own account. pumllint kg_experiment/PREREGISTRATION.md, run notes 2026-10-30, "a third harness defect": R-STALE set valid_until = v2 on the ended verifications, then the scored run's stage-2 verification loader (load_verifications, whose match did not exclude invalidated assertions) re-merged the same Verification nodes and reset the field to null; the loader was fixed, D3 re-established in results/d3check/S6 (valid_until = "v2") and results/S6 kept as the first run was. So the scored run's gate_after_reverification.stale listing read valid_until after the loader had reset it, not before r_stale set it; the record captures the defective loader, and a re-run's "v2" is the correct value. results/rerun/S6 (the arms re-run with the corrected bundle) carries the same nulls: it predates the loader fix too. d3check/S6 has no Derived node (the deterministic branch passed none until 2026-11-01), so a derived-registering run has no record right on every leaf. Regeneration (option a) rejected: it would rewrite a frozen scored record (SHA256SUMS, the vendoring digest test) against the record's own procedure, which left results/S6 untouched and added d3check/S6.

Done (option b): compare_deterministic.compare() takes ignore_keys (threaded through _leaves/_strip; the CLI passes none); scenarios.toml S6 gains scored_record_volatile = ["valid_until"] with the why as a comment, documented in subjects/README.md; views.record_check passes it only when the run is read against the scored record, returns "aside", and the narrative says "timestamps and valid_until aside". Verification: tests/run_tests.py 57/57 (three tests cover the CLI still reporting the three leaves, the record identical to itself with valid_until read, record_check identical for a derived-registering run and still counting any other leaf, nothing aside against d3check/S6); a deterministic S6 started through the page (server.py on KG_STORE=rdflib, POST /api/run) read "identical on all 170 fields compared with results/S6, timestamps and valid_until aside" while the comparator CLI on the same run folder against results/S6 still exits 1 with the three leaves.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page read a derived-registering deterministic S6 against results/S6 and showed three valid_until leaves differing. The record holds null there because the scored run's stage-2 loader reset what R-STALE had set (pre-registration run notes, "a third harness defect"); d3check/S6 has the corrected value but no Derived node. The page now sets the leaves the subject manifest names (scored_record_volatile) aside against the scored record only, says so beside the timestamps, and the comparator's command line is unchanged. Risk: none to the record; a second subject declares its own list or none.
<!-- SECTION:FINAL_SUMMARY:END -->
