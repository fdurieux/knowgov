---
id: TASK-0336
title: register_impact walks the thread (decision-0039 §3.3)
status: Done
assignee: []
created_date: '2026-11-11T22:53:00Z'
updated_date: '2026-11-12T01:44:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 328000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.3 (a), doc-0038 §3.3, B-D7. register_impact's walk enum is [dependants, realisers]; FR-06 names thread too. Add walk=thread, using the register's THREAD walk as proposal_impact already loads it (harness/proposal_impact.py), with register_impact's answer shape (edges, reached, keys, gate). It is offered on the MCP tool's inputSchema, the CLI and the page's impact route where it lists walks. check_mcp_server and the page's agreement check hold it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 register_impact walk=thread from a capability and from a process reaches the entities and keys the register's THREAD walk reaches; tests against tools/impact.py
- [x] #2 The MCP inputSchema, CLI and page offer it, and check_mcp_server holds stdio equal to HTTP; the record holds
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #495 (https://github.com/fdurieux/knowgov/pull/495), merged as e6d0619 on a whole green matrix with stack. register_impact walk=thread uses the register's THREAD walk with register_impact's answer shape; the MCP inputSchema enum, harness/store_neo4j.py WALK_STEPS, the page's impact route and its Browser Cypher offer it; check_mcp_server holds stdio equal to HTTP; demo/tools/check_impact_cypher covers 6 walks. register_impact has no CLI of its own (the register's tools/impact.py takes --walk thread), so none was added. Re-checked by group B at e6d0619: FIXED on every point, 342 node, walk and children cases at 0 differences against tools/impact.py on rdflib, Neo4j and J-F, stdio equal to HTTP, the page and its Cypher equal, edge cases (unknown walk -32602, withdrawn and deprecated links not followed, a retired node) and the record 0 differ. B-D7 closed. Low residues R-T1..R-T4 to task-0314.
<!-- SECTION:FINAL_SUMMARY:END -->
