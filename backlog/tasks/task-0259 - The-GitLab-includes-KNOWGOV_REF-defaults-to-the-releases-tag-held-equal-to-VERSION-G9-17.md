---
id: TASK-0259
title: >-
  The GitLab include's KNOWGOV_REF defaults to the release's tag, held equal to
  VERSION (G9-17)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
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
- [ ] #1 `KNOWGOV_REF` defaults to `v<VERSION>`, and a test holds it equal to `VERSION`, so the release PR moves it with `VERSION`.
- [ ] #2 The include's comments and `instance/README.md`'s GitLab section say:
- how to take a later tag;
- what `KNOWGOV_PIP` must add for Neo4j, at the pin from `demo/Dockerfile`.

`tools/check_ci_wrappers.py` passes.
- [ ] #3 The GitHub action is checked for the same default. Either it gets the same fix, or the task records why it has none.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
