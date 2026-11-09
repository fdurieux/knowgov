---
id: TASK-0262
title: >-
  One strict YYYY-MM-DD date parse for every as_of, --as-of, KG_AS_OF, KG_TODAY
  and run body (G9-17)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 256000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`harness/cadence.py` `as_of` checks only that the value is 10 characters long, then calls `date.fromisoformat`. On Python 3.11 and later that also takes the ISO week and basic forms: `2026-W45-1` reads as 2026-11-02, and `20261105xx` as 2026-11-05.

The loose parse reaches:
- the MCP `as_of` and `KG_AS_OF`;
- `--as-of` on `gate_cli`, `run`, `trace` and `proposal_impact`;
- the page's `POST /api/run`, whose `run.json` then records "2026-W45-1", a date the run did not read.

Other loose dates:
- `KG_TODAY` takes `20261109`.
- `capture due --on` and `connector --exported-on` take week forms.
- `mcp_runs` uses `\d{4}-\d{2}-\d{2}`, which also matches fullwidth digits.
- `cadence._date` cuts `[:10]` from `valid_until` and `at`.

The documented form is YYYY-MM-DD, and the fix closes the domain to it. The finding is contract-bearing, though borderline, since the documented format is unchanged.

Source: group 1 F3 and group 2 F4, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One function parses a date: an ASCII `[0-9]{4}-[0-9]{2}-[0-9]{2}` match, then `fromisoformat`. Every reader named above uses it, and a test lists them.
- [ ] #2 A week, basic, fullwidth or suffixed form is refused, naming the value:
- exit 2 on the CLIs;
- the reader's documented refusal on the MCP;
- 400 on the page.
- [ ] #3 `record`, `today` and valid dates read as they do today, and the record does not move.
- [ ] #4 `cadence._date`'s `[:10]` on `valid_until` and `at` is checked the same way, or the task records why those values are read as stored.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
