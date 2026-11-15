---
id: TASK-0349
title: 'check_worker EXEC-01: a failed or empty probe fails the isolation check (V-F2)'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-15T19:38:00Z'
updated_date: '2026-11-15T21:49:00Z'
labels:
  - worker
  - containment
dependencies: []
references:
  - tools/check_worker.py
priority: high
type: bug
ordinal: 341000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
External validation of 0.9.1 (538618f), finding V-F2: EXEC-01 in `tools/check_worker.py` read `last_json(r) or {}` and then checked only that the canaries were absent and the environment a subset of the allowlist. A probe that exited 1 with no output (its one print suppressed when `open("/proc/1/environ")` raised) passed all three, "the job's environment is the allowlist: []" included, and the CI artefact for that commit records `allowlist: []`: no leak shown, but no probe shown either. The worker's environment and confinement are not in question; the check's power to prove them is. Fix approved by the maintainer for 0.9.x on 2026-11-15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 EXEC-01 requires the probe's exit 0 and a result of the expected shape (an object whose `env` is a non-empty object of strings) before it judges the canaries absent
- [x] #2 EXEC-01 requires positive witnesses in the job's environment, `PATH` and `KG_SUBJECT` as the app set it, and names them in its line
- [x] #3 The probe emits the job's environment before and apart from the worker parent's, and reports the parent-environment access as its own field: read, or refused with the error named; an expected refusal is explicit evidence, a missing field a failure
- [x] #4 Negative controls over the pure evaluation fail the check for a non-zero exit, missing or invalid JSON, missing environment keys and a leaked synthetic canary, and pass a well-formed clean result
- [x] #5 The suite passes under `KG_CLOCK=pinned`; the stack job's EXEC-01 lines name the witnesses
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pure exec_01(r, canaries, store_pw, subject_id) in tools/check_worker.py, the probe text as EXEC01_PROBE.
2. Probe prints the job's environment on its own flushed line, then the parent's environ access as {'read'|'refused': ...} on a second line.
3. exec_01 gates: ran (exit 0, stage ok) -> shape (two lines, env non-empty object of strings, parent read or refused by name) -> witnesses (PATH == worker.JOB_PATH, KG_SUBJECT absolute .../subjects/<id>) -> canaries, store password, allowlist; each later line fails with the first.
4. worker.JOB_PATH and JOB_ENV named once in harness/worker.py, the check's allowlist and witness read from them; an AST test holds run_job's env to them.
5. tests/test_check_worker_exec01.py: negative controls (V-F2 repro, non-zero exit, timeout, missing/invalid JSON, missing keys, leaked canary, store password) and the clean pass; the probe run locally with an unopenable environ.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Negative controls (tests/test_check_worker_exec01.py) against the pre-fix inline logic, replayed in a scratch script: V-F2 repro (exit 1, no output), non-zero exit with a clean answer, timeout, env {}, no PATH, no KG_SUBJECT all printed ok before and fail now; a leaked canary failed before and fails now. Suite under KG_CLOCK=pinned: 1229/1333 passed, 104 skipped (rdflib not installed here), 0 failed. Complexity ratchet: exec_01 split into _exec01_result/_lines/_shaped/_witnessed (each under 15); main fell 44 to 41, baseline tightened. Real worker not run here: Landlock ABI 7 and dockerd were available but Docker Hub refused the base image pull (429); the stack job runs EXEC-01 on a real worker.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
EXEC-01 now fails a probe that did not run or answered nothing: it requires exit 0, the result's shape, positive witnesses (PATH, KG_SUBJECT) and the parent-environment access as its own field; pure-evaluation negative controls cover a non-zero exit, bad JSON, missing keys and a leaked canary. Merged in #562 (96a642f). Stack job on main's merge of #569 (b2dcc5b) names the witnesses: PATH and KG_SUBJECT as expected, the parent refused with PermissionError, the environment equal to the 7-name allowlist.
<!-- SECTION:FINAL_SUMMARY:END -->
