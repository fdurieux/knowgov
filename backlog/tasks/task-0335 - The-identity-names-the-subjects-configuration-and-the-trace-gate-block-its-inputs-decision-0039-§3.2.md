---
id: TASK-0335
title: >-
  The identity names the subject's configuration, and the trace gate block its
  inputs (decision-0039 §3.2)
status: Done
assignee: []
created_date: '2026-11-11T22:53:00Z'
updated_date: '2026-11-12T03:47:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 327000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.2 (a), doc-0038 §3.2. Add one additive identity field, configuration: the sha256 of each subject configuration file the load read (subject.toml whole, scenarios.toml, register_map.toml, and plants.toml and queries.toml where read), recorded at load on agent:harness through decision-0038 N2's port write record_inputs and read inputs, on both adapters. gate_cli.differs names it, and the CLI report and MCP gate_verdict carry it, with the gate-report schema updated additively and no version change. The trace report's gate block (harness/schemas/trace-report.schema.json, additionalProperties false) gains corpus, attestations, captures and configuration. check_round_trip and check_mcp_server hold them. A's repros: register_map response rows reduced, scenarios.toml verifications=false, and [rules] vague_words=[] each now move configuration and are named by differs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each of doc-0038 §3.2's three repros moves configuration, and --baseline names it; tests on both stores
- [x] #2 The trace gate block carries corpus, attestations, captures and configuration, equal to the gate report's; schema updated; tests
- [x] #3 check_round_trip and check_mcp_server hold the new fields; the record holds; CHANGELOG's 'names every input' line is true
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #496 (https://github.com/fdurieux/knowgov/pull/496), merged as fbf886f on a whole green matrix with stack. An additive configuration identity field: the sha256 of each subject configuration file the load read (subject.toml, scenarios.toml, register_map.toml, plants.toml and queries.toml where read, and the verification map), recorded at the load on agent:harness through record_inputs and read by inputs on both adapters, compared whole by gate_cli.differs, carried by the CLI report and MCP gate_verdict; the gate-report schema additive with no version change. The trace report's gate block carries corpus, attestations, captures and configuration equal to the gate report's; tools/check_configuration.py the repro tool, in the stack job on Neo4j. Re-checked by group A at fbf886f: FIXED on every point (each of the three repros moves configuration alone and --baseline names it; coverage on CargoQuote and J-F; both stores alike, the round trip neo4j to rdflib and back, MCP stdio equal to HTTP; the trace block equal; a whitespace edit a false differs, never a false same, acceptable; the record 0 differ on both subjects). Residues: Q1 (the pre-load report decides findings and the exit outside the identity, contract-bearing) joins task-0338's R3 in the decision put to the maintainer; Q2 and Q3, fix-only and low, to task-0329.
<!-- SECTION:FINAL_SUMMARY:END -->
