---
id: TASK-0281
title: >-
  MCP arguments validated against each tool's inputSchema before dispatch
  (-32602), and the page's run body refuses unknown fields (decision-0033 choice
  7)
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
ordinal: 274000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
-32602 covers unknown argument names only. A type, enum, pattern or minimum violation comes back as an `isError` result. A falsy wrong value is coerced to the default: `scenario: ""` answers for the held scenario, which defeats the scenario guard; `walk: ""` reads as `dependants`; `arguments: []` reads as `{}`. The page's `POST /api/run` ignores unknown fields, so a body with `as-of` runs as of the record date. doc-0030 F6 and CLAUDE.md already say "an argument outside a tool's inputSchema → -32602".

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 7(a), every argument is validated before dispatch, and the run body refuses unknown fields.

Source: validation-pass group 2 F1 and F2, and group 3 CB3, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `Server._tools` validates each call's arguments against the tool's `inputSchema` with `schema_check` (type, enum, pattern, minimum, minItems, required) before dispatch. A violation is -32602 naming the property. Arguments that are not an object are refused.
- [ ] #2 The per-tool coercions of falsy values (`or "codegen"`, `or "dependants"`, and the empty-scenario fall-through) are removed. A default applies only when the property is absent.
- [ ] #3 Both servers, the reader and `knowgov-runs`, get the same rule, on both transports and both protocol eras.
- [ ] #4 `POST /api/run` refuses a key outside its documented set with 400, naming the key.
- [ ] #5 `check_mcp_server`, `check_transports` and the record are unchanged in substance. `CHANGELOG.md`'s Unreleased section rewords M5's line under Contract changes.
<!-- AC:END -->
