---
id: TASK-0204
title: >-
  The two hook bypasses: a spec staged in the commit's own command, and a
  re-pointed capture dir (doc-0030 P2, P4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T18:04:00Z'
labels:
  - review
  - hooks
  - security
dependencies: []
priority: medium
type: bug
ordinal: 204000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

P2: knowgov_hook.py's spec-commit transition reads `git diff --cached` before the command runs, so `git add x && git commit` and `git commit -m x path` are never gated, and a push through /usr/bin/git, bash -c or git -C is not seen. P4: attestation_paths.py does not guard `[capture]`, so writing notes/c1.toml with [[answer]] tables and then `[capture] dir = "notes"` are both allowed, and every load reads fabricated answers as elicited. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A git commit whose command stages or names a spec path is gated, or the hook fails closed; git is matched on a word boundary, /usr/bin/git, bash -c and git -C included
- [x] #2 A change to [capture] dir, and capture-shaped content written anywhere, are blocked as review files are, by tests on both writes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov_hook.py reads git from the command's tokens (git_calls: shlex with punctuation, git by basename so /usr/bin/git, global options -C/-c skipped, a quoted bash -c/sh -c string read recursively, across &&, ; and pipes); push is any git push so read. A commit is the spec transition when what is staged carries a spec file (as before), or when its own command stages or names one before it runs (_stages_spec: a named spec path, a folder, '.', ':/' or a glob holding a changed one per git status, or -A/-u/-a/-i while one is changed); a command that cannot be tokenised falls back to the pattern and a commit fails closed to spec, as does a worktree git cannot read. attestation_paths.py adds [capture] to the subject.toml tables compared parsed before against after (a re-pointed or added dir blocked, removal passes since captures/ stays guarded) and blocks capture-shaped TOML anywhere (_is_capture: [[answer]], [[unknown]], [capture], an [answered] naming a handle or date; a textual fallback when half-written; a blank questionnaire passes). Tests: test_claude_hook's word-boundary/staging test and test_attestation_hook's capture test, each failing on the code before; run_tests 841/843 with the pins, 795/843 without yaml, skips only. README, CLAUDE.md and CHANGELOG (Unreleased > Changes) updated.
<!-- SECTION:FINAL_SUMMARY:END -->
