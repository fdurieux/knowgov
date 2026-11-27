---
id: TASK-0364
title: >-
  gate_verdict: a summary mode that returns counts by owner unit, level,
  severity and kind, the full findings only on request (0.10.0)
status: Done
assignee: []
created_date: '2026-11-16T20:24:00Z'
updated_date: '2026-11-27T20:58:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
priority: medium
ordinal: 354000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer asked a Claude Desktop session over MCP for a private subject's gate verdict (197 keys). The full report was about 156,000 characters, over the reader's response limit; the assistant read it back from a saved file and summarised it, and stated one count wrongly (every key's owner as one unit, where the report holds 104 and 93 across two). A large subject's report is too big for an assistant to read whole. The maintainer, 2026-11-16: "yes, note the gate_verdict summary mode for 0.10.0"; it joins 0.10.0 beside decision-0047's tools, an additive contract change in the same restarted soak.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 gate_verdict takes an optional argument selecting a summary: the verdict, why, the bar, the identity fields, and counts by owner unit, by level, by severity and by finding kind, with no per-key findings
- [x] #2 The default answer is unchanged (no existing caller sees a difference), unless the coordinator records otherwise in the PR with the reason
- [x] #3 The summary's counts equal those computed from the full report on the same store, on Neo4j and rdflib and over both transports; check_mcp_server.py holds it; a schema for the summary shape
- [x] #4 A finding filter (by owner, level, kind or key) returns only those findings, so an assistant can ask narrowly instead of reading the whole report
- [x] #5 CHANGELOG Unreleased under contract changes; the MCP reader docs name the summary as the first call for a large subject
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/gate_summary.py: summary(report, spec) and filtered(report, filter), pure, over the one report gate_cli.evaluate builds.
2. gate_verdict gains summary (boolean) and filter (owner, level, kind, key, severity) in its inputSchema. Summary selects harness/schemas/gate-summary.schema.json (mcp_server.output_schema). Filter keeps gate-report, with an optional filter block. With neither, the answer is the report unchanged.
3. filter.key is NFC'd and held raw and in NFC, -32602, as every key argument is. An empty filter, or a filter beside summary, is refused.
4. check_mcp_server recomputes every count from the full report on every scenario and stage 2, checks every owner and kind filter plus the blocker filter, and compares over stdio and HTTP. Neo4j is covered by the stack job.
5. Docs: the tool description and instance/README.md name the summary as the first call. The CHANGELOG gets a line under Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Design:
- by_owner counts findings by their owner field, so every count can be recomputed from the full report (AC3). Owner null collects findings no single unit answers for, plus those of a kind that names no owner (task, suspect_derived, preload). That is exactly what filter owner=null returns.
- by_level counts required keys by level, from levels.
- The summary's baseline gives its lists as counts.

Proven locally, rdflib, pinned clock (2026-11-27):
- check_mcp_server passes on CargoQuote (all 7 scenarios, S6 stage 2 included), J-F C,D3 and minimal. On every scenario and over stdio and HTTP, summary counts equal those recomputed from the full report, and each owner, kind and blocker filter returns exactly the report's findings.
- tests/test_gate_summary.py: 6 tests.
- test_mcp_output_schemas validates summary and filter calls on both public subjects.
- The default answer is byte-identical to main 510762c's on one store, under codegen, design and fail_on=info. The only difference is the knowgov build commit.
- Pinned suite 1403/1404; unpinned 1289/1404, 0 failed.
- Neo4j is left to the stack job.
- Fixed on the way: the bar's block_levels come from a set, so they differed between processes. They are now listed in the gate's level order.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in knowgov #601 (9a20b8d), merged on the whole matrix green with stack. gate_verdict gains summary (verdict, why, bar, identity fields, counts by severity, kind, level and owner, no findings; schema gate-summary) and filter (owner, level, kind, key, severity; the full report with only the matching findings and a filter block with matched and total; the verdict, exit_code, counts and levels stay the whole report's). The default answer is unchanged. check_mcp_server.py recomputes every count from the full report on every scenario and on S6 stage 2, over stdio and HTTP, on rdflib and Neo4j. Set-ordered block_levels now come out in gate order.
<!-- SECTION:FINAL_SUMMARY:END -->
