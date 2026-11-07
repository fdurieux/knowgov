---
id: TASK-0200
title: >-
  Uniform CLI and protocol edges: one exit wrapper, MCP arguments checked,
  errors mapped, hooks wrapped (doc-0030 F6)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - cli
  - mcp
  - hooks
dependencies:
  - TASK-0193
priority: medium
type: bug
ordinal: 200000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

M5: every inputSchema says additionalProperties false and only register_nodes refuses an unknown argument (`gate_verdict {senario: S4}` answers S1 unguarded). M6: an unhashable params.name kills the stdio server. G6 and R9: a malformed baseline, an unwritable -o or review.WallClock exit 1 with a traceback, the code reserved for a finding. G7: --publish commits before the report is validated and written. M10: --host ::1 crashes with exit 1. P8: a hook raised on a malformed report exits 1, which the advisory profile treats as a warning. P9: knowgov-gate.sh's `$(cd ... && pwd)` exits 1 on a mistyped path. G12: schema_check takes true for 1. M5 is a behaviour change (unknown arguments refused), so it gathers for 0.9.0; the rest are fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One exit wrapper for gate_cli, trace, run and transcript maps CannotRun, WallClock, a malformed baseline, an unwritable -o and any unexpected exception to exit 2 with its cause; gate_cli --publish validates and writes the report before commit()
- [ ] #2 The MCP servers refuse an argument not in the tool's inputSchema and a non-string tool name with -32602, and map any other exception to -32603 on stdio and HTTP; --host ::1 binds or exits 2
- [ ] #3 Every hook's entry maps a malformed report or any exception through decide or refuse to its blocking exit; knowgov-gate.sh exits 2 when a path does not resolve
- [ ] #4 schema_check's enum and const compare type as well as value
- [ ] #5 CHANGELOG.md has M5's line under Unreleased's contract heading
<!-- AC:END -->
