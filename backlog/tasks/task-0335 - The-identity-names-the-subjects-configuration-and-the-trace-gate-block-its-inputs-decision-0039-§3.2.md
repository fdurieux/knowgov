---
id: TASK-0335
title: >-
  The identity names the subject's configuration, and the trace gate block its
  inputs (decision-0039 §3.2)
status: To Do
assignee: []
created_date: '2026-11-11T22:53:00Z'
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
- [ ] #1 Each of doc-0038 §3.2's three repros moves configuration, and --baseline names it; tests on both stores
- [ ] #2 The trace gate block carries corpus, attestations, captures and configuration, equal to the gate report's; schema updated; tests
- [ ] #3 check_round_trip and check_mcp_server hold the new fields; the record holds; CHANGELOG's 'names every input' line is true
<!-- AC:END -->
