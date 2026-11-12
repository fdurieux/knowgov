---
id: TASK-0341
title: >-
  The identity names the code and suite it compared and the pre-load report it
  applied (decision-0040)
status: Done
assignee: []
created_date: '2026-11-12T08:04:00Z'
updated_date: '2026-11-12T09:19:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 333000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0040 (a), accepted 2026-11-12. Group A's re-checks: R3 (task-0338) an edit to the code or suite files moves the verdict with baseline.differs []; Q1 (task-0335) the pre-load report changes the findings and the exit with every identity field equal. Build two additive identity fields on task-0335's mechanism: code, the raw sha256 of each [reference] code, [oracle] script and [oracle] suite file the load compared, by path, in the load's part selection (subject.code_files); preload, the sha256 of the pre-load report the load applied with its path, or null with why when none was applied. Record both at the load on agent:harness through record_inputs and read them by inputs on both adapters; gate_cli.differs compares each whole (missing or null unknown, A-N1); the CLI report, MCP gate_verdict and the trace report's gate block (trace.gate_identity) carry them; the gate-report and trace-report schemas add them additively with no version change; tools/check_round_trip.py and tools/check_mcp_server.py hold them. Tests must copy subjects with KG_REGISTER set (decision-0039 §3.1).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 R3's repro (edit the suite's expectations, then --baseline against the pristine S1 report) gives baseline.differs ['code'] naming the file's path; an implementation edit likewise; on both stores
- [x] #2 Q1's repro (the example instance's gate with and without its pre-load report, --fail-on minor) gives differs ['preload']; no report reads preload null with why; on both stores
- [x] #3 The CLI report, MCP gate_verdict (stdio and HTTP) and the trace gate block carry code and preload equal; both schemas admit them additively; check_round_trip and check_mcp_server hold them
- [x] #4 The record holds on both subjects (baseline=record reads the new fields as unknown); CHANGELOG line under Unreleased, Contract changes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #505 (https://github.com/fdurieux/knowgov/pull/505), merged as 9b5e126 on a whole green matrix with stack. Two additive identity fields: code, the raw sha256 of each [reference] code, [oracle] script and [oracle] suite file by path (subject.code_digests over code_files; {} when neither table is declared); preload, {path, sha256, why} from preload.identity, path and sha256 null with why when no report is applied. Recorded through record_inputs and read by inputs on both adapters, compared whole by gate_cli.differs (null or missing unknown), carried by the CLI report, MCP gate_verdict and the trace gate block; both schemas additive; check_round_trip and check_mcp_server hold them; tools/check_code_preload.py runs R3, R3b and Q1 (rdflib in the suite, Neo4j in the stack job). Re-checked by group A at 9b5e126 on rdflib and Neo4j with the node linters installed: R3 and Q1 FIXED (a suite, an implementation or a script edit moves code alone and only its path; the pre-load report moves preload alone, none reads null with why; CodePathOutside writes no report, so code is never null in a produced report; a named missing KG_PRELOAD_REPORT is refused, exit 2; round trip neo4j to rdflib to neo4j with --expect-preload; MCP stdio equal to HTTP and preload read from the store; the trace block equal; the record 0 differ on both subjects, baseline=record differs []). Q1's counts reconciled: pumllint alone gives 2 minor and 4 info (exit 1 at --fail-on minor). Residues, fix-only and low, to task-0329: P1 preload compares the path as given, so the same bytes elsewhere differ; P2 the 'store did not answer' prefix on a missing pre-load report, and the code and preload stderr lines print whole maps.
<!-- SECTION:FINAL_SUMMARY:END -->
