---
id: TASK-0239
title: The tested platforms and clients, stated for an adopter (GAP-06)
status: To Do
assignee: []
created_date: '2026-11-08T23:46:00Z'
labels:
  - docs
  - platform
dependencies: []
priority: medium
ordinal: 234000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The v1.0 scope handover's GAP-06: no adopter document states which operating systems, Python versions, stores, container engines and assistant clients knowgov is tested on. Parts exist: Landlock ABI 3 (docs/security.md, task-0203, K1), POSIX flock (K8), the Claude Desktop test (task-0148 AC #5, K10), GitLab (task-0108), Python 3.12 in the image and 3.11+ for the tools. One adopter-register page or section states the matrix: tested, attested elsewhere, untested. A documentation change, so a 0.9.x patch under decision-0016 point 2; not a cut item.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An adopter-facing section states each platform, store, engine and client as tested (with the CI job or the test), attested (with its evidence) or untested, in plain English
- [ ] #2 tests/test_adopter_docs.py or a sibling holds each tested row to the job or test it names
<!-- AC:END -->
