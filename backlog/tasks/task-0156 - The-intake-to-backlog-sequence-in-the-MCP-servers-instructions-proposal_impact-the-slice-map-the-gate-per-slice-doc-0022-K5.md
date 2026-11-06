---
id: TASK-0156
title: >-
  The intake-to-backlog sequence in the MCP server's instructions:
  proposal_impact, the slice map, the gate per slice (doc-0022 K5)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T00:08:00Z'
updated_date: '2026-11-06T00:57:00Z'
labels:
  - mcp
  - docs
dependencies:
  - TASK-0152
priority: low
type: task
ordinal: 163000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0022 K5, disposition 'Document, after K1' (the maintainer's go on doc-0022's dispositions, 2026-11-05). With task-0152's slice map in proposal_impact's report, the read-only MCP server's instructions (harness/mcp_server.py, the text listed on both transports beside the down and up sequences of task-0143) name the intake sequence an assistant follows for a proposed initiative: proposal_impact on the overlay, its slices section as the story map's backbone, then gate_verdict per slice's keys under one task class and as_of. Work items are written by the tracker, never by knowgov (doc-0022's rejections: no items written, no initiative kind, no scores); K3's backlog coverage stays parked to the pilot. Documentation of tools that exist only: no new tool, no schema change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The server's instructions carry the intake sequence (proposal_impact, slices, gate_verdict per slice) in the same form as the down and up sequences, on both transports; a test pins the text and that every tool it names exists
- [x] #2 The text says knowgov writes no work item and ranks nothing; K3 is named as parked, not promised
- [x] #3 CHANGELOG Unreleased carries the line (not a contract change)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/mcp_server.py INSTRUCTIONS: an Intake sentence after the down and up sequences, same form (tool arg=...): proposal_impact, its slices, gate_verdict per slice under one task class and as_of; knowgov writes no work item and ranks nothing; K3 parked. 2. A test pins the order and the phrases, that every tool the chain names exists, and the same text on initialize and server/discover in-process and over Streamable HTTP. 3. CHANGELOG Unreleased under Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the Intake sentence sits after the up sequence and the files-only note, before 'A status is the repository's'. tests/test_proposal_impact.py test_the_instructions_name_the_intake_sequence_on_both_transports_and_every_tool_they_name_exists: order proposal_impact proposal= < slices < gate_verdict keys= < one task class and one as_of; the phrases 'knowgov writes no work item and ranks nothing', 'the tracker writes the items', '(K3) is parked to the pilot, not offered'; every 'tool arg=' the chain names (proposal_impact, gate_verdict, register_impact, evidence_bundle, register_nodes) in mcp_server.TOOLS; the text equal on initialize and server/discover in-process and over HTTP. CHANGELOG Unreleased › Changes, not a contract change. run_tests.py 510/525 stdlib (15 skipped), 524/525 with rdflib/pyshacl pins and KG_TEST_REQUIRE=rdflib (1 skipped), 0 failed; KG_STORE=rdflib check_mcp_server.py --scenarios S1 every check holds.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The read-only MCP server's instructions name the intake sequence beside the down and up sequences: proposal_impact on the overlay, its slices as the story map's backbone, gate_verdict per slice's keys under one task class and as_of; knowgov writes no work item and ranks nothing, the tracker writes the items, K3 parked to the pilot. Text only: no tool, schema or contract change. A test pins the text, the tools it names and both transports; CHANGELOG Unreleased › Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
