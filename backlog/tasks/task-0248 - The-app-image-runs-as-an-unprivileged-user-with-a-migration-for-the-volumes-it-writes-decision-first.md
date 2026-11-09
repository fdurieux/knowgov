---
id: TASK-0248
title: >-
  The app image runs as an unprivileged user, with a migration for the volumes
  it writes (decision first)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - security
  - demo
  - image
dependencies: []
priority: low
ordinal: 242000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033) (Sonar docker S6471 and the root default). demo/Dockerfile has no USER, so the app container runs as root; the worker already runs as 65534:65534 (compose). Running the app unprivileged is right in principle, but it changes who owns runs/ and the store volumes, so an upgrade needs a migration step and a note; it belongs with a release that can carry one (doc-0033 advice 4).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts chooses the user, the release and the migration
- [ ] #2 If built: the stack job runs the app unprivileged, existing volumes are migrated by a documented step, and docs/security.md says so
<!-- AC:END -->
