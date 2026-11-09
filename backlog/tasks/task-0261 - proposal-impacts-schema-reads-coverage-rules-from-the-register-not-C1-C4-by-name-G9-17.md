---
id: TASK-0261
title: >-
  proposal-impact's schema reads coverage rules from the register, not C1-C4 by
  name (G9-17)
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
ordinal: 255000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0241 made `proposal_impact` read the register's `COVERAGE_RULES` ("a later rule needs no code here"). But `proposal-impact.schema.json` names C1 to C4 itself:
- `coverage.before` and `coverage.after` list them under `additionalProperties: false`;
- `new_gaps[].rule` is an enum of C1 to C4.

So a register defining C5 yields a report that is invalid against its own schema. v0.2.13 (decision-0028) defines C1 to C4 only, so today's reports validate.

The finding is contract-bearing because it changes the schema's shape.

Source: group 3 CB2, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `coverage.before` and `coverage.after` admit any rule id as a key, through `additionalProperties` set to the per-rule cell. `new_gaps[].rule` is a string in the register's rule-id form. A report from a fixture register that defines C5 validates.
- [ ] #2 Today's reports still validate, on the doc-0017 fixture and on #402's slices fixture, and the record does not move.
- [ ] #3 The register view's coverage reader (task-0241) is checked the same way, or the task records that its output has no schema.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
