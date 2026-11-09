---
id: TASK-0287
title: >-
  KG_CLOCK takes only its documented value: pinned, or empty/unset for the wall
  clock (decision-0033 choice 2)
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
ordinal: 280000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`KG_CLOCK` is a contract (#418's table) and accepts anything. `Pinned`, `pinned ` (trailing space), `1` and `yes` all silently mean unpinned, and the wall clock is read. With `KG_CLOCK=Pinned`, KG_TODAY unset, and `gate_cli … --as-of today`, it exits 0; with `pinned` it exits 2.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 2, `KG_CLOCK` goes into `harness/switches.py` as a word setting: `pinned` means pinned; empty or unset means the wall clock; anything else exits 2, naming the setting and `pinned`.

Fix-only, the same module:
- N8: `switches.parse` strips whitespace but `knowgov-gate.sh`'s `flag` does not, so `KG_NO_LOAD=' 1'` is on in Python and exit 2 in the shell, though `test_switches` says they agree. One rule in both: strip in neither, and refuse.
- N9: a bad `KG_LOAD_MEMORY_CHECK` exits 2 as "the store did not answer: BadSwitch: …". `BadSwitch` reaches `cli_exit` with its own message.

Source: the bounded re-probe (decision-0032 point 4, task-0256), group 1 at main 9861953 (N1, N8, N9).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `KG_CLOCK` is read through `harness/switches.py`: `pinned` pins, empty or unset reads the wall clock, anything else exits 2 naming the setting and `pinned`, at every reader of `review.today()`, `review.now()` and `review.pinned`.
- [ ] #2 Shell and Python read a flag's whitespace the same way, and `test_switches` holds them equal on padded values.
- [ ] #3 A bad `KG_LOAD_MEMORY_CHECK` exits 2 with BadSwitch's own message, not as a store failure.
- [ ] #4 The record does not move: the test runner and every check tool keep `KG_CLOCK=pinned`.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
