---
id: TASK-0278
title: >-
  Task-class names: keys reserved and [a-z][a-z0-9_-]{0,31} required, by the
  checker and the runtime (decision-0033 choice 4)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-09T10:09:00Z'
updated_date: '2026-11-09T13:33:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 271000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`[tasks.keys]`, `[tasks.""]` and `[tasks."code gen"]` pass `check_subject` and `check_instance`. `keys` is the agent-chosen key set (doc-0014 C4), whose reports the hook refuses and which `knowgov-gate.sh` refuses as `KG_TASK`.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 4(a), `keys` is reserved, and a class name must match `[a-z][a-z0-9_-]{0,31}`. The checker and the runtime both refuse anything else.

Source: validation-pass group 1 C7, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `check_subject` and `check_instance` report an error for a class named `keys`, an empty name, or a name outside the pattern. The MCP `subject_check` reports the same.
- [ ] #2 The runtime refuses such a manifest with exit 2 naming the class, at every reader that loads task classes.
- [ ] #3 The public subjects (`codegen`, `design`) and the record are unchanged.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/task_policy.py: NAME [a-z][a-z0-9_-]{0,31}, RESERVED (keys); name_problem (code task-class); build raises TaskPolicyError on it before reading the table; table() quotes a name that is not a bare TOML key.
2. tools/check_subject.py: _class_name reports the problem per class, so check_instance and the MCP subject_check report it too; the subject-check schema's finding.rule gains task-class.
3. Every runtime reader loads task classes through tasks.TASKS, which runs build: no reader-by-reader change.
4. tests/test_task_class_names.py: names good and bad, the checker, the instance check, the MCP subject_check, gate_cli's exit 2; the public subjects clean. CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->
