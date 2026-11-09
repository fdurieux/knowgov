---
id: TASK-0258
title: >-
  gate_cli --baseline FILE refuses a report of another subject, scenario, task
  class or stage, or of a newer schema version, and names a malformed baseline
  (G9-17)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
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
- [ ] #1 A report baseline whose subject, scenario, task or stage differs from the run's exits 2, naming the field and both values.
- [ ] #2 A report baseline with a `schema_version` above the current one exits 2, under decision-0023's rule. Versions 1 to 3 read as they do today.
- [ ] #3 A report baseline is validated against `gate-report.schema.json` for its version before any comparison. A failure exits 2 naming the file and the first error, never "the store did not answer".
- [ ] #4 `--baseline record` and `deterministic.json` baselines read as they do today, and the record does not move.
- [ ] #5 Wherever the MCP reader's `gate_verdict` `baseline` argument reads a report, it applies the same checks.
- [ ] #6 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
