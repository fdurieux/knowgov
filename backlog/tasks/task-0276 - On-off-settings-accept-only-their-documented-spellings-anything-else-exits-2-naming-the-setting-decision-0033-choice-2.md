---
id: TASK-0276
title: >-
  On/off settings accept only their documented spellings; anything else exits 2
  naming the setting (decision-0033 choice 2)
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
ordinal: 269000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`KG_NO_LOAD` and `KG_PUBLISH` act only on exactly `1`, so `true`, `yes` and `on` silently mean off. In `action.yml`, `annotate` and `sarif` are compared case-sensitively in sh, while `publish` is compared in a GitHub expression, which ignores case.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 2(a): `1` means on; `0`, empty or unset means off; anything else exits 2 naming the setting and the accepted values. A setting whose documentation uses a word (for example `KG_LOAD_MEMORY_CHECK=off`, `KG_KEY_CHECK=off`) keeps that spelling and refuses others. The action's and the GitLab include's boolean inputs take `true` or `false` in any case, and anything else fails.

Source: validation-pass group 1 C4, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The task lists every on/off `KG_*` setting with its documented spellings, and one parser reads them all. A value outside a setting's spellings exits 2 naming the setting and the spellings accepted.
- [ ] #2 `action.yml`'s and the GitLab include's boolean inputs compare without case. A value other than true or false fails the step, naming the input.
- [ ] #3 Every spelling documented today keeps its meaning, and the record does not move.
- [ ] #4 `check_ci_wrappers`, `harness.yml`'s instance/ci steps and `tests/run_tests.py` pass.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
