---
id: TASK-0263
title: >-
  CLI entry points exit through cli_exit, and empty or duplicate values are
  refused (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T15:38:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 257000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
These CLI failures were found:
- `register_nodes`, `upward` and `proposal_impact` do not go through `cli_exit`. A missing `KG_REGISTER` or `KG_SUBJECT`, `-o /dev/full`, `-o <dir>`, and upward's code_map format 2 each exit 1 with a traceback, which is the gate contract's code for a finding.
- Empty values silently become defaults in `gate_cli`:
  - `--subject ''` gates cargo_quote;
  - `--scenario ''` gates the first scenario;
  - `--register-previous ''` skips the staleness check, exit 0 and PROCEED, where the real previous register gives BLOCKED with 15 stale;
  - `-o ''` writes nothing.
- `KG_SUBJECT=''` gates cargo_quote.
- `run.py --scenarios` with no value runs nothing and exits 0, and duplicate scenarios run twice.
- `register_nodes --roots --parent X` silently takes `--roots`.
- `proposal_impact --scenario S9` on an empty store exits 0, reading keys as null.

These are fix-only: wrong results behind unchanged contracts.

Source: group 1 F1, F2, F14, F15 and F16, and group 3 F6 and F10, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `register_nodes`, `upward` and `proposal_impact` exit through `cli_exit.guard`/`run`, so any failure to run is exit 2 with its cause in one line. A test drives each case named.
- [ ] #2 An empty `--subject`, `--scenario`, `--register-previous`, `-o` or `--scenarios`, or an empty `KG_SUBJECT`, exits 2 naming the option. Duplicate `--scenarios` exit 2.
- [ ] #3 `register_nodes` refuses `--roots` together with `--parent`, and `proposal_impact --scenario` on a store that holds nothing exits 2.
- [ ] #4 The record and every check tool's output are unchanged.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256):
- Group 1: F2 still reproduces, `gate_cli --register-previous ''` silently skipped, exit 0.
- Spot check PI-1: `proposal_impact` exits 1 with a traceback for `-o /nonexistent/dir/x.json` (FileNotFoundError), `-o <a directory>` (IsADirectoryError) and a non-UTF-8 proposal file; route it through `cli_exit.run` as task-0228 did for preload_check. Not probed, read from the code: StoreChanged is not caught in its main(), so a racing writer gives a traceback.
- Spot check PI-2, task-0281's falsy rule not carried to the CLIs: `proposal_impact --task ''` reads as codegen, exit 0, where MCP refuses `task:''`; `--scenario ''` passes the held-scenario guard because `held.refusal` tests `if scenario and …`, shared with `gate_cli --no-load` (gate_cli.py:684). Fix: `scenario is not None`.
<!-- SECTION:NOTES:END -->
