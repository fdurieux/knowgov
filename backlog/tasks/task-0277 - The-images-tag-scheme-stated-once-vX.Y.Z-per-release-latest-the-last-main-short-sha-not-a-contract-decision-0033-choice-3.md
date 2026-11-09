---
id: TASK-0277
title: >-
  The image's tag scheme stated once: :vX.Y.Z per release, :latest the last
  main, :<short-sha> not a contract (decision-0033 choice 3)
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
ordinal: 270000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The image's tags are stated three ways. The README says `:<version>`. The contracts table says `:<tag>` for a release and `:latest` for the last main. `release.yml` publishes `:v0.8.0`, from `github.ref_name`. `demo.yml` also publishes `:<short-sha>`, which no document names.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 3(a), the contract is `ghcr.io/fdurieux/knowgov:vX.Y.Z` for a release and `:latest` for the last main. `:<short-sha>` is named as a build of main, not a contract.

Source: validation-pass group 1 C6, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The README, `instance/README.md`'s contracts table and the image's documentation state the scheme in the same words, with `:<short-sha>` named as not a contract.
- [ ] #2 A test holds the documented release form to `release.yml`'s tag expression, and the documented main tags to `demo.yml`'s.
- [ ] #3 `CHANGELOG.md`'s Unreleased section names the clarification under Contract changes.
<!-- AC:END -->
