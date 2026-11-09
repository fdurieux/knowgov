---
id: TASK-0271
title: >-
  code_map shapes are checked, and rules.compatible compares fields exactly
  (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 265000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`code_map.toml` shapes are not checked:
- `[code] include` given as a string is split into characters (`list("**/*.md")`), so `reference_impl.py` reads as code.
- `[code]` as a string, `root` as an int, or `[[map]]` as a table give AttributeError or TypeError. trace exits 2 with "the store did not answer"; upward exits 1.

`rules.compatible` compares fields as strings:
- "a=1" against "a=1.0" is a conflict, while "1" against "1.0" is equal: task-0243's rule is not applied per field.
- "a=1;b=2;a=3" against "a=3;b=2" is equal: a duplicate field, where the last one wins.

These are fix-only.

Source: group 3 F5 and F11, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `code_map.py` checks `code_map.toml`'s shapes and refuses a wrong one by name (exit 2), and `check_instance` reports them.
- [ ] #2 `rules.compatible` compares numeric fields with task-0243's exact comparison, and refuses or flags a duplicate field, with tests for the three cases.
- [ ] #3 R-CONFLICT ids (`check_conflict_ids`) and the record are unchanged.
<!-- AC:END -->
