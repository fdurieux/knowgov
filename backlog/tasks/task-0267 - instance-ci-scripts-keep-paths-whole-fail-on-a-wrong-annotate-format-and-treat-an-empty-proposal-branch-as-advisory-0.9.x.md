---
id: TASK-0267
title: >-
  instance/ci scripts keep paths whole, fail on a wrong annotate format, and
  treat an empty proposal branch as advisory (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
updated_date: '2026-11-09T15:38:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 261000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Paths are split on whitespace: changed paths go through `p.stdout.split()` and then an unquoted `for p in $paths` with globbing on, and `KG_FILES` is split the same way. So a file named `a b.py` is checked as `a` and `b.py`.

An unknown `KG_ANNOTATE` format prints "annotate … failed", and the job exits 0.

`proposal-impact.sh` exits 2 ("adds no node and no link") on a register branch with no additions. The README calls the step advisory and promises 0 with a report, and 2 only when it cannot run.

Path forms are handled inconsistently:
- `preload-check.sh` joins an absolute `KG_PRELOAD_BASELINE` as `$INST//abs` and exits 2.
- `preload_check` skips `--changed ../../../etc/passwd` (exit 0) but cannot run on `--changed /etc/passwd` (exit 2).
- A directory that is not an instance passes when `--layout` is not given.

These are fix-only.

Source: group 1 F9, F10, F17 and F18, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Paths travel NUL-separated (`git -z`) with globbing off, held by a test with a space and a glob character in a path.
- [ ] #2 An unknown `KG_ANNOTATE` format exits 2.
- [ ] #3 `proposal-impact.sh` exits 0 with a report naming `not_read` when a branch adds nothing.
- [ ] #4 Absolute and escaping paths are handled one way, and named. A directory that is not an instance is refused.
- [ ] #5 `check_ci_wrappers` and `harness.yml`'s instance/ci steps pass.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256); pulled forward before the 0.9.0 cut by the coordinator, because AC #1 fails open:
- Spot check GL-1: git quotes non-ASCII names (`core.quotepath`), so committing `<code root>/módulo.py` and running `KG_GATE=trace-check` reports 'no code changed since <base>', exit 0; `new module.py` checks 'module.py'. Use `git -c core.quotepath=off diff -z --name-only`.
- Spot check GL-2, AC #2: `KG_ANNOTATE=nope:x.json` and `,,` log 'annotate … failed' (one with a Python traceback) and exit 0 with no report. Unknown formats and empty elements exit 2 before the core command; a write failure (`gitlab:sub dir/x.json`) stays a logged warning with the command's exit.
- Group 1 N2: `KG_BASE=--output=/tmp/x` reaches `git diff` as an option (git created /tmp/x). Use `--end-of-options`, or refuse a leading `-`.
- Group 1 N6: `KG_SPECTRAL=/nonexistent/spectral tools/preload_check.py` exits 0, file unchecked, 'Spectral is not installed here'. A named linter that cannot run exits 2 naming the setting; unset keeps 'not installed'.
<!-- SECTION:NOTES:END -->
