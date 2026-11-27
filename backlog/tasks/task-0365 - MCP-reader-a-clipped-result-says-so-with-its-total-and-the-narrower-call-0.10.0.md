---
id: TASK-0365
title: >-
  MCP reader: a clipped result says so, with its total and the narrower call
  (0.10.0)
status: In Progress
assignee: []
created_date: '2026-11-16T20:28:00Z'
updated_date: '2026-11-27T22:13:38Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
priority: medium
ordinal: 355000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-16: "yes, add them as 0.10.0 tasks", after a Claude Desktop session over MCP gave a private subject's counts and links loosely: it summarised a report too large to read whole, carried the wrong count forward, and inferred a subject-to-application link no tool states. A result cut to fit the reader's response limit reaches the assistant without a mark that it is partial, so the assistant generalises from a sample. Ships in 0.10.0 beside task-0364.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every tool result cut to fit carries, in _meta, that it is partial, the full count of what it holds, and how to ask narrowly (the filter or summary argument that fits)
- [x] #2 An uncut result carries no such mark; the mark is the same on both transports and both stores
- [x] #3 check_mcp_server.py holds a clipped and an unclipped case; a schema or the _meta contract documents the fields; CHANGELOG Unreleased under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Decision-0048, option B, taken by the coordinator under the maintainer's delegation:
1. harness/result_marks.py marks a result in two cases:
   - io.knowgov/clipped: register_nodes or scenario_runs past its limit. An over-cap refusal also names its size and the narrower call.
   - io.knowgov/large: an answer whose text is over KG_MCP_CLIENT_BUDGET. Nothing is truncated.
2. Each mark goes in _meta, merged with the era's stamp, and as a text item before the answer, which stays the last text item. A result with no mark is unchanged.
3. KG_MCP_CLIENT_BUDGET is a bounded contract setting (settings.NUMBERS, MCP_SETTINGS, the settings table).
4. harness/schemas/result-meta.schema.json pins the fields.
5. check_mcp_server holds a clipped, a large and a plain case over stdio and HTTP. In-repo content[0] JSON readers move to the last text item.
6. Docs: instance/README.md and the CHANGELOG under Contract changes. decision-0048 is recorded through the CLI.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proven locally, rdflib, pinned clock (2026-11-27):
- check_mcp_server passes on CargoQuote (all scenarios), J-F C,D3 and minimal, and again on S1,S2,S6 after merging main (#602). It holds three cases over stdio and HTTP:
  - clipped: register_nodes 2 of 57 nodes;
  - large: 10,832 characters over a 1,000-character budget;
  - plain: one node's lineage.
- tests/test_result_marks.py: 9 tests, covering both eras, the over-cap refusal and the setting's bounds (exit 2).
- Pinned suite: 1412/1413.
- In-repo readers that parsed content[0] as JSON now read the last text item. They are tests/test_mcp_server.py, test_instance_register_residues.py and test_mcp_subjects.py. lighthouse_evidence reads structuredContent.
- Neo4j is left to the stack job.
<!-- SECTION:NOTES:END -->
