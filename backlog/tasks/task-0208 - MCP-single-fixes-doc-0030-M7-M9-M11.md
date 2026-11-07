---
id: TASK-0208
title: MCP single fixes (doc-0030 M7, M9, M11)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - mcp
dependencies: []
priority: low
type: bug
ordinal: 208000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

M7: code_path's ledger leg reads drift false for a file never looked at. M9: tools/check_mcp_server.py hardcodes task_codegen where the arms use the scenario's prompts. M11: register_impact's exec_module writes __pycache__ into KG_REGISTER/tools. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 code_path's ledger leg with no code root reads unchecked, not drift false
- [ ] #2 check_mcp_server.py takes each scenario's prompts as the arms do
- [ ] #3 The reader writes no bytecode into KG_REGISTER
<!-- AC:END -->
