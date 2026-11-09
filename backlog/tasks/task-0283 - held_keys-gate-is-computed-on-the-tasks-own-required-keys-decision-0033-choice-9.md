---
id: TASK-0283
title: >-
  held_keys' gate is computed on the task's own required keys (decision-0033
  choice 9)
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
ordinal: 276000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`held_keys`' `gate` gates every held key (93 on CargoQuote S1) under the task's bar and calls them "required". It reads "codegen BLOCKED" where `gate_verdict` gives codegen PROCEED.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 9(a), the field is computed on the task's own required keys, so it equals `gate_verdict`'s verdict on the same store, task and `as_of`.

Source: validation-pass group 2 F5, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `held_keys`' `gate` equals `gate_verdict`'s verdict and `why` for the same store, task and `as_of`, on CargoQuote S1, S4 and S6 under `codegen` and `design`, and on J-F C.
- [ ] #2 The tool's description and the held-keys schema's wording say what the field is.
- [ ] #3 `check_mcp_server` holds it, and the record does not move.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
