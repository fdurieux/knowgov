---
id: TASK-0227
title: >-
  The page names the knowgov it runs: VERSION, the commit and the distance from
  the release tag, in the header and in /api/subjects
status: To Do
assignee: []
created_date: '2026-11-08T16:51:00Z'
labels:
  - page
  - adopter
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 227000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08, asking why the page shows no knowgov version, then "yes" to building it.

Today the page shows the register's version (the register panel's heading: tag, or describe, or commit) but nothing of knowgov's own. demo/app/server.py sends only the HTTP Server header kg-demo/1. On the EC2 route the stack builds knowgov:local from the checkout (demo/docker-compose.override.yml), so the page runs whatever commit was last pulled, while VERSION reads 0.8.0 until the next release PR: on 2026-11-08 the maintainer's instance was at v0.8.0-277-g7e113f0. A version alone would therefore mislead; the page must name the commit too.

What to show: knowgov's VERSION, the build's commit (short), and its distance from the release tag when known, for example 'knowgov 0.8.0 + 277 (7e113f0)' from a checkout build, or 'knowgov 0.8.0 (v0.8.0)' from the release image. A part that cannot be known reads unknown, never a guess (a release image built without tags, a copy without .git).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The page header shows knowgov's VERSION and the build's commit, with the distance from the release tag when known; a part not known reads unknown, never inferred
- [ ] #2 GET /api/subjects gains an additive knowgov object (version, commit, describe), each null when unknown; nothing else in the response changes
- [ ] #3 The identity is read once at server start from the image's own files (VERSION; .git where the build copied it, or a value the Dockerfile records at build); no network, no wall clock, standard library
- [ ] #4 It reads right in three cases, each with a test or a recorded check: a local build from a checkout (the override's knowgov:local), the published release image (or what the next release image will carry, if 0.8.0's cannot), and the page run from a checkout without Docker
- [ ] #5 demo/README.md says where the page shows it and how to compare it with git -C ~/knowgov describe --tags --always; CHANGELOG under Unreleased > Changes; the record, the pins and the images' pins are unchanged
<!-- AC:END -->
