---
id: TASK-0279
title: >-
  A register named explicitly that cannot be read exits 2 (decision-0033 choice
  5)
status: To Do
assignee: []
created_date: '2026-11-09T10:10:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 272000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`check_subject --register DIR` with a DIR that does not exist, or a bad `KG_REGISTER`, gives one "unchecked" note and exits 0, as documented. A typo silently drops the register check.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 5(a), a register that is named (by a flag or by `KG_REGISTER`) and cannot be read exits 2, naming it. "Unchecked" stays for the case where no register is named.

Source: validation-pass group 1 C8, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `check_subject` exits 2 naming the path when a named register cannot be read, and keeps the unchecked note when none is named. The documentation says so.
- [ ] #2 The task lists every other reader that takes a register (`register_nodes`, `upward`, `proposal_impact`, `gate_cli --register-previous`, the MCP reader), and each follows the same rule, or the task records why not.
- [ ] #3 The record does not move.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
