---
id: TASK-0004
title: 'In-memory rdflib adapter: deterministic half and tests run without a container'
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - platform
  - store
milestone: m-1
dependencies:
  - TASK-0003
priority: low
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
shacl.py already builds an RDF projection with rdflib from Cypher reads, and rdflib is in the image. A second adapter proves the port is real and removes the Neo4j container from unit tests and from a first replay-plus-deterministic start. The Neo4j Browser link and saved Cypher stay a Neo4j-adapter feature.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The rdflib adapter passes the deterministic comparator on CargoQuote
- [ ] #2 Unit tests run with no Neo4j service; the container is needed for the Neo4j adapter's own tests only
- [ ] #3 The page says which adapter is active and hides the Browser link when it is not Neo4j
<!-- AC:END -->
