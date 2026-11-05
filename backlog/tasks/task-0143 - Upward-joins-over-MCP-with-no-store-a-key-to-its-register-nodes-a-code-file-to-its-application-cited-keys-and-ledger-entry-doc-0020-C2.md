---
id: TASK-0143
title: >-
  Upward joins over MCP with no store: a key to its register nodes, a code file
  to its application, cited keys and ledger entry (doc-0020 C2)
status: To Do
assignee: []
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-05T20:53:00Z'
labels: []
dependencies:
  - TASK-0142
documentation:
  - doc-0020
priority: medium
type: feature
ordinal: 149000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The chain travels down over MCP but not back up from its two ends. register_map.toml is read only from node to key; harness/trace.py maps a code path to its application (code_map.app_of), the keys its header cites (citation.read) and its ledger entry, but only from the CLI. With these joins, a code file climbs to its capability through register_impact walk=dependants and register_nodes lineage, and the server's instructions name the up and down sequences once, instead of one tool that walks everything both ways (doc-0011's ALL row: every start reached the same 15 nodes).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 From a knowledge key, the tool returns the register nodes its register_map.toml rows name, with the row's owner, anchor and note; an unknown key is refused
- [ ] #2 From a code path, it returns the application code_map.toml assigns, the keys its header cites, and the trace ledger's entry (derived id, keys used, commit, digest); a missing code map or ledger is reported unchecked, never as empty
- [ ] #3 The instance and ledger paths are server configuration, documented; the tool reads files only and opens no store
- [ ] #4 A test on the example instance climbs from a code file to its capability and that capability's ancestors in at most four calls; the server's instructions name the down and up sequences; CHANGELOG Unreleased carries the line
- [ ] #5 From a document path, the register links whose evidence cites it (the kit: path, with its anchor), each with the nodes at both ends and their owners, read from the register's files; the document hop doc-0020's table left to the Browser's register-cites query
- [ ] #6 Served by the read-only knowgov MCP server over stdio and Streamable HTTP, listed by tools/list, admitted by the shipped managed-mcp-allowlist.json by server name with no client change, and named in instance/README.md's MCP section (maintainer, 2026-11-05: "make these functionalities available via the MCP")
<!-- AC:END -->
