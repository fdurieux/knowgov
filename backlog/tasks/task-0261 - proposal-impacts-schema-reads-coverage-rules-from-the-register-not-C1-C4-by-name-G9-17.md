---
id: TASK-0261
title: >-
  proposal-impact's schema reads coverage rules from the register, not C1-C4 by
  name (G9-17)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T11:02:00Z'
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
- [x] #1 `coverage.before` and `coverage.after` admit any rule id as a key, through `additionalProperties` set to the per-rule cell. `new_gaps[].rule` is a string in the register's rule-id form. A report from a fixture register that defines C5 validates.
- [x] #2 Today's reports still validate, on the doc-0017 fixture and on #402's slices fixture, and the record does not move.
- [x] #3 The register view's coverage reader (task-0241) is checked the same way, or the task records that its output has no schema.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. proposal-impact.schema.json: coverage.before and after keyed by $defs.rule_id (propertyNames, ^C[0-9]+$) with additionalProperties the coverage cell; new_gaps[].rule a rule_id; the schema names no rule. 2. schema_check gains pattern (ECMA's final $ as \Z) and propertyNames, split into _check_value and _check_object for the complexity ratchet. 3. Tests: a register whose checker defines C5 validates; the rule-id form and the cell are held; the register view's reader follows a C5 checker (its output has no schema). 4. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
proposal-impact.schema.json: $defs.rule_id (string, ^C[0-9]+$) and $defs.coverage_cell; coverage.before and after are {propertyNames: rule_id, additionalProperties: coverage_cell}; new_gaps[].rule is a rule_id; the schema names no rule (a test holds that). Version 1, a widening: every earlier report validates. harness/schema_check.py gains pattern, read as ECMA-262 does (a final $ as \Z, so 'C5\n' is refused; the coordinator's heads-up from #422's builder) and propertyNames; _check split into _check_value and _check_object for task-0251's ratchet (41 -> 14, baseline tightened); the refusal test's example keyword is now maxLength. A fixture register defining C5 (the vendored copy, its checker given a C5 that repeats C4) yields a valid report on task-0241's C4 fixture, new gaps C4 and C5 on PROC-0011. Today's reports validate: the doc-0017 worked example and #402's slices cases in tests/test_proposal_impact.py, and tools/check_proposal_branch.py on both fixtures; the record does not move. AC 3: the register view's output has no schema; its coverage reader (task-0241) follows a C5 checker, by test.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
proposal-impact's schema reads coverage by the register's rule ids and names none (group 3 CB2): before and after are keyed by rule_id with the coverage cell as additionalProperties, and a new gap's rule is a rule_id. A register defining C5 yields a valid report; today's doc-0017 and slices reports still validate; the register view's output has no schema and its reader follows the checker's rules. schema_check gains pattern (ECMA's final $) and propertyNames, split for the complexity ratchet. The record held. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
