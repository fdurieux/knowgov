---
id: TASK-0257
title: >-
  The subject-check schema names every rule its checker emits: require-approved,
  rationale and attestation (G9-17)
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
- [ ] #1 `finding.rule`'s enum includes `require-approved`, `rationale` and `attestation`, and these reports validate:
- `subjects/jef_data_load`;
- the example instance;
- a manifest with `require_approved = "yes"` and `rationale = 5`.
- [ ] #2 A test runs every rule code that `check_subject.py` and `task_policy.problems` can emit through the schema, so a new code without its enum entry fails the suite.
- [ ] #3 `CHANGELOG.md`'s Unreleased section names the widening under its contract heading.
<!-- AC:END -->
