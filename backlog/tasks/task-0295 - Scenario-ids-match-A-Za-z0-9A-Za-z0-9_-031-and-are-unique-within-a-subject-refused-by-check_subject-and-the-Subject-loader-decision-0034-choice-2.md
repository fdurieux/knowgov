---
id: TASK-0295
title: >-
  Scenario ids match [A-Za-z0-9][A-Za-z0-9_-]{0,31} and are unique within a
  subject, refused by check_subject and the Subject loader (decision-0034 choice
  2)
status: To Do
assignee: []
created_date: '2026-11-09T16:51:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 288000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 (accepted 2026-11-09, "N7, D1, D3 as advised") choice 2(a). Found by the spot check (CS-3) at 9861953.

- Duplicate ids pass `check_subject`, and `Subject` keeps the last one silently.
- `id = ""` and `id = "../x"` pass, and the runtime gates them: `gate_cli` reports `"scenario": "../x"`.
- `run.py` writes `out_root / sc` (`harness/run.py` `_run_all`), so `../x` leaves `--out`.

Every public scenario id matches (S0 to S7, C, D1 to D5). `[[scenario.sources]]` ids and `stage2.derived` ids are not scenario ids and are unchanged. task-0265's duplicate-scenario-id item moves here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A scenario id outside `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, a duplicate id within a subject, and a scenario with no id are each an error in `check_subject` (exit 1) and in the MCP `subject_check`, naming the id and the rule.
- [ ] #2 The `Subject` loader refuses the same manifests, so `gate_cli`, `run.py`, the page and the MCP servers exit 2 or refuse naming the id, before anything is written.
- [ ] #3 The public subjects, the example instance and the record are unchanged.
- [ ] #4 Each form in the description is a test.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->
