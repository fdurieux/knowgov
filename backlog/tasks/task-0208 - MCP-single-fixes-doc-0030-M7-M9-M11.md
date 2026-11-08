---
id: TASK-0208
title: MCP single fixes (doc-0030 M7, M9, M11)
status: In Progress
assignee: []
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T15:54:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. M7: code_path's ledger leg reads unchecked when the ledger holds an entry but there is no code root (no instance, or a code map that does not hold); a test first, failing on the old code.
2. M11: register_impact.no_bytecode(), a counted context that sets sys.dont_write_bytecode while the register's own modules load (load_tools, proposal_impact.check_module); a test in a fresh interpreter on a copy of the register, failing on the old code.
3. M9: tools/check_mcp_server.py's arms_bundle takes the scenario's prompts (scenarios.toml prompts, task_codegen by default), as harness/run.py's _run_all; a test recording the task name verbatim_documents receives, failing on the old code.
4. CHANGELOG under Unreleased > Changes. Checks: run_tests with pins, bare, J-F; check_mcp_server (with check_transports) on both subjects; the comparator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Each new test failed on the old code first:
- tests/test_upward.py::test_a_ledger_entry_with_no_code_root_reads_unchecked_never_drift_false: the old leg read status read, drift false, for a ledger entry with no instance and with an instance lacking code_map.toml.
- tests/test_reader_no_bytecode.py: on a copy of demo/register, load_tools plus check_module wrote tools/__pycache__ (check_register, impact, reconcile, register .pyc) under the old code; none after, and sys.dont_write_bytecode is restored.
- tests/test_check_mcp_arms_prompts.py: the old check passed task_codegen for every CargoQuote scenario; the runner passes task_s6 for S6.
Outside this task's scope, left as they are: tools/connector.py and tools/lighthouse_evidence.py also load demo/register/tools by path and can write its __pycache__ (gitignored); neither is the reader. register_impact.load_tools keeps the register's tools/ on sys.path, as before.
<!-- SECTION:NOTES:END -->
