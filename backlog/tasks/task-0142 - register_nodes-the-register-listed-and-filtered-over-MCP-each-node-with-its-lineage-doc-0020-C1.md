---
id: TASK-0142
title: >-
  register_nodes: the register listed and filtered over MCP, each node with its
  lineage (doc-0020 C1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-05T22:10:00Z'
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
- [x] #1 A new read-only MCP tool lists the nodes of the register the server reads (KG_REGISTER), each with id, kind, name, state, owner and parent, filterable by kind, state, owner and parent, with a limit and the total; read with the register's own loader, no store
- [x] #2 For one node it returns the lineage: every ancestor by parent up to the root, and the children with their states; on the vendored register CAP-0002 reads CAP-0001 and the listing holds the 8 capabilities
- [x] #3 Its report is pinned by a schema, it is listed in the server's instructions, check_mcp_server.py exercises it, and CHANGELOG Unreleased carries its line
- [x] #4 Served by the read-only knowgov MCP server over stdio and Streamable HTTP, listed by tools/list, admitted by the shipped managed-mcp-allowlist.json by server name with no client change, and named in instance/README.md's MCP section (maintainer, 2026-11-05: "make these functionalities available via the MCP")
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/register_nodes.py: listing and lineage from the register's own loader (register_impact.load_tools), no store.
2. Schema harness/schemas/register-nodes.schema.json; MCP tool entry, dispatch and instructions in harness/mcp_server.py.
3. Tests (tests/test_register_nodes.py), check_mcp_server.py exercise, CHANGELOG, CLAUDE.md, instance/README.md.
4. Served-over-MCP AC: the server process on stdio and HTTP, the managed allowlist by name.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Filters: taxonomy (an addition: the 8 capabilities are the capabilities taxonomy, two of them capability_domain), kind, state, owner (owner field or approved owns link, register_impact.owning_unit), parent (null: roots); limit (default 100, max 1000), offset, total, truncated. node: owning unit and lineage; a cycle or a missing parent ends the climb and is named. Unknown filter values are refused naming the register's. Also a CLI. Verified: tests/run_tests.py 448/448 then 449/449; KG_STORE=rdflib check_mcp_server.py --scenarios S1,S6 every check holds; matrix green at d2a92e7 (tests, rdflib, stack).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
register_nodes, a new read-only MCP tool and command (harness/register_nodes.py): the register KG_REGISTER names listed by id with taxonomy, kind, name, state, owner and parent, filtered by taxonomy, kind, state, owning unit and parent, with a limit, an offset and the total; with node, its ancestors by parent to the root and its children with their states, an annotation and never a walk (decisions 0010, 0014). Schema register-nodes v1; served on stdio and HTTP and admitted by the managed allowlist by name (test); check_mcp_server.py exercises it. Merged in #238 (60259d8). Follow-up: none; task-0143 composes it into the up sequence.
<!-- SECTION:FINAL_SUMMARY:END -->
