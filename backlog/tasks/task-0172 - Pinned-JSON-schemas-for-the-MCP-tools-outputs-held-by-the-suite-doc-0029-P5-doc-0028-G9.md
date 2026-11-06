---
id: TASK-0172
title: >-
  Pinned JSON schemas for the MCP tools' outputs, held by the suite (doc-0029
  P5, doc-0028 G9)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T13:03:00Z'
updated_date: '2026-11-06T13:26:00Z'
labels:
  - mcp
  - contracts
dependencies: []
priority: medium
ordinal: 173000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0029 advice 1. The MCP reader's and knowgov-runs' tool outputs are contracts at 1.0 under decision-0016 point 3 (proposed), but only harness/schemas/ pins JSON shapes today (gate, trace, preload, subject-check, register-nodes, key-nodes, code-path, document-links, held-keys, derived-outputs, document-statements, proposal-impact); other tool outputs are described in prose only, and task-0168 noted run_options has none. Add a schema per tool output not yet pinned, check every tool's output against its schema in the suite through harness/schema_check.py (standard library), and name each schema in the tool's description. Additive: no output changes shape. If the key-check PR (task-0171, another session) changes run_options first, rebase onto it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every tool the MCP reader and knowgov-runs list (both transports) has a JSON schema for its output under harness/schemas/, or names the existing one it returns
- [x] #2 A test calls each tool on the public subjects (rdflib, no network) and validates the output against its schema with harness/schema_check.py; a field added without the schema fails it
- [x] #3 Each tool's description names its schema; no output changes shape; CHANGELOG line under Unreleased > Changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Record every answer check_mcp_server reads on the full sets of both subjects; draft each missing schema from the code and those answers, every object closed.
2. mcp_server.OUTPUT_SCHEMAS and mcp_runs.OUTPUT_SCHEMAS; each description ends naming its schema.
3. tests/test_mcp_output_schemas.py: files-only tools (stdlib), store-backed (rdflib) and knowgov-runs (stub page), both subjects, a stray field refused.
4. check_mcp_server validates every answer it reads (stdio, HTTP, Neo4j in stack).
5. run_options follows #304 (worker) and #307 (key_check) once merged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
New schemas: store-status, three-valued-answer, evidence-bundle, register-impact, list-subjects, scenario-runs, scenario-result, run-options, run-started, run-status; the other ten tools name gate-report, register-nodes, key-nodes, code-path, document-links, held-keys, derived-outputs, document-statements, proposal-impact, subject-check.
No output changes shape: 1813 answers recorded from check_mcp_server on every scenario of both subjects (stdio and HTTP) validate against them.
Suites: stdlib 611/633, pinned 637/638, 0 failed; check_mcp_server rdflib holds on cargo_quote S1,S2,S6 and J-F C,D3 with every answer validated.
run-options carries execution, arms_ready and worker (task-0169, #304); key_check (task-0171, #307) is added when it merges. MCP outputSchema left out (coordinator, 2026-11-06).
<!-- SECTION:NOTES:END -->
