---
id: TASK-0204
title: >-
  The two hook bypasses: a spec staged in the commit's own command, and a
  re-pointed capture dir (doc-0030 P2, P4)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
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
- [ ] #1 A git commit whose command stages or names a spec path is gated, or the hook fails closed; git is matched on a word boundary, /usr/bin/git, bash -c and git -C included
- [ ] #2 A change to [capture] dir, and capture-shaped content written anywhere, are blocked as review files are, by tests on both writes
<!-- AC:END -->
