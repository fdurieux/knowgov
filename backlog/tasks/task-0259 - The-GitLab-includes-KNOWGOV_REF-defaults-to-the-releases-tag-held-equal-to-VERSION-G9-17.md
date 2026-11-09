---
id: TASK-0259
title: >-
  The GitLab include's KNOWGOV_REF defaults to the release's tag, held equal to
  VERSION (G9-17)
status: Done
assignee: []
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T10:55:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 253000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`instance/ci/gitlab/knowgov.gitlab-ci.yml` sets `KNOWGOV_REF: main`. An include taken from tag vX therefore clones main's harness at run time unless the default is overridden. That contradicts the README's "you run them from the knowgov tag you pin".

Its `KNOWGOV_PIP` also leaves out the neo4j driver, which a `KG_PUBLISH=1` job against Neo4j needs.

The finding is contract-bearing because it changes a default input of the include.

Source: group 1 C5, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `KNOWGOV_REF` defaults to `v<VERSION>`, and a test holds it equal to `VERSION`, so the release PR moves it with `VERSION`.
- [x] #2 The include's comments and `instance/README.md`'s GitLab section say:
- how to take a later tag;
- what `KNOWGOV_PIP` must add for Neo4j, at the pin from `demo/Dockerfile`.

`tools/check_ci_wrappers.py` passes.
- [x] #3 The GitHub action is checked for the same default. Either it gets the same fix, or the task records why it has none.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. KNOWGOV_REF in instance/ci/gitlab/knowgov.gitlab-ci.yml defaults to v<VERSION>; a test in tests/test_ci_wrappers.py holds it equal to VERSION.
2. The include's comments and instance/README.md's GitLab section: how to take a later tag (the include URL's tag, the default following), and the Neo4j driver at demo/Dockerfile's pin for KNOWGOV_PIP.
3. Check the GitHub action, and the GitHub workflow template instance/ci/preload-check.yml, for the same default.
4. CHANGELOG under Unreleased > Contract changes. Check with tests/run_tests.py and tools/check_ci_wrappers.py.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on PR #411 (branch claude/task-0259-gitlab-ref).
- instance/ci/gitlab/knowgov.gitlab-ci.yml: KNOWGOV_REF defaults to v0.8.0 (v<VERSION>) instead of main. Its comments say a later knowgov is taken by changing the tag in the include's URL, which the default follows; setting KNOWGOV_REF alone would run another release's harness under this release's job. Against Neo4j (KG_STORE=neo4j, and KG_PUBLISH=1 for a later trace job), KNOWGOV_PIP adds neo4j==6.4.1, the driver at demo/Dockerfile's pin.
- The fix covers both templates: instance/ci/preload-check.yml, the GitHub workflow template an instance copies, also defaulted KNOWGOV_REF to main and gets the same default and test (the coordinator, 2026-11-09: keep it, the same defect in the same template class).
- The GitHub action (instance/ci/github/action.yml) needs no default: it calls knowgov-gate.sh from $GITHUB_ACTION_PATH, the checkout of the tag in uses:, and has no KNOWGOV_REF. The new test holds that too.
- instance/README.md: the GitLab section says the default, how to take a later tag, and the Neo4j driver; the pre-load section no longer says 'pin KNOWGOV_REF'.
- tests/test_ci_wrappers.py::test_the_templates_default_to_their_own_release_and_the_action_runs_its_own_checkout fails on the old templates: ('knowgov.gitlab-ci.yml', ['main'], 'v0.8.0').
- Checks: run_tests 881/931, 50 skipped, 0 failed; KG_STORE=rdflib tools/check_ci_wrappers.py runs/wrap-gitlab exit 0. PR #411 was green at 02ddb08 (tests, rdflib, rdflib-readers, stack, the knowgov gate).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The GitLab include's KNOWGOV_REF defaults to the include's own release, v<VERSION>, instead of main, so an include taken from tag vX runs vX's harness. A test holds it equal to VERSION, so the release PR moves the two together. The include's comments and instance/README.md say how to take a later tag (change the tag in the include URL; the default follows) and that a Neo4j job adds the driver at demo/Dockerfile's pin to KNOWGOV_PIP. The same fix covers instance/ci/preload-check.yml, the GitHub workflow template, which had the same default. The GitHub action needs none: it runs from its own checkout, the tag in uses:. A contract change under CHANGELOG's Unreleased. PR #411.
<!-- SECTION:FINAL_SUMMARY:END -->
