---
id: TASK-0143
title: >-
  Upward joins over MCP with no store: a key to its register nodes, a code file
  to its application, cited keys and ledger entry (doc-0020 C2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-05T22:10:00Z'
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
- [x] #1 From a knowledge key, the tool returns the register nodes its register_map.toml rows name, with the row's owner, anchor and note; an unknown key is refused
- [x] #2 From a code path, it returns the application code_map.toml assigns, the keys its header cites, and the trace ledger's entry (derived id, keys used, commit, digest); a missing code map or ledger is reported unchecked, never as empty
- [x] #3 The instance and ledger paths are server configuration, documented; the tool reads files only and opens no store
- [x] #4 A test on the example instance climbs from a code file to its capability and that capability's ancestors in at most four calls; the server's instructions name the down and up sequences; CHANGELOG Unreleased carries the line
- [x] #5 From a document path, the register links whose evidence cites it (the kit: path, with its anchor), each with the nodes at both ends and their owners, read from the register's files; the document hop doc-0020's table left to the Browser's register-cites query
- [x] #6 Served by the read-only knowgov MCP server over stdio and Streamable HTTP, listed by tools/list, admitted by the shipped managed-mcp-allowlist.json by server name with no client change, and named in instance/README.md's MCP section (maintainer, 2026-11-05: "make these functionalities available via the MCP")
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/upward.py: key_nodes (register_map.toml rows to register nodes), code_path (code_map.app_of, citation.read, trace.read_ledger), document_links (register links whose evidence cites a document, the register_project rule); files only, no store, no walk.
2. Server configuration --instance/KG_INSTANCE, --ledger/KG_LEDGER, read once at start; tool entries, dispatch, instructions naming the down and up sequences.
3. Schemas key-nodes, code-path, document-links; tests/test_upward.py on the example instance; check_mcp_server.py (trace.py register, then code_path and the climb); check_transports on stdio and HTTP and the allowlist.
4. CHANGELOG, CLAUDE.md, instance/README.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Three tools, each one hop: key_nodes (a known key with no row reads mapped false; an unknown one refused), code_path (each leg read or unchecked with its reason; an absolute path, a .. segment or a symlink out of the code root refused), document_links (manifest key, with or without the subject's prefix and #anchor; held equal to register_project's cites for every document). Climb on the example instance: code_path reference_impl.py -> APP-0001; register_impact walk=dependants children=true -> CAP-0002..0004; register_nodes node=CAP-0002 -> CAP-0001: 3 calls. Verified: tests/run_tests.py 465/469 (4 skips from main: rdflib, hook-live), 0 failed; KG_STORE=rdflib check_mcp_server.py on CargoQuote S1,S2,S6 and J-F C,D3, every check holds, check_transports included; #246 tests and stack green, rdflib running at writing.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The upward joins over MCP with no store (harness/upward.py, also a CLI key|code|doc): key_nodes, a key to the register nodes its register_map.toml rows name with owner, anchor and note; code_path, a path under code_map.toml's root to its application, cited keys and trace ledger entry (derived id, keys, statements, commit, digest, drift), each leg read or unchecked, never empty; document_links, the register links citing a document with both ends' nodes and owners, the Browser's register-cites join from files. Instance and ledger are server configuration (--instance/KG_INSTANCE, --ledger/KG_LEDGER). The server's instructions name the down sequence (register_impact realisers, evidence_bundle) and the up one (code_path, key_nodes, register_impact dependants, register_nodes). Schemas key-nodes, code-path, document-links v1; served on stdio and HTTP, admitted by the managed allowlist by name. PR #246. Follow-up: task-0144 (store reads) after task-0141.02.
<!-- SECTION:FINAL_SUMMARY:END -->
