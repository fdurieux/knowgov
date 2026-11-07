---
id: TASK-0194
title: >-
  check_instance refuses a scenario id two subjects declare, an empty subjects/
  and duplicate subject ids (doc-0030 F1 interim, P11)
status: To Do
assignee: []
created_date: '2026-11-07T07:14:00Z'
labels:
  - review
  - instance
dependencies: []
priority: high
type: bug
ordinal: 194000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

The interim for H1, to ship now as a fix ahead of F1. The store records a held scenario by its id alone (`act:extract:<scenario>:<version>`), so two subjects of one instance that share a scenario id answer each other's gates: the page, `gate_cli --no-load` and every store-backed MCP tool (three reviewers, CONFIRMED). The onboarding skill makes every subject share `S0` (instance/ci/claude/skills/knowgov-onboard/SKILL.md). P11: tools/check_instance.py accepts an empty `subjects/` and two folders with one `[subject] id`, which the page and subject_ids then hide silently.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 tools/check_instance.py exits 1 when two of an instance's subjects declare one scenario id, naming the id, the subjects and why (doc-0030 H1)
- [ ] #2 It exits 1 on an empty subjects/ and on a repeated subject id
- [ ] #3 The public subjects and tools/example_instance.py's instance pass unchanged
- [ ] #4 The onboarding skill tells an adopter to give each subject its own scenario ids, and harness/wizard.py --check stays fresh
<!-- AC:END -->
