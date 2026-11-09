---
id: TASK-0275
title: >-
  One table of every KG_* setting the two contract files name, each marked
  contract or not, held by a test (decision-0033 choice 1)
status: To Do
assignee: []
created_date: '2026-11-09T10:09:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 268000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0016 point 3 made every setting that `instance/README.md` or `docs/security.md` documents a contract. task-0234's README section reads as if only decision-0027's twenty are contracts, and the two files name 75 settings.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 1(b), one table lists them all, each marked contract or not. decision-0016 point 3 now reads "a setting the table marks as a contract".

The contracts are the settings an instance's CI, compose file or hook sets in order to run. The test clock, demo ports and tuning knobs are marked not a contract. The classification is the maintainer's word row by row: the build proposes it, and the PR is held until the maintainer confirms the table.

Source: validation-pass group 1 C3, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `instance/README.md` has one table with one row per `KG_*` setting named in `instance/README.md` or `docs/security.md`. Each row gives the setting, what it does, its group, and whether it is a contract.
- [ ] #2 A test fails when either file names a setting the table lacks, or when the table names a setting neither file mentions.
- [ ] #3 The README's settings paragraph and the contracts table say that a setting is a contract when the table marks it so, citing decision-0016 point 3 as amended by decision-0033 choice 1.
- [ ] #4 The PR is held for the maintainer's confirmation of the rows. The coordinator merges only after it.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the table under Contract changes.
<!-- AC:END -->
