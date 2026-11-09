---
id: TASK-0265
title: >-
  The manifest checker and the runtime agree, and the checker checks every field
  the runtime reads (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 259000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Where the checker and the runtime disagree:
- With `keys` omitted, the checker errors but the gate crashes with ZeroDivisionError, reported as "the store did not answer".
- With `max_unverified_share` or `block_levels` omitted, or a mistyped field such as `max_unverfied_share`, the runtime runs on defaults.

What the checker does not check:
- a subject id that is `""`, `"../evil"`, `"a b"`, missing, or an integer (the integer makes `check_subject`'s own report fail its schema);
- `[record] as_of = "soon"`, after which `--as-of record` silently reads today;
- a duplicate scenario id;
- a scenario without an id, which passes the check and then fails with "does not load: 'id'";
- `verifications = "no"`, which is read as true;
- `gate = "MAYBE"`;
- duplicate task keys.

The MCP `subject_check`, and `check_subject`'s CLI, crash on an unparseable register_map, scenarios or plants TOML instead of reporting it.

`scenario_runs` lists a "record" source on minimal, which `scenario_result` then refuses.

These are fix-only.

Source: group 1 F5 and F6, and group 2 F10 and F12, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `task_policy.build` raises when `keys` is missing. The runtime refuses whatever the checker errors on, unknown task fields included, with exit 2 naming the field.
- [ ] #2 `check_subject` errors on each manifest and scenario case listed, with a test per case.
- [ ] #3 An unparseable register_map, scenarios or plants file is a `manifest` finding, on the CLI and through `subject_check`.
- [ ] #4 `scenario_runs` lists a record source only where `scenario_result` can answer it, and `check_mcp_server` passes on `subjects/minimal`.
<!-- AC:END -->
