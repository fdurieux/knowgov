---
id: TASK-0144
title: >-
  Store reads over MCP: every key the held scenario holds with its level, every
  derived output built on a key with the statements it used (doc-0020 C3)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-06T00:29:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port reads held_keys, derived_outputs, artefact_assertions in harness/store.py, on Neo4j and rdflib, by id (store.by_id), in store.READS and mcp_server.READS.
2. harness/store_reads.py: held_keys (levels from gate_cli.evaluate over the held key set, the classes requiring each), derived_outputs (key or derived, exclusive; each used statement live, stale, superseded via gate.superseded_by, or rejected), document_statements (a document's statements by version, the outputs built on them).
3. MCP tools on one read handle per call (_with_store), refused mid-run and on another subject's scenario; schemas held-keys, derived-outputs, document-statements.
4. tests/test_store_reads.py (stub store via the server; rdflib fixture); check_mcp_server.py equal to the port's reads at stage 1 and S6 stage 2, listed on both transports; check_round_trip.py compares the reads across store kinds.
5. CHANGELOG Unreleased contract line, CLAUDE.md, instance/README.md.
<!-- SECTION:PLAN:END -->
