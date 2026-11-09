---
id: TASK-0270
title: >-
  proposal_impact validates its overlay: types, exceptions and duplicates
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
ordinal: 264000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Malformed overlays crash or pass:
- `links[].owner` given as a list, `reused[].id` as a list, or `links[].rationale` as an int each crash with a traceback (exit 1; the MCP says "could not answer: TypeError").
- `links[].id` or `title` given as an int exits 0 with a report that is invalid against `proposal-impact`.

Overlay exceptions are not checked:
- a rule of "C9", null or "c4" is accepted;
- so is a scope that names no node;
- duplicate exception ids are accepted, while links refuse theirs;
- `expires = 20270601` is coerced to a date, and a TOML datetime is truncated to a date.

A duplicate reused entry (`{CAP-0003 as_is}`, then `{CAP-0003 changed}`) drops the second. That also drops the owner approval which a changed reused node requires, a weaker policy.

These are fix-only.

Source: group 3 F1, F2, F3 and F4, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every overlay field is type-checked. A malformed overlay is a refusal (exit 2, or an MCP isError naming the field), never a traceback or a report invalid against its schema.
- [ ] #2 Exception rule ids are checked against the register's rules and scopes against its nodes, ids are unique, and `expires` is a TOML date.
- [ ] #3 A duplicate reused id is refused.
- [ ] #4 The doc-0017 fixture, `check_proposal_branch` and the record are unchanged.
<!-- AC:END -->
