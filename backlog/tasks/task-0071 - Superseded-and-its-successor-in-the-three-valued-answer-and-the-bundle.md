---
id: TASK-0071
title: Superseded and its successor in the three-valued answer and the bundle
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:09:00Z'
labels:
  - gate
milestone: m-8
dependencies:
  - TASK-0056
references:
  - backlog/docs/doc-0013
priority: low
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P5. Superseded is a reading of an invalidated statement that has a verified or approved successor, not a new stored status. Agents see invalidated and miss the successor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The three-valued answer and the gate bundle name superseded_by where a successor exists
- [x] #2 The S6 record shows it after re-verification
- [x] #3 Any schema change is recorded under decision-0003
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate.py: superseded_by(stale) and invalidated_on_key(s, key), read from stale_on_keys; no port change, no stored status; resolve_spec untouched so the deterministic record is unchanged.
2. Bundle and index (render_bundle, render_index) name superseded_by per stale statement.
3. gate_cli report: additive superseded_by map; schema gains the field, not required (contract change, minor under decision-0003); the info finding says superseded by.
4. MCP three_valued_answer: invalidated list with superseded_by.
5. check_mcp_server covers S6 stage 2 --reverify against the record's successors; demo.yml asks S1,S2,S6 on Neo4j; check_gate_after_change holds superseded_by to the record; unit test in test_gate_cli.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR #115. Contract change (decision-0003): gate-report schema gains superseded_by, additive and not required, schema_version stays 2; minor at the next release; CHANGELOG left to the release PR. Proven locally: tests 182/182; rdflib comparator 0 diffs S1-S7; check_mcp_server (S1-S7 + S6 stage 2) and check_gate_after_change on rdflib and on Neo4j 5.26.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An invalidated statement now names its verified or approved successors as superseded_by: in the gate bundle and pull index (gate.render_bundle, render_index), in the gate report (additive superseded_by map; the schema grows, a minor contract change under decision-0003), and in the MCP three_valued_answer (invalidated, each with superseded_by). A reading of stale_on_keys, no stored status, no port change; the deterministic record is unchanged. check_mcp_server covers S6 after --stage 2 --reverify and holds superseded_by to the record's gate_after_reverification successors, on rdflib in harness.yml and on Neo4j in the stack job (S1,S2,S6); check_gate_after_change holds the report's field to the record too.
<!-- SECTION:FINAL_SUMMARY:END -->
