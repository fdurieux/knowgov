---
id: TASK-0056
title: The gate and the three-valued answer behind a read-only MCP server
status: To Do
assignee: []
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-03T22:51:00Z'
labels:
  - lighthouse
  - mcp
milestone: m-8
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: high
type: feature
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0012 §3, V4 = 3: an agent reaches the gate only through gate_cli.py or the harness, while SAP LeanIX, Backstage and Neo4j already serve agents over MCP, and both external reviewers named an MCP surface as the first move. The question an agent should be able to ask is "may I build on this?": the gate's verdict for the keys it needs, and the three-valued answer (asserted, documented absent, unknown) for a key. It must stay a reader: writes to the record remain pull requests, and a private instance must not leak content to whoever connects.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An MCP client can ask for the gate verdict on a scenario or a key set and receives the same verdict, blocking keys and JSON as harness/gate_cli.py for the same input, checked by a test that compares the two
- [ ] #2 An MCP client can ask the three-valued answer for a key and receives asserted, documented absent or unknown with its statements' provenance
- [ ] #3 The server exposes no tool that writes to the store, the register or the instance
- [ ] #4 It runs against both store adapters (neo4j and rdflib), and the rdflib path is covered by tests that need no container
- [ ] #5 It binds to localhost unless the operator configures otherwise, and instance/README.md says how to connect an agent to it
- [ ] #6 Any new dependency is pinned in demo/Dockerfile and held by tests/test_demo.py
<!-- AC:END -->
