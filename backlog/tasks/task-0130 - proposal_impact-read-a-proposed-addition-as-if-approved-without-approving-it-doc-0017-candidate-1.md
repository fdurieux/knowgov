---
id: TASK-0130
title: >-
  proposal_impact: read a proposed addition as if approved, without approving it
  (doc-0017 candidate 1)
status: To Do
assignee: []
created_date: '2026-11-04T20:25:00Z'
updated_date: '2026-11-04T20:25:00Z'
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
- [ ] #1 On the public register, doc-0017's worked example (a new product reusing CAP-0002, a new capability, a journey partly based on an existing one) reports C1 on the two unsupported new steps and C2 on the unrealised new capability, and the walks from CAP-0002 and PROC-0002 reach the new product and journey, each overlay element and edge marked hypothetical
- [ ] #2 The same proposal written as draft changes nothing in the register's own checker; nothing is written to KG_REGISTER or the store (digest before and after in a test)
- [ ] #3 Keys on reused nodes carry level, owner and route equal to register_impact's for the same node, task and as_of
- [ ] #4 proposal_impact is a read-only MCP tool (readOnlyHint), covered by tools/check_mcp_server.py; the tool-count test and instance/README.md's tool table are updated
- [ ] #5 Report JSON validates against its schema through harness/schema_check.py; CHANGELOG line under Unreleased (contract addition); a walkthrough in the demo README (doc-0017 candidate 7)
<!-- AC:END -->
