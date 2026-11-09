---
id: TASK-0267
title: >-
  instance/ci scripts keep paths whole, fail on a wrong annotate format, and
  treat an empty proposal branch as advisory (0.9.x)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:33:00Z'
updated_date: '2026-11-09T16:12:00Z'
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
- [x] #1 Paths travel NUL-separated (`git -z`) with globbing off, held by a test with a space and a glob character in a path.
- [x] #2 An unknown `KG_ANNOTATE` format exits 2.
- [x] #3 `proposal-impact.sh` exits 0 with a report naming `not_read` when a branch adds nothing.
- [x] #4 Absolute and escaping paths are handled one way, and named. A directory that is not an instance is refused.
- [x] #5 `check_ci_wrappers` and `harness.yml`'s instance/ci steps pass.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AC1: knowgov-gate.sh changed() reads git -c core.quotepath=off diff -z --name-only --end-of-options BASE; the Python helper shlex-quotes each path into 'FLAG path' pairs the shell takes by eval, never word-split or globbed; KG_FILES split with globbing off. The same NUL-separated read in the Claude hook (_committed, _status with renames) and proposal_impact's branch mode. 2. AC2: annotate_ok refuses an empty element, an unknown format or FORMAT: before the core command, exit 2 naming KG_ANNOTATE and its four formats; annotate.py's unwritable -o a message, never a traceback (a warning beside the command's exit). 3. AC3: evaluate_branch reads a branch that adds nothing (empty overlay), so proposal-impact.sh exits 0 with a report naming not_read. 4. AC4: preload-check.sh takes an absolute KG_PRELOAD_BASELINE as given; preload_check refuses --changed outside the instance (absolute or by ..) alike, naming it, and a directory with no subjects/. 5. N2: KG_BASE starting with - refused (exit 2); --end-of-options before every base git reads. N6: a KG_* linter setting naming nothing executable exits 2 naming it. 6. Tests: check_ci_wrappers on both wrappers (space, glob character, non-ASCII; KG_ANNOTATE; a base of --output=); tests/ for the hook, branch mode, preload_check and proposal-impact.sh; each failing on main.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256); pulled forward before the 0.9.0 cut by the coordinator, because AC #1 fails open:
- Spot check GL-1: git quotes non-ASCII names (`core.quotepath`), so committing `<code root>/módulo.py` and running `KG_GATE=trace-check` reports 'no code changed since <base>', exit 0; `new module.py` checks 'module.py'. Use `git -c core.quotepath=off diff -z --name-only`.
- Spot check GL-2, AC #2: `KG_ANNOTATE=nope:x.json` and `,,` log 'annotate … failed' (one with a Python traceback) and exit 0 with no report. Unknown formats and empty elements exit 2 before the core command; a write failure (`gitlab:sub dir/x.json`) stays a logged warning with the command's exit.
- Group 1 N2: `KG_BASE=--output=/tmp/x` reaches `git diff` as an option (git created /tmp/x). Use `--end-of-options`, or refuse a leading `-`.
- Group 1 N6: `KG_SPECTRAL=/nonexistent/spectral tools/preload_check.py` exits 0, file unchecked, 'Spectral is not installed here'. A named linter that cannot run exits 2 naming the setting; unset keeps 'not installed'.

Places that read git's path list or KG_FILES (the coordinator's list, from the spot check of 2026-11-09): (1) instance/ci/knowgov-gate.sh changed(), used by trace-check (--changed) and trace-register (--file), shared by instance/ci/gitlab/knowgov.gitlab-ci.yml and instance/ci/github/action.yml (which calls the script with KG_BASE from its base input or the pull request's base): now git -c core.quotepath=off diff -z --name-only --end-of-options BASE, the helper shlex-quoting each path into 'FLAG path' that the shell takes by eval; (2) knowgov-gate.sh's KG_FILES loop (trace-register; the action's files input): whitespace-separated as documented, now with globbing off; (3) instance/ci/claude/knowgov_hook.py _committed (git diff --cached / --name-only) and _status (git status --porcelain=v1): now -z with core.quotepath=off, a rename's source skipped; (4) harness/proposal_impact.py branch_overlay, run by instance/ci/proposal-impact.sh: git diff --name-status -z; (5) tools/preload_check.py _since, run by instance/ci/preload-check.sh: already -z, now with core.quotepath=off and --end-of-options. Spot check: the non-ASCII form failed open beyond the space split (git quoted módulo.py, so trace-check read 'no code changed', exit 0); a space read 'new module.py' as 'module.py'; tested with módulo.py, new module.py and glob[1]*.py on both wrappers. AC2: ',,' and 'nope:x.json' exit 2 before the core command naming KG_ANNOTATE and its four formats; 'gitlab:<dir>/sub dir/x.json' unwritable is a warning beside the command's exit; the traceback form was annotate.py's unwritable -o, now a message. N2: KG_BASE=--output=FILE made git write FILE; now refused with exit 2 naming KG_BASE, and --end-of-options guards changed(), preload_check --since and proposal_impact --base. N6: KG_SPECTRAL (and siblings) naming nothing executable exits 2 naming the setting; unset keeps not installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The CI templates read paths and settings one way and refuse what they cannot follow. Changed paths travel NUL-separated and unquoted (git -z, core.quotepath=off) through knowgov-gate.sh, the Claude hook and proposal_impact's branch mode, the helper quoting each into the argv with globbing off: módulo.py no longer reads 'no code changed' (fail-open) and 'new module.py' is no longer 'module.py'. KG_ANNOTATE that the script cannot follow exits 2 before the core command; an unwritable annotation is a warning, no traceback. A KG_BASE starting with '-' is refused and --end-of-options guards every base git reads (N2). proposal-impact.sh exits 0 with a report naming not_read on a branch that adds nothing. preload_check refuses --changed outside the instance alike (absolute or by ..), a directory with no subjects/, and a named linter setting that cannot run (N6); preload-check.sh takes an absolute KG_PRELOAD_BASELINE as given. Tests: check_ci_wrappers through both wrappers (space, glob character, non-ASCII; KG_ANNOTATE; a base of --output=), and tests/ for the hook, branch mode, preload_check and proposal-impact.sh, each failing on main. The record held (the comparator on S1-S7 and J-F, the round trip).
<!-- SECTION:FINAL_SUMMARY:END -->
