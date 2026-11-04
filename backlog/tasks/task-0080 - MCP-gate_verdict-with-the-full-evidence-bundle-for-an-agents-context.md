---
id: TASK-0080
title: MCP gate_verdict with the full evidence bundle for an agent's context
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:55:00Z'
labels:
  - mcp
milestone: m-8
dependencies:
  - TASK-0056
priority: low
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by the task-0056 session: gate_verdict returns the report; an agent building on the knowledge needs the evidence bundle (gate.render_bundle) the arms read.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A read-only tool or option returns the bundle for a task or key set
- [x] #2 tools/check_mcp_server.py holds it equal to what the arms read
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. evidence_bundle tool in harness/mcp_server.py: resolve_spec on the held store (task or key set), render_bundle with arms.policy() and the task's verbatim documents from the kit of the held version (stage 2 when the store holds the change); as_of record by default, as the arms resolve.
2. tools/check_mcp_server.py: per scenario (and S6 stage 2) hold the bundle and its assertion ids equal to render_bundle over resolve(store, codegen) as run.py's arm_runs builds it; and a key set.
3. Unit test on the stub; instance README tool table; CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Local proof: KG_STORE=rdflib check_mcp_server.py every check holds (S1-S7, S6 stage 2); Neo4j 5.26 community S1,S2,S6 every check holds; tests 223/223 plain and jef.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
evidence_bundle, a fourth read-only MCP tool, returns gate.render_bundle over the gate's result for a task or a key set: the policy, superseded_by, lapsed/as_of, preload, the suspect outputs, and the task's verbatim documents from the kit of the held version, as of the record by default (as the arms resolve). It also returns the verdict and the assertion ids. tools/check_mcp_server.py holds it equal to what run.py's arm_runs hands the governed arm, for every scenario, for S6 after the change and re-verification, and for a key set. Proven on rdflib (both subjects) and on Neo4j 5.26 (S1, S2, S6). PR #131.
<!-- SECTION:FINAL_SUMMARY:END -->
