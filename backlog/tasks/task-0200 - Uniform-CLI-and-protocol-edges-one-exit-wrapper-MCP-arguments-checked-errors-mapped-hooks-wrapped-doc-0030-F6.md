---
id: TASK-0200
title: >-
  Uniform CLI and protocol edges: one exit wrapper, MCP arguments checked,
  errors mapped, hooks wrapped (doc-0030 F6)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T15:16:00Z'
labels:
  - review
  - cli
  - mcp
  - hooks
dependencies:
  - TASK-0193
priority: medium
type: bug
ordinal: 200000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

M5: every inputSchema says additionalProperties false and only register_nodes refuses an unknown argument (`gate_verdict {senario: S4}` answers S1 unguarded). M6: an unhashable params.name kills the stdio server. G6 and R9: a malformed baseline, an unwritable -o or review.WallClock exit 1 with a traceback, the code reserved for a finding. G7: --publish commits before the report is validated and written. M10: --host ::1 crashes with exit 1. P8: a hook raised on a malformed report exits 1, which the advisory profile treats as a warning. P9: knowgov-gate.sh's `$(cd ... && pwd)` exits 1 on a mistyped path. G12: schema_check takes true for 1. M5 is a behaviour change (unknown arguments refused), so it gathers for 0.9.0; the rest are fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One exit wrapper for gate_cli, trace, run and transcript maps CannotRun, WallClock, a malformed baseline, an unwritable -o and any unexpected exception to exit 2 with its cause; gate_cli --publish validates and writes the report before commit()
- [x] #2 The MCP servers refuse an argument not in the tool's inputSchema and a non-string tool name with -32602, and map any other exception to -32603 on stdio and HTTP; --host ::1 binds or exits 2
- [x] #3 Every hook's entry maps a malformed report or any exception through decide or refuse to its blocking exit; knowgov-gate.sh exits 2 when a path does not resolve
- [x] #4 schema_check's enum and const compare type as well as value
- [x] #5 CHANGELOG.md has M5's line under Unreleased's contract heading
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/cli_exit.py run() and guard() for gate_cli, trace, run, transcript; G6 baseline and -o as cannot-run; G7 deliver() before commit(). 2. Server: unknown argument and non-string tool/prompt name -32602, catch-all -32603; --host ::1 and a failed bind exit 2. 3. knowgov_hook.entry for every hook; a non-object report refused; knowgov-gate.sh exit 2 on an unresolved path. 4. schema_check same() for enum and const. 5. CHANGELOG: M5 under contract changes, the rest under Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence, tests/test_edges.py (11 tests, each failing on the old code): AC #1 test_the_wrapper_maps_every_failure_to_run_to_exit_2_and_passes_exits_through, test_g6_r9_a_wall_clock_read_and_a_malformed_baseline_exit_2_with_their_cause_no_traceback (also run.py with a pin missing: one line, exit 2), test_g6_an_unwritable_output_exits_2_and_g7_nothing_is_published_before_the_report_is_written; AC #2 test_m5_an_argument_not_in_the_tools_schema_is_refused_in_both_eras_by_both_servers, test_m6_a_non_string_tool_name_is_minus_32602_and_any_other_failure_minus_32603 (stdio loop survives), test_m5_m6_over_streamable_http, test_m10_an_ipv6_host_exits_2_before_any_bind, and check_mcp_server's check_transports on stdio and HTTP; AC #3 test_p8_a_report_that_is_not_an_object_blocks_in_every_profile, test_p8_every_hooks_entry_blocks_on_any_exception, test_p9_the_gate_script_exits_2_when_a_path_does_not_resolve (under bash -e the old script exited 1); AC #4 test_g12_enum_and_const_compare_type_as_well_as_value; AC #5 CHANGELOG. M10: --host ::1 exits 2 (binds IPv4 only), since binding IPv6 would need socket in harness/, which the network scan forbids. Re-pinned for M5: tests/test_mcp_runs.py (start_run's n refused, -32602) and tests/test_register_nodes.py (walk refused by the protocol). Follow-up: wrap tools/preload_check.py once task-0217 merges. Suites before the main merge: stdlib 758/798 (40 skipped), pins 796/798, J-F 795/798; hook tests live 0 fails; comparator 0 differing leaves CQ (rdflib, Neo4j) and J-F; round trip rdflib both subjects and neo4j,rdflib,neo4j CQ; check_mcp_server rdflib S1,S2,S6 and J-F C,D3 and Neo4j S1, check_transports on stdio and HTTP.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
doc-0030 F6, the uniform edges. `harness/cli_exit.py` gives gate_cli, trace, run and transcript one exit: any failure to run, WallClock, a malformed baseline, an unwritable -o, a pin not installed (`guard`) or anything unexpected, exits 2 with its cause in one line, never 1. `gate_cli --publish` checks and writes its report before it publishes. Both MCP servers refuse an argument outside a tool's inputSchema (M5, the contract change) and a non-string tool or prompt name with -32602, map any other failure to -32603 so stdio and HTTP survive, and `--host ::1` exits 2. Every hook runs through `knowgov_hook.entry`, so a crash or a report that is not an object blocks in every profile; `knowgov-gate.sh` exits 2 on an unresolved path; `schema_check`'s enum and const compare type. The record stays equal. Follow-up: `tools/preload_check.py` after task-0217.
<!-- SECTION:FINAL_SUMMARY:END -->
