---
id: TASK-0281
title: >-
  MCP arguments validated against each tool's inputSchema before dispatch
  (-32602), and the page's run body refuses unknown fields (decision-0033 choice
  7)
status: Done
assignee: []
created_date: '2026-11-09T10:10:00Z'
updated_date: '2026-11-09T13:34:00Z'
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
- [x] #1 `Server._tools` validates each call's arguments against the tool's `inputSchema` with `schema_check` (type, enum, pattern, minimum, minItems, required) before dispatch. A violation is -32602 naming the property. Arguments that are not an object are refused.
- [x] #2 The per-tool coercions of falsy values (`or "codegen"`, `or "dependants"`, and the empty-scenario fall-through) are removed. A default applies only when the property is absent.
- [x] #3 Both servers, the reader and `knowgov-runs`, get the same rule, on both transports and both protocol eras.
- [x] #4 `POST /api/run` refuses a key outside its documented set with 400, naming the key.
- [x] #5 `check_mcp_server`, `check_transports` and the record are unchanged in substance. `CHANGELOG.md`'s Unreleased section rewords M5's line under Contract changes.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on claude/task-0281-mcp-arguments (PR #422), after #412 (task-0272) and train #426 (#417's schema_check). mcp_server.argument_refusal runs in Server._tools before dispatch on both servers (knowgov, knowgov-runs), both transports, both eras: arguments not an object (absent or null are none; [] and "" refused), an unknown argument (M5), and every other inputSchema violation by schema_check (type, enum, pattern, minimum, minItems, required) as -32602 naming the property (argument_errors). schema_check: #417's pattern (a final $ read as \\Z) and propertyNames kept; minItems added in _check_value. Coercions removed: task, walk, fail_on and baseline default only when absent; _check_scenario refuses scenario ""; _as_of reads "" as a date to resolve, not the session's. POST /api/run refuses a key outside server.RUN_FIELDS (scenario, mode, n, row, effort, as_of, by, subject: run_request's set, what index.html and knowgov-runs send, listed in demo/README.md) with 400 naming the key. CHANGELOG Unreleased > Contract changes: M5's line reworded. Tests: tests/test_mcp_arguments.py (8: every property's wrong type on both servers and eras; each keyword; non-object arguments; defaults; HTTP both eras; the run body; the changelog). Existing tests expecting isError for a schema violation now ask _refused (tests/test_mcp_server.py), which asserts the one refusal argument_refusal says the call must get; module _call helpers read a -32602 through _as_result, asserting its code. Complexity: schema_check._check and Server._tools held by helpers (argument_refusal); baseline tightened by --update on the merged tree.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every MCP call's arguments are held to the tool's inputSchema before dispatch, on both servers, both transports and both protocol eras: a type, enum, pattern, minimum, minItems or required violation, an unknown argument, or arguments that are not an object answer -32602 naming the property, and nothing runs. A default applies only when the argument is absent, so scenario "" no longer answers for the held scenario and walk "" no longer reads as dependants. The page's POST /api/run refuses a body key outside its eight fields with 400, naming the key. schema_check gains minItems beside #417's pattern. decision-0033 choice 7(a); CHANGELOG rewords M5's contract line.
<!-- SECTION:FINAL_SUMMARY:END -->
