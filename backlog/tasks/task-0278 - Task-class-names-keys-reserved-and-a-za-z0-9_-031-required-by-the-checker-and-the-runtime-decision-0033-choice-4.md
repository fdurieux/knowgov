---
id: TASK-0278
title: >-
  Task-class names: keys reserved and [a-z][a-z0-9_-]{0,31} required, by the
  checker and the runtime (decision-0033 choice 4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T10:09:00Z'
updated_date: '2026-11-09T13:52:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 271000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`[tasks.keys]`, `[tasks.""]` and `[tasks."code gen"]` pass `check_subject` and `check_instance`. `keys` is the agent-chosen key set (doc-0014 C4), whose reports the hook refuses and which `knowgov-gate.sh` refuses as `KG_TASK`.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 4(a), `keys` is reserved, and a class name must match `[a-z][a-z0-9_-]{0,31}`. The checker and the runtime both refuse anything else.

Source: validation-pass group 1 C7, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `check_subject` and `check_instance` report an error for a class named `keys`, an empty name, or a name outside the pattern. The MCP `subject_check` reports the same.
- [x] #2 The runtime refuses such a manifest with exit 2 naming the class, at every reader that loads task classes.
- [x] #3 The public subjects (`codegen`, `design`) and the record are unchanged.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/task_policy.py: NAME [a-z][a-z0-9_-]{0,31}, RESERVED (keys); name_problem (code task-class); build raises TaskPolicyError on it before reading the table; table() quotes a name that is not a bare TOML key.
2. tools/check_subject.py: _class_name reports the problem per class, so check_instance and the MCP subject_check report it too; the subject-check schema's finding.rule gains task-class.
3. Every runtime reader loads task classes through tasks.TASKS, which runs build: no reader-by-reader change.
4. tests/test_task_class_names.py: names good and bad, the checker, the instance check, the MCP subject_check, gate_cli's exit 2; the public subjects clean. CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
task_policy.name_problem refuses a name outside [a-z][a-z0-9_-]{0,31} (empty, spaced, capitalised, leading digit or hyphen, over 32 characters, non-ASCII, dotted) and keys, the task a report on an agent-chosen key set names (doc-0014 C4). The problem's code is task-class, which the subject-check schema's finding.rule now lists.
task_policy.build raises TaskPolicyError(name, 'name', ...) before it reads the table, and tasks.TASKS builds every class. So every reader that loads task classes refuses the manifest, and a command exits 2: gate_cli, trace, run, proposal_impact, capture, store_reads, transcript, the MCP reader and the check tools. Its message reads '[tasks."code gen"] name: class name ...', with task_policy.table quoting a name that is not a bare TOML key.
check_subject._class_name reports it per class, so check_instance (its errors, exit 1) and the MCP subject_check (exit_code 1) carry it.
tests/test_task_class_names.py holds the names, the checker, the instance check, the MCP subject_check, and gate_cli's exit 2 with no store opened. The public subjects' codegen and design report no task-class finding.
Checks at 4bb2a59, on main ada71ce: run_tests 1002/1003 (1 skipped) on the pins and 943/1003 (60 skipped) bare. Comparators: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. check_round_trip --chain rdflib,rdflib on CargoQuote, and on J-F C,D3 with --expect-parts: every answer survives. check_mcp_server (rdflib) on CargoQuote S1,S2,S6 and J-F C,D3: every check holds. check_review_walkthrough, check_one_clock, check_subject on both subjects: OK. tools/complexity.py --check holds (1752 functions, 181 in the baseline).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A task class's name is now [a-z][a-z0-9_-]{0,31}, and never keys, the task a report on an agent-chosen key set names (doc-0014 C4). harness/task_policy.py's name_problem says why a name is refused, and build raises on it. So check_subject, check_instance and the MCP subject_check report an error, rule task-class, which the subject-check schema adds. Every command that loads task classes, all of them through tasks.TASKS, exits 2 naming the class. The public subjects' codegen and design are unchanged and the record did not move: both comparators show 0 differences, and the round trips and check_mcp_server hold. CHANGELOG: Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
