---
id: TASK-0097
title: MCP server keeps one read-only store handle per process
status: To Do
assignee: []
created_date: '2026-11-04T08:46:00Z'
updated_date: '2026-11-06T00:14:00Z'
labels:
  - mcp
  - ci
milestone: m-8
dependencies:
  - TASK-0095
priority: low
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0095: the MCP server reopens the store on every call, about 4 s per J-F call on rdflib; one read-only handle per process would save about 30 s a J-F scenario in every MCP step (check_mcp_server, the lighthouse).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The server opens the store once per process behind the same read-only view and serves every call from it
- [ ] #2 check_mcp_server and the lighthouse step pass unchanged and the step timings in the task notes show the saving
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-05 (coordinator, doc-0020): task-0141.02 (S1) introduces read-only store handles for page and MCP reads; re-read this task when S1 merges, it may be satisfied or reduced. task-0144 does not depend on it.

2026-11-06: S1 (task-0141.02, #243, af6f0eb) has merged. The MCP server now reads through the port's read handle (open_store(access="read"), store.ReadOnly), and a read handle never publishes. What this task still asks beyond S1, one handle kept per process rather than one per call, is a performance question, not a correctness one; S2 (task-0141.06, generation-pinned reads) changes the reader's lifecycle again. Re-read after S2; until then it stays LOW.
<!-- SECTION:NOTES:END -->
