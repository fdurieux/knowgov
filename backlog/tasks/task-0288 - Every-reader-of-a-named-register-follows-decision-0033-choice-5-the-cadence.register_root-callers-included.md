---
id: TASK-0288
title: >-
  Every reader of a named register follows decision-0033 choice 5, the
  cadence.register_root callers included
status: To Do
assignee: []
created_date: '2026-11-09T15:37:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
  - backlog/decisions/decision-0033
priority: high
ordinal: 281000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0279 left the readers that go through `cadence.register_root` unchanged. Choice 5 covers every reader that takes a register. With `KG_REGISTER` set to a missing directory:
- capture ingest skips the issued-handle check (N11): `ans-handle_unknown.toml`, from `employee-99`, is refused with the good register, but here it exits 0 and writes `2026-11-09-ORG-0002-employee-99.toml`, a weaker policy;
- capture questionnaire and review exit 2, but with a raw FileNotFoundError;
- capture due exits 0;
- trace check falls back to 12 review months without saying so;
- `run.py --deterministic` exits 0;
- the page starts, and `/api/register` answers 404 with the full path in the error.

Fix-only, the same check (N10): `check_subject`'s test of a readable register differs from the others'. A directory with only `metamodel/types.toml` gives exit 1 with 187 errors where the others give 2, and one without `tools/register.py` gives 0 where the others give 2.

Source: the bounded re-probe (decision-0032 point 4, task-0256), group 1 at main 9861953 (§8, N10, N11).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A named register that cannot be read is refused with exit 2 naming it, by the one check `register_impact.require` uses, at capture ingest, questionnaire, review and due, trace check and register, and `run.py`. An unnamed register keeps today's behaviour.
- [ ] #2 The page refuses at start, or answers `/api/register` with a message that does not leak the path.
- [ ] #3 `check_subject` uses the same readable-register test as the other tools.
- [ ] #4 Every reproduction in the description is a test. The record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
