---
id: TASK-0209
title: Gate single fixes (doc-0030 G9, G11)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T15:33:00Z'
labels:
  - review
  - gate
dependencies: []
priority: low
type: bug
ordinal: 209000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

G9: --stage 2 --baseline record compares against stage 1's record, so the record's own stage-2 outcome reads as a regression. G11: review months take the minimum over nodes with the default mixed in, where decision-0005 point 2 says the default applies only when no node's kind is named. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 --stage 2 --baseline record is refused with exit 2, or reads the stage-2 gate
- [ ] #2 Review months follow decision-0005 point 2, by a test with a kind longer than the default beside an unnamed kind
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. G9: gate_cli refuses --stage 2 --baseline record (CannotRun, exit 2, before any store opens): the record keeps stage 2's verdicts but not its per-key levels, so it cannot ratchet the keys; --baseline FILE takes an earlier stage-2 report. 2. G11: cadence._read takes the shortest months among the kinds the register names months for, the default only when it names none (decision-0005 point 2). 3. Tests first, each failing on main: the refusal in test_gate_cli; a synthetic register with a 24-month kind beside an unnamed kind in test_cadence. 4. CHANGELOG under Unreleased > Changes; docs where --baseline record is described. 5. Checks: one_clock, comparator, run_tests (pins, no yaml, J-F), gate_after_change, stage2_reload.
<!-- SECTION:PLAN:END -->
