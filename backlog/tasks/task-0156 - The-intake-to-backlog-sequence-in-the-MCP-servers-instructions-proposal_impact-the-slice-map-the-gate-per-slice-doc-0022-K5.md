---
id: TASK-0156
title: >-
  The intake-to-backlog sequence in the MCP server's instructions:
  proposal_impact, the slice map, the gate per slice (doc-0022 K5)
status: To Do
assignee: []
created_date: '2026-11-06T00:08:00Z'
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
- [ ] #1 The server's instructions carry the intake sequence (proposal_impact, slices, gate_verdict per slice) in the same form as the down and up sequences, on both transports; a test pins the text and that every tool it names exists
- [ ] #2 The text says knowgov writes no work item and ranks nothing; K3 is named as parked, not promised
- [ ] #3 CHANGELOG Unreleased carries the line (not a contract change)
<!-- AC:END -->
