---
id: TASK-0142
title: >-
  register_nodes: the register listed and filtered over MCP, each node with its
  lineage (doc-0020 C1)
status: To Do
assignee: []
created_date: '2026-11-05T20:44:00Z'
labels: []
dependencies: []
documentation:
  - doc-0020
priority: medium
type: feature
ordinal: 148000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
An assistant has nowhere to start without an id, and cannot climb the register's hierarchy: register_impact names one parent and never climbs. A listing answers "list all entities" for the register and "what does unit ORG-x own" (a listing, since owns is never walked, decision 0010); lineage answers "what does this sit under". Lineage is an annotation, like the owner, never a reached node: decision 0014 keeps parent out of the walk.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A new read-only MCP tool lists the nodes of the register the server reads (KG_REGISTER), each with id, kind, name, state, owner and parent, filterable by kind, state, owner and parent, with a limit and the total; read with the register's own loader, no store
- [ ] #2 For one node it returns the lineage: every ancestor by parent up to the root, and the children with their states; on the vendored register CAP-0002 reads CAP-0001 and the listing holds the 8 capabilities
- [ ] #3 Its report is pinned by a schema, it is listed in the server's instructions, check_mcp_server.py exercises it, and CHANGELOG Unreleased carries its line
<!-- AC:END -->
