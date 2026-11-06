---
id: TASK-0097
title: MCP server keeps one read-only store handle per process
status: To Do
assignee: []
created_date: '2026-11-04T08:46:00Z'
updated_date: '2026-11-06T06:16:00Z'
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

2026-11-06 (S2 sub-session), re-read after S2 (task-0141.06, #278, decision-0014). Recommendation: rescope, not close. Reason:
- As written, one read handle kept per process now conflicts with S2. On rdflib a read handle keeps the snapshot it loaded, so a process-long handle would answer from a retired generation after the next publication: a correctness regression, not a saving. On Neo4j a read handle pins one generation and is refused (StoreChanged) after any publication, so a held handle would fail every call after the first publication and must be reopened anyway.
- The saving it measured (~4 s a J-F call) is rdflib's parse of the published file. Neo4j's open is a driver connection and a one-row pin read, not material.
- Rescoped aim: keep one read handle per call, the unit of a logical read under S2. Cache the parsed rdflib snapshot per process, keyed by the published file's identity (st_dev, st_ino, st_size, st_mtime_ns): a publication is an atomic replace, so a new inode reloads it and an unchanged one reuses the parse. Optionally keep the Neo4j driver per process and open a session and pin per call.
- Rescoped ACs: (1) a call after a publication answers the new generation (a test across a publication on both stores); (2) check_mcp_server and the lighthouse step pass unchanged, with the step timings showing the saving on rdflib.
Priority unchanged (LOW): performance only.
<!-- SECTION:NOTES:END -->
