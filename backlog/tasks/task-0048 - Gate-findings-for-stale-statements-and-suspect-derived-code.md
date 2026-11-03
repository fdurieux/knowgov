---
id: TASK-0048
title: Gate findings for stale statements and suspect derived code
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T23:08:00Z'
labels:
  - gate
milestone: m-7
dependencies: []
references:
  - backlog/docs/doc-0011
priority: high
type: bug
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 3, measured: harness/gate_cli.py reports stale and suspect_derived as counts only, so they never move the exit code; after S6's re-verification the gate reads PROCEED while derived:S1:G:run1 is still suspect. Make both finding classes on the contract's ladder and raise the report schema version.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Stale statements on required keys and suspect derived outputs appear as findings with a severity, and count toward --fail-on
- [x] #2 harness/schemas/gate-report.schema.json moves to version 2, with the change documented; tests validate every record scenario against it
- [x] #3 A gate run after S6's stage 2 no longer exits 0 while a derived output it names is suspect, shown in harness.yml
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate_cli.findings: add two classes from gate.resolve's own lists, each with kind and ref: a stale statement on a required key (major when no verified or approved successor replaces it, the key's own finding carries the blocker; info when superseded, the record of the change) and a suspect derived output (blocker: it may not be reused as it is). Both count toward --fail-on through at_or_above; the verdict stays the gate's (the record pins it).
2. Report v2: schema_version 2; findings gain kind (key, task, stale, suspect_derived), ref and related; stale and suspect_derived become id lists instead of counts; the baseline ratchet also fails on a derived output suspect now that the baseline did not hold suspect (new_suspect). Schema description and demo README, docs/guide.md say what changed from v1.
3. Tests: every CargoQuote record scenario (stage 1, and S6's stage 2 before and after re-verification) and every jef_data_load record scenario validates against v2; S6 after re-verification: PROCEED, a blocker on derived:S1:G:run1, exit 1; stale findings info.
4. Acceptance in harness.yml: tools/check_gate_after_change.py reproduces S6's stage 2 through the store port (gate_cli._load, then run.stage2 with the record's S1 run1_G.py as the derived input) into a KG_RDFLIB_FILE, then runs gate_cli.py --scenario S6 --no-load on it and asserts exit 1, the blocker naming derived:S1:G:run1. No --stage option: that is TASK-0049.
5. Run the tests (both subjects), the comparator S1-S7 on rdflib, the harness.yml gate steps locally; PR, wait for the matrix, merge on green.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented as planned. gate_cli.findings reads gate.resolve's own stale and suspect_derived lists (gate.py untouched, so the record and the comparator are unchanged: S1-S7 on rdflib, 0 differing leaves). Severities: suspect derived output blocker; stale statement info when a verified or approved successor replaces it, major when none does (that key's own finding is already the blocker). The verdict stays the gate's: after S6's re-verification it reads PROCEED and the command exits 1.
Report v2: findings gain kind, ref, related; stale and suspect_derived are id lists; baseline gains new_suspect (a derived output suspect that the baseline did not hold is a regression, else --baseline record would still pass the CI hook). A v1 report still reads as a baseline. Documented in the schema's description, demo/README.md, docs/guide.md section 9 and CLAUDE.md.
Stage 2: no --stage option (TASK-0049's scope). tools/check_gate_after_change.py reproduces S6's stage 2 through the store port (gate_cli._load, the record's S1/run1_G.py registered as derived with the stage-1 gate's statements, run.stage2) into KG_RDFLIB_FILE, then runs gate_cli.py --scenario S6 --no-load: PROCEED, exit 1, blocker derived:S1:G:run1; S6 stage 1 alone exits 0. harness.yml runs it on rdflib, demo.yml on Neo4j.
Tests: test_gate_cli validates every CargoQuote record scenario, the scored S6's stage 2 before and after re-verification, and every jef_data_load record scenario against v2. Local: 140/140 with either subject; harness.yml's gate steps with the same exit codes as before.

Verified on PR #90's matrix (tests, rdflib, stack all green at fcb44a5). AC1: tests/test_gate_cli.py, scored S6 after re-verification: blocker derived:S1:G:run1, 3 stale at info, exit 1 at blocker; before re-verification stale at major/info by successor; counts toward --fail-on (info threshold fails the stale-only report). AC2: schema const 2, change in its description, demo/README.md, docs/guide.md; tests validate every CargoQuote record scenario (and S6 stage 2 before/after) and every jef_data_load scenario; harness.yml asserts the S1 report is v2 and valid. AC3: harness.yml step 'The gate after S6's change (task-0048)': 'exit 1: gate_cli.py --scenario S6 --no-load, after the change: PROCEED, blocker derived:S1:G:run1'; the stack job does the same on Neo4j. Comparator S1-S7 on rdflib: 0 differing leaves.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
gate_cli.py now turns gate.resolve's stale and suspect_derived lists into findings on the contract's ladder: a suspect derived output is a blocker; a stale statement on a required key is major without a verified or approved successor, info with one. Both count toward --fail-on, and the baseline ratchet treats a newly suspect derived output as a regression. The verdict stays the gate's (gate.py untouched; the comparator still reports 0 differing leaves). The report schema moved to version 2 (findings gain kind/ref/related; stale and suspect_derived are id lists; baseline gains new_suspect), documented in the schema, demo/README.md, docs/guide.md and CLAUDE.md. tools/check_gate_after_change.py reproduces S6's stage 2 through the store and shows gate_cli.py --no-load exiting 1 (PROCEED, blocker derived:S1:G:run1); harness.yml runs it on rdflib, the stack job on Neo4j. Follow-up: TASK-0049 adds loading a later version to the command itself; the script can then shrink to that option.
<!-- SECTION:FINAL_SUMMARY:END -->
