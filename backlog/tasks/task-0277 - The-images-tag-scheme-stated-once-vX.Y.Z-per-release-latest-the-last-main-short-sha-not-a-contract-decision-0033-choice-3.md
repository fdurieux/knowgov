---
id: TASK-0277
title: >-
  The image's tag scheme stated once: :vX.Y.Z per release, :latest the last
  main, :<short-sha> not a contract (decision-0033 choice 3)
status: Done
assignee: []
created_date: '2026-11-09T10:09:00Z'
updated_date: '2026-11-09T10:58:00Z'
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
- [x] #1 The README, `instance/README.md`'s contracts table and the image's documentation state the scheme in the same words, with `:<short-sha>` named as not a contract.
- [x] #2 A test holds the documented release form to `release.yml`'s tag expression, and the documented main tags to `demo.yml`'s.
- [x] #3 `CHANGELOG.md`'s Unreleased section names the clarification under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. State the scheme once: :vX.Y.Z for a release, :latest for the last main, :<short-sha> a build of main and not a contract, in the README, instance/README.md's contracts table and the demo's guide.
2. tests/test_image_tags.py holds them to release.yml's github.ref_name tag (after its v<VERSION> check) and demo.yml's two tags.
3. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on PR #421 with task-0276.
- The README, the contracts table (instance/README.md) and the demo's guide (demo/README.md, both places) now say ghcr.io/fdurieux/knowgov:vX.Y.Z for a release (the tag, v included) and :latest for the last build of main, with :<short-sha> a build of main, not a contract. CLAUDE.md's :<tag> became :vX.Y.Z.
- tests/test_image_tags.py:
  - release.yml publishes :${{ github.ref_name }} after its test that the tag is v<VERSION>, on tags v*;
  - demo.yml publishes exactly :${{ steps.sha.outputs.short }} and :latest;
  - the README and the table state the scheme with 'not a contract', and no README, instance/README.md, demo/README.md, docs/security.md or CLAUDE.md names :<version> or :<tag>.
- Checks at 9c07512: run_tests 896/946, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The image's tag scheme is stated once: ghcr.io/fdurieux/knowgov:vX.Y.Z for a release, :latest for the last build of main, and :<short-sha> a build of main, not a contract. It is in the README, instance/README.md's contracts table and the demo's guide. tests/test_image_tags.py holds them to release.yml's tag expression and demo.yml's two tags. A contract clarification under CHANGELOG's Unreleased. PR #421.
<!-- SECTION:FINAL_SUMMARY:END -->
