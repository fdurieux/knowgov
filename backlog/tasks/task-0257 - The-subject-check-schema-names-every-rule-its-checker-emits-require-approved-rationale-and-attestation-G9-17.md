---
id: TASK-0257
title: >-
  The subject-check schema names every rule its checker emits: require-approved,
  rationale and attestation (G9-17)
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
ordinal: 251000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The validation pass found three rule codes that `tools/check_subject.py` emits and `harness/schemas/subject-check.schema.json`'s `finding.rule` enum lacks:
- `require-approved` and `rationale`, task-0242's `task_policy` codes;
- `attestation`, from `check_attestations`, task-0199.

The report on J-F's own `subject.toml`, on the example instance, and on a manifest with `require_approved = "yes"` fails its own schema. That holds for the CLI's `--json` and for the MCP `subject_check`.

The finding is contract-bearing because the schema's enum widens, additively.

Source: group 1 C1 and group 2 F3, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `finding.rule`'s enum includes `require-approved`, `rationale` and `attestation`, and these reports validate:
- `subjects/jef_data_load`;
- the example instance;
- a manifest with `require_approved = "yes"` and `rationale = 5`.
- [x] #2 A test runs every rule code that `check_subject.py` and `task_policy.problems` can emit through the schema, so a new code without its enum entry fails the suite.
- [x] #3 `CHANGELOG.md`'s Unreleased section names the widening under its contract heading.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/schemas/subject-check.schema.json: finding.rule gains require-approved, rationale and attestation (version 1, additive).
2. tests/test_subject_check_rules.py: read every rep.error/warning/note code from tools/check_subject.py's AST and every code literal from harness/task_policy.py; run them all through the schema; the one non-literal code must be task_policy's pass-through.
3. Validate the named reports: J-F, the example instance's subject reports, and a manifest with require_approved = "yes" and rationale = 5; also an attestation with no at.
4. CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The enum now lists 20 finding rules; the note enum already held all four note codes (map, yield, unyielded, attestation).
tests/test_subject_check_rules.py:
- test_every_rule_code_the_checker_can_emit_is_in_the_schema: AST, both files; a synthetic report with one finding per code validates.
- test_a_code_missing_from_the_enum_fails_the_schema.
- test_the_reports_the_validation_pass_named_validate: J-F, CargoQuote and minimal; minimal with require_approved = "yes" and rationale = 5, giving require-approved and rationale errors; minimal with [verification] authored and no at, giving an attestation error.
- test_the_example_instances_subject_reports_validate: every check_subject report check_instance carries.
Without the enum change, two of the four fail. On today's main, J-F's own report validates (it lists the Versions it attests); the manifest case reproduces the failure, and the MCP subject_check answers the same report, its outputSchema loaded from the same file.
Checks at 0a57437: run_tests 944/945 on the pins and 886/945 bare; the comparators show 0 differences; check_subject passes on both subjects. At c715316, merged with main: 950/951 on the pins and 892/951 bare.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The subject-check schema's finding.rule enum now names require-approved and rationale (task_policy's codes for a malformed [tasks.<class>] field) and attestation (an attestation with no day or no attester). tools/check_subject.py emitted all three, so a report carrying one failed its own schema, from the CLI's --json and from the MCP subject_check alike. Schema version 1, additive. tests/test_subject_check_rules.py reads every code the checker and task_policy.problems can emit from their source, and runs each through the schema, so a new code without its enum entry fails the suite. It also validates the reports the validation pass named: J-F, the example instance, and a manifest with require_approved = "yes" and rationale = 5. The record is unchanged. CHANGELOG: Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
