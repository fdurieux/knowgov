---
id: TASK-0090
title: >-
  Publish the page, Neo4j Browser and bolt on 127.0.0.1 by default; refuse the
  default Neo4j password on a wider bind
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T03:18:00Z'
updated_date: '2026-11-04T03:33:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. KG_BIND (default 127.0.0.1) prefixes every published port in demo/docker-compose.yml; the instance overlay and the claude profile publish none.
2. Neo4j starts through demo/neo4j/bind-guard.sh (mounted read-only): a wider bind with NEO4J_AUTH neo4j/kgpoc2026 exits 78 with a message naming KG_NEO4J_PASSWORD; otherwise exec the image's own entrypoint. The app waits on Neo4j's health check, so the stack does not start.
3. tests/test_demo.py holds every compose file's ports to KG_BIND and runs the guard over loopback and wider binds.
4. docs/security.md: a row under What is sent, gap 1 rewritten (the page still has no login), the matrix row and operator practices; test_security's gap check reads KG_BIND and the guard.
5. demo README start section and EC2 route: what changed, how to widen, a new password needs a fresh volume.
6. Prove on Neo4j 5.26 locally: default bind healthy on 127.0.0.1 and refused on the host's address; KG_BIND=0.0.0.0 refused with the default; started with a password of its own; S1 run and comparator identical.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proved locally on neo4j:5.26-community with the image built from this checkout: default bind publishes 127.0.0.1 only (curl and urllib reach localhost; the host's own address 192.0.2.2 refused); KG_BIND=0.0.0.0 with the default password: neo4j exits 78, compose up --wait fails, logs name KG_NEO4J_PASSWORD; KG_BIND=0.0.0.0 with a password of its own on a fresh volume: both healthy on 0.0.0.0; S1 deterministic through POST /api/run then compare_deterministic: 122 leaves, 0 differ; check_saved_queries: every saved query ran. run_tests 277/277 plain and with KG_SUBJECT=subjects/jef_data_load. Neo4j takes its password when its volume is created, so the README says to down -v once before a new password.
<!-- SECTION:NOTES:END -->
