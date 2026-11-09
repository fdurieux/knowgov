---
id: TASK-0286
title: >-
  gate_cli --baseline FILE given a deterministic.json is held to the run:
  scenario, task, stage and subject (decision-0033)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T15:37:00Z'
updated_date: '2026-11-09T16:52:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
  - backlog/decisions/decision-0033
priority: high
ordinal: 279000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0258 holds a gate-report baseline to the run. A deterministic.json is not, despite its own `scenario` field. All of these are accepted:
- `gate_cli --subject subjects/cargo_quote --as-of record --scenario S2 --baseline subjects/cargo_quote/vendor/kg_experiment/results/S5/deterministic.json` exits 0;
- the same with J-F's `record/D5/deterministic.json` exits 1, a "regression" against J-F's keys;
- `--task design` with S2's deterministic.json exits 0, though the record is codegen's;
- `--stage 2` with a stage-1 file is accepted.

Group 3 found the same gap, and a second form: a JSON with `tool` removed and a `D6_gate` object added bypasses every check, exit 0. `--scenario S1 --baseline …/results/S2/deterministic.json` exits 0; `--task design` with S1's own file reads as a regression, exit 1, where `--baseline record` refuses a non-codegen task.

Fix-only, the same flag: a v3 report whose `levels` holds a non-level value (`{"shipper_id|present":"bogus"}`) passes the schema, then exits 2 as "the store did not answer: ValueError".

Contract-bearing: it finishes task-0258's change on one input form of the same flag. Source: the bounded re-probe (decision-0032 point 4, task-0256), group 1 at main 9861953 (1(a), 1(b)) and group 3 (3(a), 3(b)).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A deterministic.json baseline is held to the run's scenario, to task `codegen` (the record's class) and stage 1, or to what the file declares if it names them, and must sit under this subject's own record or results tree. Each refusal exits 2 naming what differs.
- [x] #2 A file that is neither a gate report nor the record's deterministic.json, identified by its whole shape and not one key, is refused with exit 2. The `D6_gate` bypass is a test.
- [x] #3 Each `levels` value is checked against the gate's levels, and a bad one exits 2 naming the field.
- [x] #4 Every reproduction in the description is a test. The record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate_cli.check_record_baseline: a deterministic.json baseline's whole shape first (_record_shape: every record's top-level parts, D6_gate's fields with a verdict of the gate, gate keys each with a level), then the subject's own record tree, its scenario the run's, its task its D6_gate's (codegen) and stage 1, unless the file names them.
2. _levels_known for a report's levels and a record's gate keys.
3. Tests from both groups' reproductions; CHANGELOG under Unreleased, Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence: tests/test_baseline_record_identity.py, 9 tests, all pass; on the old code each reproduction is accepted (the forged D6_gate file too, on 2435372). The four CLI reproductions exit 2 naming the reason; S2 against its own record and --baseline record exit 0. Record unmoved: comparator 0 diffs on CargoQuote S1-S7 and J-F (6); round trip rdflib on both subjects; check_mcp_server on both; check_gate_after_change 0; complexity --check holds. Suites on 661094b: bare 963/1023, J-F bare 962/1023, pinned 1021/1023, J-F pinned 1018/1023, 0 failed; bare 966/1026 after the merge of main.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
gate_cli --baseline FILE now holds a deterministic.json to the run as task-0258 holds a report: the record's whole structure (a report with its tool removed and a D6_gate added is neither), this subject's own record tree, the run's scenario, its own task (codegen) and stage 1; a level off the gate's ladder, in a report or a record, is named. Each refusal exits 2 naming the file and what differs. The record's own file for the same run reads as before; the record does not move.
<!-- SECTION:FINAL_SUMMARY:END -->
