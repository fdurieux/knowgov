---
id: TASK-0245
title: >-
  No .env file enters the image: the build context excludes every .env, and the
  compose guidance matches (R4)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - security
  - demo
dependencies: []
priority: medium
ordinal: 239000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
R4 of the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). demo/Dockerfile copies the repository (COPY . /repo) and demo/Dockerfile.dockerignore has no .env rule, while demo/docker-compose.yml:11 invites a .env beside the compose file, inside the build context: a key written there is baked into a locally built image. The release image is built from a clean checkout. Exclude **/.env and **/.env.* (an .env.example, if one is added, stays allowed), hold the rule with a test that builds the context list from the ignore file, and make the compose comment say the file is read for interpolation and never copied into the image.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 demo/Dockerfile.dockerignore excludes .env and .env.* at the root and nested; a test holds it, as tests/test_demo.py holds the Dockerfile
- [ ] #2 demo/docker-compose.yml's comment and docs/security.md agree on where a key may live and that a .env never reaches the image
- [ ] #3 CHANGELOG Unreleased › Changes names it under security
<!-- AC:END -->
