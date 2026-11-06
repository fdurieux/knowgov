---
id: TASK-0097
title: >-
  MCP server caches the parsed rdflib snapshot per process, keyed by the
  published file's identity
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T08:46:00Z'
updated_date: '2026-11-06T08:10:00Z'
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
Found by task-0095: on rdflib the MCP server parses the published store file on every call, about 4 s per J-F call, about 30 s a J-F scenario in every MCP step (check_mcp_server, the lighthouse). The first scope, one read handle kept per process, conflicts with store generations (task-0141.06, decision-0014): an rdflib read handle keeps the snapshot it loaded, so a process-long handle would answer from a retired generation after the next publication; a Neo4j read handle is refused after any publication. Rescoped: one read handle per call stays the unit of a logical read, and only the parse is cached, per process, keyed by the published file's (st_dev, st_ino, st_size, st_mtime_ns); a publication is an atomic replace, so it changes the key. Neo4j unchanged: its open is a driver connection and a one-row pin read.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Two calls with no publication between them parse the store file once; a call after a publication answers the new generation, never the retired one (a test across a publication, on a file-backed store)
- [x] #2 check_mcp_server and the lighthouse step pass unchanged, and the step timings in the task notes show the saving on rdflib
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/store_rdflib.py: a read handle's load reads the published file through one descriptor and keys the parse by its fstat identity (path, dev, ino, size, mtime_ns, ctime_ns); the latest parse kept per process (graph, node index, edge indexes, seq) and reused by the next read handle on the same identity; a publication's atomic replace changes the key. Fill under a lock (single-flight for the HTTP transport's concurrent calls). Writers never use or fill it; one read handle per call stays the unit of a logical read; Neo4j unchanged. 2. Shown safe to share: no method in store.READS mutates the graph or its indexes. 3. Tests: two reads parse once; a read after a publication answers the new generation; a held handle keeps its own (decision-0014); 12 concurrent readers parse once and see one generation; a writer neither uses nor fills it. 4. Evidence: check_mcp_server and the lighthouse unchanged in their answers; the MCP step before/after locally on both subjects and on the PR's rdflib job; memory of the cached graph for CargoQuote and J-F; SNAP-01..07 on rdflib; the suites both ways.
<!-- SECTION:PLAN:END -->

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

2026-11-06: the coordinating session accepted the rescope (title, description, ACs) under the maintainer's delegation, on the S2 sub-session's recommendation above. Status To Do, priority low.

2026-11-06, evidence on main at e8717b3 plus this branch, CPython 3.13, rdflib 7.6.0, 4 cores. Shared-graph safety: no method in store.READS (37) mutates the graph or its indexes (an AST walk of each read and what it calls: only local sets and dicts, node() a lookup, _edge() a read). Tests (tests/test_rdflib_snapshot_cache.py): two reads parse once and share the graph; after a publication the next read parses again and sees the new generation, while a handle held across it keeps its own (decision-0014); 12 concurrent read handles parse once and see one generation; a writer neither uses nor fills the cache, and an uncommitted writer leaves it current. Timing, check_mcp_server on the PR subsets, rdflib, sequentially, main then branch: CargoQuote S1,S2,S6 88.9 s -> 36.5 s; J-F C,D3 341.3 s -> 222.6 s; the step 430 s -> 259 s (-171 s, -40%); every check holds both times and the outputs are line-for-line equal once timings, ports and temporary paths are masked. Lighthouse (--only cargo_quote=S1,S2,S6, jef_data_load=C,D3): 144 s -> 100 s, J-F's mcp C 31.0 -> 12.2 s and mcp D3 28.9 -> 13.8 s; the three evidence files equal once timings_s and the checkout paths are removed. Memory of the cached parse (latest only): CargoQuote S1, 0.52 MB of Turtle, 11 985 triples: 14.6 MB retained (tracemalloc), RSS +32 MB; J-F C, 3.47 MB, 69 722 triples: 82.4 MB, RSS +173 MB. SNAP-01..07 on rdflib (tools/check_snapshots.py --disposable): every check holds. Suites: bare venv stdlib 561/581 and KG_SUBJECT=jef 560/581; pinned with KG_TEST_REQUIRE=rdflib 580/581 and 579/581; 0 failed (a parallel run of two suites trips test_subject_check_tool's /tmp scan, each seeing the other's temporary directory; sequential runs pass). The PR's rdflib job gives the CI before/after.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A read handle on a file-backed rdflib store reuses the process's parse of the published file while it is the same publication, keyed by the file's fstat identity (path, dev, ino, size, mtime_ns, ctime_ns) and filled single-flight under a lock; a publication's atomic replace changes the key, so a read never answers from a retired generation, and a held handle keeps its own. One read handle per call, writers and Neo4j are unchanged. check_mcp_server and the lighthouse answer identically; the MCP step on the PR subsets goes 430 s -> 259 s locally, the lighthouse 144 s -> 100 s; the cache holds about 15 MB (CargoQuote) and 82 MB (J-F). SNAP-01..07 hold on rdflib; the suites pass both ways.
<!-- SECTION:FINAL_SUMMARY:END -->
