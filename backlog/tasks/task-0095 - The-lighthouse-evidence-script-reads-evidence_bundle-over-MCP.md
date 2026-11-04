---
id: TASK-0095
title: The lighthouse evidence script reads evidence_bundle over MCP
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T07:29:00Z'
updated_date: '2026-11-04T08:08:00Z'
labels:
  - lighthouse
  - mcp
milestone: m-8
dependencies:
  - TASK-0080
  - TASK-0069
priority: low
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by the task-0080 session: tools/lighthouse_evidence.py (task-0069) rebuilds the bundle itself; reading it through the MCP server's evidence_bundle (task-0080) proves criterion 4 (agent grounding) by the path an agent uses.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 lighthouse_evidence.py takes the bundle from evidence_bundle and the run's evidence is unchanged
- [x] #2 harness.yml's lighthouse step still passes on the PR subset and the full set
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. collect_mcp asks evidence_bundle (as_of record) on the client that asks gate_verdict and three_valued_answer; record verdict, date, version, size, digest, assertions, verbatim; fail when its verdict or date is not gate_verdict's.
2. --transport stdio|http; HttpClient beside StdioClient in tools/check_mcp_server.py (mcp_server.py --http on a free loopback port).
3. No in-process rebuild: check_mcp_server.py already holds the bundle equal to the arms' in the same job; a rebuild costs two more store reads a scenario.
4. Measure the PR subset and the full set on rdflib; docs/lighthouse-evaluation.md (run section, item table, criterion 4); test_security's network guard and docs/security.md for the HTTP client.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured on rdflib in the session container, not a GitHub runner, so the relative cost is what counts: PR subset (cargo_quote S1,S2,S6; jef C,D3) 3m04 on main, 3m31 with the change, uncontended. J-F's mcp item 29 s and 26 s a scenario before, 40 s and 35 s after: each server call opens the store (about 4 s on J-F), the bundle call about 10 s. CargoQuote about 1 s a scenario. No extra server start: the existing per-scenario stdio client is reused (start 0.08 s). An in-process arms comparison was tried and dropped: another 10.6 s a J-F scenario for the proof check_mcp_server.py already gives.
Full set, stdio and http run concurrently: both exit 0, 8m54 and 8m45 contended; every bundle's verdict and date equal gate_verdict's on all 13 scenarios.
Every other item unchanged: evidence-<subject>.json of main's run and this one are equal once timings and the new mcp fields are dropped, both subjects.
tests/run_tests.py 287/287 plain and with KG_SUBJECT=subjects/jef_data_load.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/lighthouse_evidence.py's mcp item reads the evidence bundle through the read-only server's evidence_bundle (as of the record), the path an agent uses, over stdio by default or Streamable HTTP with --transport http (HttpClient in tools/check_mcp_server.py, a loopback server it starts itself). It records the bundle's verdict, date, version, size, digest, assertions and verbatim documents, and fails when its verdict or date is not gate_verdict's. The bundle is not rebuilt here: check_mcp_server.py holds it equal to the arms' in the same job. docs/lighthouse-evaluation.md (run, item table, criterion 4), docs/security.md and test_security's network guard follow. PR subset on rdflib 3m04 to 3m31; full set exits 0 over both transports; every other item byte-equal to main's run; tests 287/287 both subjects. PR #165.
<!-- SECTION:FINAL_SUMMARY:END -->
