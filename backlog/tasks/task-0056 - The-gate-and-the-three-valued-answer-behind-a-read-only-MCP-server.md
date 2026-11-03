---
id: TASK-0056
title: The gate and the three-valued answer behind a read-only MCP server
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-03T23:30:00Z'
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
- [x] #1 An MCP client can ask for the gate verdict on a scenario or a key set and receives the same verdict, blocking keys and JSON as harness/gate_cli.py for the same input, checked by a test that compares the two
- [x] #2 An MCP client can ask the three-valued answer for a key and receives asserted, documented absent or unknown with its statements' provenance
- [x] #3 The server exposes no tool that writes to the store, the register or the instance
- [x] #4 It runs against both store adapters (neo4j and rdflib), and the rdflib path is covered by tests that need no container
- [x] #5 It binds to localhost unless the operator configures otherwise, and instance/README.md says how to connect an agent to it
- [x] #6 Any new dependency is pinned in demo/Dockerfile and held by tests/test_demo.py
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. No new dependency: the server is standard library, MCP JSON-RPC 2.0 over stdio (default) and over Streamable HTTP (POST /mcp, JSON responses; GET 405), like the page and the gate command. Conformance checked locally against the official mcp SDK client, which is not added to the image.
2. gate.py: resolve(s, task) delegates to resolve_spec(s, name, spec), so a key set resolves through the same code; the three-valued answer moves from run.d5 into gate.three_valued(s, key), run.d5 unchanged in output.
3. gate_cli.py: the part after the load becomes evaluate(st, ...) -> report; run() and the server both call it, so the same input gives the same JSON by construction and by test.
4. harness/mcp_server.py: tools store_status, gate_verdict {scenario, task | keys, fail_on}, three_valued_answer {key}, all readOnlyHint. The store is wrapped in a read-only view (an allowlist of read operations; an rdflib file is never written back on close); the scenario named must be the one the store holds, as gate_cli --no-load requires. HTTP binds 127.0.0.1 by default; a non-loopback bind needs KG_MCP_TOKEN (Bearer); a foreign Origin is refused (DNS rebinding).
5. tests/test_mcp_server.py, stdlib only: protocol, tool list and annotations, the read-only view, the bind and token rules, Origin, and the report equal to gate_cli.report on a stub store. tools/check_mcp_server.py: the same scenario through gate_cli --no-load and through the server over stdio, JSON equal, plus the three-valued answer against the record's D5; run in harness.yml on rdflib and in the stack job on Neo4j.
6. instance/README.md: connecting an agent (stdio, HTTP, the token). test_demo.py holds that the image gains no package for it.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built as planned. No dependency: mcp_server.py is standard library (JSON-RPC 2.0; stdio, and Streamable HTTP POST /mcp with JSON responses, GET/DELETE 405). gate.resolve -> resolve_spec (a key set resolves through the same gate); gate.three_valued(s, key) is run.d5's logic, run.d5 now calls it (S1 deterministic re-run: 113 leaves, 0 differ). gate_cli.evaluate() is the report after the load; run() and the server both call it.

Verified 2026-11-03: tools/check_mcp_server.py on rdflib, CargoQuote S1-S7 and J-F D1-D5: gate_verdict equal to gate_cli --no-load -f json for every scenario; the three CargoQuote three-valued keys give the record's D5 answers on S1 (documented_absent, asserted, unknown), each statement with artefact and fragments; census unchanged after the server read. Conformance: the official mcp SDK 2.3.0 Client (mode auto: server/discover probe, then the handshake at 2025-11-25) over stdio and over HTTP listed the three tools read-only, called gate_verdict (PROCEED on S1) and three_valued_answer, and got isError for a scenario the store does not hold. The SDK is not in the image. tests/run_tests.py 157/157.

Open: the Neo4j path is the stack job's new step (check_mcp_server --scenarios S1,S2); AC #4 is checked when it is green. The 2026-07-28 stateless revision (server/discover) is not served: clients fall back to the handshake, as the SDK did.

Neo4j, 2026-11-03: the stack job on 4070bee (main with #90 merged in) ran tools/check_mcp_server.py --scenarios S1,S2 inside the app container: "S1: gate_verdict PROCEED (exit_code 0) equals gate_cli --no-load", "S2: ... BLOCKED (exit_code 1)", three-valued keys checked, census unchanged, "MCP server: every check holds". rdflib after the merge, locally: CargoQuote S1-S7 and J-F hold, S6 included with #90 v2 stale findings.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
harness/mcp_server.py serves the gate and the three-valued answer to AI assistants over MCP, read-only and standard library: stdio, or Streamable HTTP at /mcp on 127.0.0.1 (a wider bind needs KG_MCP_TOKEN; a foreign Origin is refused). Tools: store_status, gate_verdict (a task class or an agent's own key set; the report gate_cli --no-load -f json prints, through the shared gate_cli.evaluate) and three_valued_answer (with each statement's provenance). The store sits behind a view that lets the port's reads through and raises on every write; an rdflib file is never written back; nothing is loaded. Refactors with no change in output: gate.resolve_spec, gate.three_valued (from run.d5), gate_cli.evaluate. Verified: tools/check_mcp_server.py on rdflib (both subjects) and on Neo4j in the stack job; the official mcp SDK 2.3.0 client over stdio and HTTP; tests/test_mcp_server.py on a stub store; tests 162/162. Follow-ups proposed, not started: the 2026-07-28 stateless revision (server/discover), and a gate_verdict variant returning the full evidence bundle.
<!-- SECTION:FINAL_SUMMARY:END -->
