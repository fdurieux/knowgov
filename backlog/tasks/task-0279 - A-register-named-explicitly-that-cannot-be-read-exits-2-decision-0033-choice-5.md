---
id: TASK-0279
title: >-
  A register named explicitly that cannot be read exits 2 (decision-0033 choice
  5)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-09T10:10:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/register_impact.py: unreadable(root, tools), named(), require(root, by, tools), require_named(); RegisterUnreadable, an ImpactError.
2. check_subject: --register or KG_REGISTER unreadable exits 2 naming it; none named keeps the unchecked note.
3. The other readers: register_nodes, upward, proposal_impact (and --register-branch), gate_cli (KG_REGISTER, --register-previous) exit 2 before a store opens; the MCP reader refuses to start. New branches in helpers, so the complexity ratchet holds.
4. Docs: instance/README.md, subjects/README.md, check_subject's docstring and --register help. tests/test_named_register.py. CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->
