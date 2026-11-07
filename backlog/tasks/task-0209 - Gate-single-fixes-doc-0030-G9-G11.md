---
id: TASK-0209
title: Gate single fixes (doc-0030 G9, G11)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
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
