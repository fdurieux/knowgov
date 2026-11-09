---
id: TASK-0265
title: >-
  The manifest checker and the runtime agree, and the checker checks every field
  the runtime reads (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T19:02:00Z'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256):
- Group 3: a class with no `keys` still crashes the gate (ZeroDivisionError), while check_subject flags `required` and `task_policy.build` accepts it; duplicate keys pass; a key-syntax error passes the gate; `block_levels = []` is accepted, which may need a decision; a stored date of 9999-06-30 overflows `cadence.due`'s add_months, exit 2, and check_subject passes it.
- Spot check CS-1: check_subject exits 1 with a traceback (exit 1 is 'manifest refused') for a non-UTF-8 subject.toml, an invalid scenarios.toml or register_map.toml, and `[register] map = 5` (TypeError); MCP subject_check answers 'could not answer'. Each should be an error finding (rule `manifest`).
- Spot check CS-2: `[[subject]]` and `[[tasks]]` pass check_subject (exit 0); gate_cli refuses them ('list' object has no attribute 'get'/'items'), exit 2. Type-check the tables.
- Spot check CS-4, each exit 0: `[record] as_of = "tomorrow"`; `[register] map = "nope.toml"` with no finding, so the rows go unchecked; a key holding a zero-width space, which KEY_RE's \s misses.
- Scenario ids (duplicates, `""`, `"../x"`, which run.py joins under --out) go to the maintainer as the spot check's D1. If they decide on a format rule, that task carries the duplicate-id item here.

Group 2's re-probe at 9861953: round-1 F10 still reproduces. `subject_check` with `register_map_toml: "x"` answers isError TOMLDecodeError.

decision-0034 (accepted 2026-11-09): the duplicate scenario id item moves to task-0295 (choice 2), and CS-4's zero-width space in a key to task-0296 (choice 3). The other items stay here.

Re-check of the pass's second-round fixes (decision-0032 point 4, task-0256), the spot check at 0682e16 and 946c72e, all fix-only:
- N1: a document named `plants.toml` or `scenarios.toml`, with no plants_toml or scenarios_toml passed, is refused as 'the same file as … passed already'. It is a reserved name, so say so.
- N2: `documents {"subject.toml/x": …}` is refused as 'document path 'subject.toml' is also a folder', which names the manifest a document.
- `[register] map = 5` still answers 'could not answer: TypeError' (CS-1).
- T1: a scenarios.toml written with `[scenario]` (a table) instead of `[[scenario]]` passes check_subject (exit 0, CLI and MCP). gate_cli exits 2 with 'string indices must be integers', and the MCP reader exits 1 at start with a TypeError traceback. `scenario_ids.problems` treats a non-list as empty. It should report 'scenario must be an array of tables', and the loader should raise ScenarioIdError, exit 2 everywhere.
<!-- SECTION:NOTES:END -->
