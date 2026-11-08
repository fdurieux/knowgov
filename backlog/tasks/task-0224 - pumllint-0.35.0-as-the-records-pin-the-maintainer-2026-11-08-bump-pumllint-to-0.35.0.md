---
id: TASK-0224
title: >-
  pumllint 0.35.0 as the record's pin (the maintainer, 2026-11-08: bump pumllint
  to 0.35.0)
status: To Do
assignee: []
created_date: '2026-11-08T13:08:00Z'
labels:
  - pins
  - record
  - image
  - pumllint
dependencies: []
priority: high
type: task
ordinal: 224000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08: "bump pumllint to 0.35.0". task-0217 (decision-0018 point 1, step 4) needs pumllint trace --features, which first appears in pumllint 0.35.0 (PyPI); the record pins 0.33.0, the library the sequence-diagram mapper imports. Put to the maintainer with its four parts. Canvas: one pumllint across the record, the image and the lint step, so adopters get the feature trace from the image. Fit/gap: G9-4 (the 0.9.0 image runs every feature) fits only with the bump; the record must be proven equal under 0.35.0. SWOT: S one version everywhere; W a rebuild and a full re-proof; O the record on the current pumllint; T a parse difference moves the record, which stops this task and returns to the maintainer. Advice taken: bump first, then build task-0217 on the pin directly, with no side install (option b dropped unless this task finds the record moves). Places that name 0.33.0 on main at 3b931bb: demo/Dockerfile:22, .github/workflows/harness.yml:62 and :139, tests/test_demo.py:259, tests/test_rdflib_split.py:19, CLAUDE.md:81, docs/security.md:207 (and the linters row :209 if it names pumllint), instance/ci/gitlab/knowgov.gitlab-ci.yml:20, instance/ci/preload-check.yml:27. pumllint imports nothing from knowgov and is installed from PyPI; nothing in pumllint changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every place that names pumllint 0.33.0 as a pin names 0.35.0, and tests/test_demo.py holds the new pin
- [ ] #2 The image is rebuilt with 0.35.0 and the stack job runs on it
- [ ] #3 The scored record (S1 to S7), the deterministic run and the comparator stay equal on rdflib and Neo4j; the sequence-diagram mapper yields the same statements under 0.35.0 as under 0.33.0, shown by a diff of its yield
- [ ] #4 pumllint 0.35.0's trace --features runs from the installed library (a smoke step), for task-0217
- [ ] #5 CHANGELOG.md carries the pin change under Unreleased, and CLAUDE.md's pins line is updated
- [ ] #6 If the record or the mapper's yield moves, the task stops and the before and after go to the maintainer before any merge
<!-- AC:END -->
