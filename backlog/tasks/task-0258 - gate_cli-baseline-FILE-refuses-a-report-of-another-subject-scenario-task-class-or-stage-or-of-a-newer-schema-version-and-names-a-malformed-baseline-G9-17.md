---
id: TASK-0258
title: >-
  gate_cli --baseline FILE refuses a report of another subject, scenario, task
  class or stage, or of a newer schema version, and names a malformed baseline
  (G9-17)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T10:55:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 252000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The flag's documentation reads: "an earlier report of this command (at stage 2, a stage-2 report)". `baseline_of` checks only the report's shape, so all of these are accepted:
- A BLOCKED S2 exits 0 against minimal S0's report, against S2's design report, and against a hand-written `{"tool":"knowgov gate","verdict":"BLOCKED"}`.
- A stage-1 report is read at stage 2.
- A baseline with `schema_version` 99 is read.

A malformed field (verdict "FOO", a bad level, `levels` given as a list) exits 2 as "the store did not answer: ValueError". A baseline without `levels` never trips the key ratchet.

The finding is contract-bearing because the flag gains exit-2 cases; the fix keeps the documented promise.

Source: group 1 C2 and F4, and group 3 CB4 and F9, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A report baseline whose subject, scenario, task or stage differs from the run's exits 2, naming the field and both values.
- [x] #2 A report baseline with a `schema_version` above the current one exits 2, under decision-0023's rule. Versions 1 to 3 read as they do today.
- [x] #3 A report baseline is validated against `gate-report.schema.json` for its version before any comparison. A failure exits 2 naming the file and the first error, never "the store did not answer".
- [x] #4 `--baseline record` and `deterministic.json` baselines read as they do today, and the record does not move.
- [x] #5 Wherever the MCP reader's `gate_verdict` `baseline` argument reads a report, it applies the same checks.
- [x] #6 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate_cli.check_report_baseline: a report baseline's schema_version a whole number, above 3 refused (decision-0023); validated against the gate-report schema of its own version (v1, v2 frozen from e181138 and 4c7fcb0 beside the current); its subject, scenario, task and stage (2 when it carries a change) the run's.
2. _read_baseline runs it for a FILE baseline before baseline_of; record and deterministic.json unchanged.
3. harness.yml's S2-against-S1 step expects the refusal; an S1-against-its-own step expects 0.
4. Tests from the reproductions; CHANGELOG under Unreleased, Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence on #423 (merged with main through 4d3140b): tests/test_baseline_identity.py, 8 tests, all pass; on the old code every reproduction is accepted. The harness.yml gate step reproduced locally: S2 --baseline record 0; S1 against its own report 0; S2 against S1's report 2, naming scenario S1 against S2. Comparator 0 diffs on CargoQuote S1-S7 and J-F (6); check_round_trip --chain rdflib,rdflib on both subjects; check_mcp_server on both subjects; check_gate_after_change 0; complexity --check holds with no raise. Suites: bare 887/944, pinned 942/944 on the merged head; J-F bare 880/938, J-F pinned 933/938 before it; 0 failed. AC5: the MCP reader's gate_verdict serves none or record only, never a report path; a test pins it.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
gate_cli --baseline FILE now holds a gate report to the flag's own promise before any store is opened: a schema_version above 3 is refused under decision-0023, the report is validated against the gate-report schema of its own version (versions 1 and 2 frozen from the commits that last wrote them, beside the current), and a report of another subject, scenario, task class or stage is refused; each exit 2 naming the file and what differs, never "the store did not answer". --baseline record and a deterministic.json read as before; the MCP reader still serves no report baseline. harness.yml's S2-against-S1 line now expects the refusal. The record does not move.
<!-- SECTION:FINAL_SUMMARY:END -->
