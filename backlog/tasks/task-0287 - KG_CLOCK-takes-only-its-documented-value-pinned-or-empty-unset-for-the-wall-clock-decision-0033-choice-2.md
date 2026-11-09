---
id: TASK-0287
title: >-
  KG_CLOCK takes only its documented value: pinned, or empty/unset for the wall
  clock (decision-0033 choice 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T15:37:00Z'
updated_date: '2026-11-09T16:19:00Z'
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
- [x] #1 `KG_CLOCK` is read through `harness/switches.py`: `pinned` pins, empty or unset reads the wall clock, anything else exits 2 naming the setting and `pinned`, at every reader of `review.today()`, `review.now()` and `review.pinned`.
- [x] #2 Shell and Python read a flag's whitespace the same way, and `test_switches` holds them equal on padded values.
- [x] #3 A bad `KG_LOAD_MEMORY_CHECK` exits 2 with BadSwitch's own message, not as a store failure.
- [x] #4 The record does not move: the test runner and every check tool keep `KG_CLOCK=pinned`.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. KG_CLOCK into harness/switches.py as CLOCK {pinned, empty}; review._pinned() reads it through switches.on in today() and now(); review.pinned writes pinned, so every check tool and the worker keep it.
2. N8: switches.parse strips nothing (words still case-folded); knowgov-gate.sh's flag already strips nothing; test_switches holds both on padded values.
3. N9: gate_cli.run and trace.main re-raise switches.BadSwitch past their store catch-all, so cli_exit names it.
4. instance/README.md's row and paragraph; CHANGELOG Unreleased > Contract changes; the suite, the ratchet and the CQ comparator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Readers: KG_CLOCK is read only by harness/review.py (today(), now(), both through _pinned()); review.pinned and harness/worker.py write 'pinned'; cadence.py and mcp_server.py reach it only through review.today(). So AC1 holds at every reader. Verified on gate_cli (rdflib, pins, KG_TODAY unset): KG_CLOCK=Pinned, 'pinned ' and 1 exit 2 with 'KG_CLOCK=... is not a value it accepts: pinned (the wall clock refused), or empty or unset (the wall clock)'; pinned exits 2 with WallClock. N8: switches.parse no longer strips; test_switches refuses ' 1', '1 ', ' 0' in both the shell flag and Python, and ' off'/'off ' for the word settings. N9: KG_LOAD_MEMORY_CHECK=nope on gate_cli exits 2 naming the setting, not 'the store did not answer'; test_switches holds the re-raise in gate_cli.py and trace.py. Record: CQ comparator 0 differing over 7 scenarios; tests/run_tests.py 1015/1016 (1 skipped, 0 failed) with the pins; complexity ratchet holds. PR #432.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
KG_CLOCK is a switch in harness/switches.py: pinned pins, empty or unset reads the wall clock, any other value is BadSwitch, exit 2 naming the setting (before, Pinned or 1 silently read the wall clock). switches.parse strips no whitespace, as knowgov-gate.sh's flag never did, so a padded flag is refused in both (N8). gate_cli and trace let BadSwitch reach cli_exit, so a misspelt switch exits 2 as itself, not as a store failure (N9). The record does not move: the test runner, the check tools and the worker keep KG_CLOCK=pinned; the CQ comparator 0 differing; the suite green with the pins. CHANGELOG Unreleased > Contract changes. PR #432.
<!-- SECTION:FINAL_SUMMARY:END -->
