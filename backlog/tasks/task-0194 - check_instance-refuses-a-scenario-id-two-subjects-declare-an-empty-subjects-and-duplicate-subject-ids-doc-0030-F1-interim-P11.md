---
id: TASK-0194
title: >-
  check_instance refuses a scenario id two subjects declare, an empty subjects/
  and duplicate subject ids (doc-0030 F1 interim, P11)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:14:00Z'
updated_date: '2026-11-07T07:38:00Z'
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
- [x] #1 tools/check_instance.py exits 1 when two of an instance's subjects declare one scenario id, naming the id, the subjects and why (doc-0030 H1)
- [x] #2 It exits 1 on an empty subjects/ and on a repeated subject id
- [x] #3 The public subjects and tools/example_instance.py's instance pass unchanged
- [x] #4 The onboarding skill tells an adopter to give each subject its own scenario ids, and harness/wizard.py --check stays fresh
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. check_instance.check: an empty subjects/, a subject id two roots declare, a scenario id two subjects declare, each an error (exit 1) naming what and why. 2. Tests on the example instance with a copied subject; the public subjects' scenario ids disjoint. 3. Skill: rename the copied S0 to <id>-S0 and keep ids unique per instance; instance/README the same, and the three refusals listed; wizard --check. 4. Sweep the suite's multi-subject fixtures for a shared scenario id. 5. CHANGELOG under Changes; suite both ways.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
tools/check_instance.py: subjects/ empty -> error; ids -> roots, a repeated id -> error naming the roots; scenario id -> subjects, one declared by two -> error naming the id, the subjects and why (the store records a held scenario by its id alone, doc-0030 H1). A hyphenated <id>-S0 checked through gate_cli default, --publish and --no-load's held-scenario read. Fixture sweep: the repository's subjects/ and every tools/fixtures subject declare disjoint ids (C, D1-D5, S0-S7); tests/test_page_subject.py's rescan fixture built alpha and beta both with S0 (it passed, the page does not check ids) and now gives each <sid>-S0, as the skill tells adopters. tools/example_instance.py's instance (one subject) checks clean, unchanged. Suite: KG_TEST_REQUIRE=rdflib 691/693 (2 skipped), KG_SUBJECT=subjects/jef_data_load 690/693 (3 skipped), 0 failed, before the page-fixture change; rerun after.
<!-- SECTION:NOTES:END -->
