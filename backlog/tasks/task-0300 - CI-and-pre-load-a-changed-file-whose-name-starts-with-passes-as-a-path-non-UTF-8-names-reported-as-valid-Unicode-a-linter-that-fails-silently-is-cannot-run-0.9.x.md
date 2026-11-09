---
id: TASK-0300
title: >-
  CI and pre-load: a changed file whose name starts with '-' passes as a path;
  non-UTF-8 names reported as valid Unicode; a linter that fails silently is
  cannot-run (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T19:02:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 293000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: the re-check of the pass's second-round fixes (decision-0032 point 4, task-0256), the spot check and group 1 at main c94dfa5. Fix-only; none fails open.

- R1, B2-1: a changed code file named `-x.py` or `--changed.py` makes trace-check exit 2 through both wrappers ("argument --changed: expected one argument"): the helper emits `--changed <name>`. trace-register's `--file` and preload's `--changed` take paths the same way. It fails closed, but a legal file name turns CI red.
- R2: for a non-UTF-8 name, the JSON report's `changed` holds a lone surrogate (`"caf\udce9.py"`) through surrogateescape; a strict consumer may reject it.
- B2-2: `KG_MARKDOWNLINT=/bin/false tools/preload_check.py INST` exits 0 and reports `spec.md` clean (`exit 0`, `version null`); `/bin/true` the same.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The helper emits `--changed=<name>` and `--file=<name>`, and preload takes `--changed=<name>`; a file named `-x.py` and `--changed.py` is checked as itself through both wrappers, held by `check_ci_wrappers`.
- [ ] #2 A non-UTF-8 name is reported in a form that is valid Unicode, and the form is documented.
- [ ] #3 A linter that answers no `--version`, or exits non-zero without a report the reader parses, is cannot-run, named; held by a test with `/bin/false` and `/bin/true`.
- [ ] #4 No contract changes; the record does not move.
<!-- AC:END -->
