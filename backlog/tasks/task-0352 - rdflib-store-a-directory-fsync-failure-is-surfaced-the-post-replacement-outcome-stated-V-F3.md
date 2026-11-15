---
id: TASK-0352
title: >-
  rdflib store: a directory fsync failure is surfaced, the post-replacement
  outcome stated (V-F3)
status: In Progress
assignee: []
created_date: '2026-11-15T19:59:00Z'
updated_date: '2026-11-15T19:59:00Z'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 341000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
External validation of 0.9.1 (538618f), finding V-F3: harness/store_rdflib.py _fsync_dir swallows every OSError, from opening the directory and from syncing it, while the adapter's docstring promises a returned commit has its file and directory entry fsynced. ST-06 injects faults only into the file fsync and never reaches the directory path. Reproduced: os.fsync raising EIO on directory descriptors only, the writer's commit still returns. Maintainer approved fixing the fix-validation residuals in 0.9.x on 2026-11-15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A directory sync that is explicitly unsupported (the directory cannot be opened for syncing, or fsync on a directory is refused as not supported) is told apart from a genuine I/O failure, and only the I/O failure is surfaced
- [x] #2 A directory fsync failing with a genuine I/O error makes commit() raise a documented store error, stating the new snapshot may already be visible and its durability indeterminate, never that the old file was restored
- [x] #3 Separate directory-open and directory-sync failure regressions in the ST tests assert the chosen outcome, and fail before the fix
- [x] #4 The durability contract (module docstring, docs) states the outcome
- [x] #5 After the failure the lock is released on close, and the next reader and the next writer work
- [x] #6 gate_cli, run.py and the page map the error to their existing failure-to-run contract (exit 2)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Regressions first: ST-10 in tests/test_store_persistence.py, directory open and directory fsync each failing with EIO (and unsupported errnos) on directory descriptors only.
2. _fsync_dir: tell an unsupported directory sync (open EISDIR/ENOTSUP/EOPNOTSUPP or Windows; fsync EINVAL/ENOTSUP/EOPNOTSUPP) from an I/O failure; raise the latter as an OSError keeping its errno, worded as published-but-indeterminate.
3. Contract: module docstring, docs/security.md, CHANGELOG Unreleased.
4. Checks: suite pinned, rdflib deterministic + comparator, check_snapshots --disposable on rdflib.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
ST-10 (tests/test_store_persistence.py) failed before the fix (directory open EIO and directory fsync EIO each: commit returned) and passes after. Suite pinned 1324/1326, 2 skipped, 0 failed; KG_STORE=rdflib deterministic run + comparator 0 differing leaves over 7 scenarios; check_snapshots --disposable on rdflib: every check holds. Outcome: an OSError keeping its errno (no new exception name), exit 2 through cli_exit for run.py and gate_cli; the page's run is a run.py child (exit 2 -> failed), its projection route answers 503 with the message.
<!-- SECTION:NOTES:END -->
