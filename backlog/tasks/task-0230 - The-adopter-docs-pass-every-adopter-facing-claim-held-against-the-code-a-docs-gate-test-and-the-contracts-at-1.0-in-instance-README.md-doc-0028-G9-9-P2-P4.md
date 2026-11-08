---
id: TASK-0230
title: >-
  The adopter-docs pass: every adopter-facing claim held against the code, a
  docs gate test, and the contracts at 1.0 in instance/README.md (doc-0028 G9-9,
  P2, P4)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T19:36:00Z'
updated_date: '2026-11-08T19:44:00Z'
labels:
  - docs
  - release
  - contract
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0028 -
    What-a-knowgov-0.9-and-1.0-need-the-record-is-silent-the-version-arithmetic-the-contract-surface-the-gap-lists-proposed.md
priority: high
ordinal: 229000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0028 G9-9 is the last work item before the 0.9.0 cut besides G9-2. #291 fixed two stale claims, but the pass holding every adopter-facing claim against the code (P2) had not run: only docs/reverse-engineering.md was held, by tests/test_reverse_engineering_guide.py. A 0.9.0 that freezes contracts (decision-0016) needs its adopter docs to state the real commands, flags, KG_* settings, paths, endpoints, exit codes, pins and counts. decision-0016 point 3 makes the KG_* settings that instance/README.md or docs/security.md documents, and the page HTTP API as demo/README.md documents it, contracts at 1.0, so a stale doc there is a stale contract. P4: instance/README.md states the contracts at 1.0 in the adopter register. Dispatched by the coordinating session on the maintainer (2026-11-08 19:30Z: "dispatch task-0174 and the docs pass"). Scope: README.md, demo/README.md, instance/README.md, subjects/README.md, docs/guide.md, docs/security.md, docs/reverse-engineering.md, docs/reverse-engineering-preregistration.md, docs/lighthouse-evaluation.md; not CLAUDE.md or the backlog. Limits: no code behaviour change, no pin moved. A KG_* setting the code reads and no doc names is listed for the maintainer, not documented, because documenting it would make it a 1.0 contract. A docs-right, code-wrong finding, or a fix that would change a documented contract, is reported, not made.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every command, --flag, KG_* variable, repository path, HTTP endpoint, exit code, pinned version and stated count in the nine docs is held against main code, and each stale claim found is fixed
- [ ] #2 A stdlib test holds every --flag the docs name to an option of a parser under harness/, tools/ or demo/tools/, every KG_* to a read in code and every repository path to one that exists, with foreign flags in a named allow-list; it fails on main before the fixes
- [ ] #3 instance/README.md has a short section stating the contracts at 1.0 in the adopter register, quoting decision-0016 point 3 without widening it
- [ ] #4 KG_* settings read in code and named by no doc are listed for the maintainer, not documented
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tests/test_adopter_docs.py, stdlib, the code read as text. It holds each of the nine docs to main:
   - every --flag to a parser option under harness/, tools/, demo/tools/, demo/app/, instance/ or the vendored register's tools, or to FOREIGN_FLAGS with its owner;
   - each fenced python command's options to that program's own add_argument;
   - every KG_* name to a read in code;
   - every repository path and relative link, from the root or the doc's folder, to one that exists, and every tests/x.py::name to a test of that file;
   - every /api route to one demo/app/server.py serves.
   Foreign entries are listed with their owner, and one no doc names any more fails. Run on main first: 4 stale claims and 17 foreign flags.
2. Fix what it catches: demo/README's tools/impact.py (x2, the register's tool), its two-walks claim (the page offers two of the register's three; thread is command-line only), the record path missing vendor/, security.md's /api/gaps.
3. Semantic claims (counts, exit codes, defaults, fields, versions, test references, behaviour) are reviewed by three read-only reviewers on a frozen main worktree; each finding is verified against the code before a fix.
4. P4: instance/README.md's last section quotes decision-0016 point 3 verbatim, with a plain-English table of where each is described. Format versions are named as not yet built.
5. DECIDE, not documented: the KG_* read in code and named by no doc, and those named only in demo/README.md (not 1.0 contracts as point 3 reads).
6. CHANGELOG under Unreleased, Changes; suites stdlib, bare and pins.
<!-- SECTION:PLAN:END -->
