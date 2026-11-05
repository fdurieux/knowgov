---
id: TASK-0144
title: >-
  Store reads over MCP: every key the held scenario holds with its level, every
  derived output built on a key with the statements it used (doc-0020 C3)
status: To Do
assignee: []
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-05T20:53:00Z'
labels: []
dependencies:
  - TASK-0141.02
documentation:
  - doc-0020
priority: medium
type: feature
ordinal: 150000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
store_status lists declared keys only and census only counts, so a key held but required by no task class is invisible; derived outputs reach an assistant only when suspect. Both need a new read on both store adapters, which task-0141.02 (S1) reworks first: built before it, they would be built twice.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A read-only tool lists every key the held scenario holds with its level, and says which of them a task class requires
- [ ] #2 A read-only tool returns every derived output built on a key, any state, with the statements it used and whether each is live, stale or superseded; and from a derived output id, the keys and statements behind it
- [ ] #3 Both reads exist on Neo4j and rdflib, enter READS, ride on S1's read-only handle, and check_mcp_server.py holds them equal to the port on a live store; CHANGELOG Unreleased carries the line
- [ ] #4 From a document (an artefact path, and a version where several are held), the statements it yields in the held scenario with their keys, statuses and versions, and the derived outputs that used them
- [ ] #5 Served by the read-only knowgov MCP server over stdio and Streamable HTTP, listed by tools/list, admitted by the shipped managed-mcp-allowlist.json by server name with no client change, and named in instance/README.md's MCP section (maintainer, 2026-11-05: "make these functionalities available via the MCP")
<!-- AC:END -->
