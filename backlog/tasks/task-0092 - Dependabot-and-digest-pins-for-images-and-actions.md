---
id: TASK-0092
title: Dependabot and digest pins for images and actions
status: To Do
assignee: []
created_date: '2026-11-04T03:18:00Z'
labels:
  - security
  - ci
milestone: m-8
dependencies:
  - TASK-0059
priority: medium
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0059: no automated dependency updates; python:3.12-slim, neo4j:5.26-community and knowgov:latest are pinned by tag, actions/setup-python@v6 and setup-node@v6 by tag, not by digest or SHA.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 .github/dependabot.yml covers pip, npm, docker and github-actions
- [ ] #2 Base images and the compose image are pinned by digest, the remaining actions by SHA; a test holds the pins
- [ ] #3 docs/security.md's pins section and gap list move with the fix
<!-- AC:END -->
