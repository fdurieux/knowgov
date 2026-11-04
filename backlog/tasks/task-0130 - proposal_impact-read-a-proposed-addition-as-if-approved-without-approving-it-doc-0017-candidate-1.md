---
id: TASK-0130
title: >-
  proposal_impact: read a proposed addition as if approved, without approving it
  (doc-0017 candidate 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:25:00Z'
updated_date: '2026-11-04T20:48:00Z'
labels:
  - mcp
  - register
  - proposal
milestone: m-6
dependencies: []
priority: medium
type: feature
ordinal: 130000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0017 §6, candidate 1; maintainer's go of 2026-11-04. An evaluator, `harness/proposal_impact.py`, takes a proposal as an overlay on the register the server reads (`KG_REGISTER`, at its tag): register-shaped nodes (provisional id, kind, name, parent, owner) and links (type, source, target, rationale); each reused node marked `as_is` or `changed`, with optional proposed exceptions. Only the register's own functions decide, loaded by path as `register_impact` loads them: `check_nodes`, `check_relationships`, `check_glossary` on the overlay's elements, `check_coverage`, `impact.walk` with `FORWARD` and `REALISERS`, with or without children. The overlay is read as approved; the register's own draft and proposed elements keep their states. Every overlay element and edge is marked `hypothetical`; the report names the base (tag, commit) and the overlay's digest and is never stored. Report: placement findings; candidates (task-0131); coverage before and after with denominators; reach before and after for every reused node, `changed` ones flagged; what each new node rests on; the keys the reused nodes carry with level, owner and route as `register_impact` reads them under one task class and `as_of`; new elements left unmapped (never unknown); approvals per owning unit. Exposed as a read-only MCP tool `proposal_impact` and a CLI. JSON pinned by a schema under `harness/schemas/`. Journey reuse per decision-0007 (a). knowgov never mints ids or writes register files (doc-0017 candidate 8).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 On the public register, doc-0017's worked example (a new product reusing CAP-0002, a new capability, a journey partly based on an existing one) reports C1 on the two unsupported new steps and C2 on the unrealised new capability, and the walks from CAP-0002 and PROC-0002 reach the new product and journey, each overlay element and edge marked hypothetical
- [x] #2 The same proposal written as draft changes nothing in the register's own checker; nothing is written to KG_REGISTER or the store (digest before and after in a test)
- [x] #3 Keys on reused nodes carry level, owner and route equal to register_impact's for the same node, task and as_of
- [x] #4 proposal_impact is a read-only MCP tool (readOnlyHint), covered by tools/check_mcp_server.py; the tool-count test and instance/README.md's tool table are updated
- [x] #5 Report JSON validates against its schema through harness/schema_check.py; CHANGELOG line under Unreleased (contract addition); a walkthrough in the demo README (doc-0017 candidate 7)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/proposal_impact.py: Overlay (provisional ids, in-memory ids only where malformed or taken), the register's check_nodes/check_relationships/check_glossary on the overlay held proposed, check_coverage and impact.walk/walk_children/realisers on it held approved, every overlay element hypothetical. 2. Keys per reused node as register_impact lands them; levels via gate_cli.evaluate per node, as the MCP tool. 3. Approvals per unit from the link ends' owners. 4. Schema harness/schemas/proposal-impact.schema.json; MCP tool proposal_impact (READ_ONLY); CLI. 5. tests/test_proposal_impact.py on doc-0017's worked example (tools/fixtures/proposal_contract_quote.json); tools/check_mcp_server.py on a live store. 6. demo README walkthrough, instance/README tool table, CHANGELOG, CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Placement runs on the overlay held proposed (the approval block a register PR adds is not asked); coverage and walks on it held approved. Only findings whose where names an overlay element are reported; a node without [source] is an info finding (in no tool yet). Provisional ids well formed for their kind and free are used as given; any other gets the next free id in memory, never reported. A register node a stated link names is reused as_is unless declared. Levels: one gate_cli.evaluate per reused node over its landed keys, so each entry equals the MCP register_impact for that node, task and as_of (test over every task class on the stub; check_mcp_server on rdflib: S1, S6 51 keys on 4 nodes equal, J-F C 0 keys). Tool-count test renamed test_every_tool_listed_and_marked_read_only (same meaning), docs/security.md follows. Evidence: both suites 394/394; deterministic rdflib run 0 differing leaves; draft-file test (scratch register copy) leaves C1-C3 and errors unchanged; register digest and stub writes unchanged.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
proposal_impact (harness/proposal_impact.py, a CLI and a sixth read-only MCP tool) reads a proposed addition against KG_REGISTER as if approved, with only the register's own functions loaded by path: placement, coverage C1-C3 before and after with new gaps, reach before and after per reused node (changed flagged), what each new node rests on, the reused nodes' keys as register_impact reads them, new nodes unmapped, approvals per unit (both end owners on a cross-domain link). Every overlay element hypothetical; nothing stored; no id minted. Report pinned by harness/schemas/proposal-impact.schema.json v1. doc-0017's worked example reproduces §2 (C1 8/11, C2 5/6; the walks from CAP-0002 and PROC-0002 reach PRD-0006 and JRN-0012). PR #211. Limits: decision-0007's (journey reuse through shared processes and D3 only); candidate precision unmeasured until the pilot.
<!-- SECTION:FINAL_SUMMARY:END -->
