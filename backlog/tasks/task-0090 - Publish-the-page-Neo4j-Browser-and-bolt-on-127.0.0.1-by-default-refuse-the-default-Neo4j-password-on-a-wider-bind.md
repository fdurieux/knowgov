---
id: TASK-0090
title: >-
  Publish the page, Neo4j Browser and bolt on 127.0.0.1 by default; refuse the
  default Neo4j password on a wider bind
status: To Do
assignee: []
created_date: '2026-11-04T03:18:00Z'
labels:
  - security
milestone: m-8
dependencies:
  - TASK-0059
priority: high
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0059 (docs/security.md, gaps): the compose stack publishes 8080, 7474 and 7687 on every interface; the page has no login and POST /api/run can start a run that calls the model; Neo4j keeps the default password kgpoc2026. On a shared host that is an open door.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The compose files bind 8080, 7474 and 7687 to 127.0.0.1 unless a named variable widens the bind
- [ ] #2 With a wider bind the stack refuses to start while the Neo4j password is the default
- [ ] #3 docs/security.md, the demo README and test_security.py's gap list move with the fix; the stack job still passes
<!-- AC:END -->
