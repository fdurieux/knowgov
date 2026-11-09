---
id: TASK-0242
title: >-
  One task-policy validator at the runtime boundary: a malformed block_levels,
  keys, share or require_approved refuses, never weakens (R1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T07:58:00Z'
labels:
  - gate
  - subject
  - correctness
dependencies: []
priority: high
ordinal: 236000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
R1 of the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). tools/check_subject.py validates block levels only when block_levels is already a list, and harness/tasks.py builds set(spec.get("block_levels", …)), so block_levels = "absent" becomes a set of letters: nothing blocks, the verdict reads QUALIFIED, exit 0. An integer passes the checker and fails at runtime (exit 2). max_unverified_share is coerced by float() at runtime. One validator (types, item values, ranges; no coercion into a weaker policy) serves the checker, the task construction the gate, gate_cli, the MCP reader and run.py use, and the agent-key path; a malformed policy at runtime is the gate contract's exit 2 with the field named. The reviewer's probe (string, integer, list) is the regression case.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 harness/ holds one task-policy validator; tools/check_subject.py and the runtime task construction both call it, and nothing coerces block_levels, keys, max_unverified_share or require_approved into another type
- [x] #2 block_levels = "absent" and = 7 are a check_subject error and, unchecked, a gate exit 2 naming the field; ["absent"] blocks as today; a test holds all three, on gate_cli and the MCP reader's gate_verdict
- [x] #3 The deterministic comparator on both subjects and the round trip pass with the record unchanged; CHANGELOG Unreleased › Changes names the fix
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/task_policy.py: problems() (checker codes) and build() raising TaskPolicyError naming [tasks.<class>] <field>; no coercion.
2. harness/tasks.py builds every class through build(); tools/check_subject.py reports through problems(); LEVELS one list.
3. mcp_server maps TaskPolicyError to an isError result; gate_cli exits 2 through its subject-does-not-load path.
4. tests/test_task_policy.py: the probe on a CargoQuote copy, on check_subject, gate_cli and gate_verdict.
5. CHANGELOG, subjects/README.md, instance/README.md: a malformed class makes the subject unloadable.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-09 evidence.
- AC1: harness/task_policy.py is the one validator. problems(spec) returns {code, field, value, message, hint}, the checker's codes; build(task, spec) raises TaskPolicyError on the first problem. harness/tasks.py builds TASKS through it, and tools/check_subject.py reports through it (LEVELS = task_policy.LEVELS, held equal to gate.ORDER). Nothing coerces: block_levels must be a list of gate levels, keys a non-empty list of strings, max_unverified_share an int or float (not bool) in [0, 1] (an int 0 or 1 is that share), require_approved a bool, rationale a str. tasks.py holds no set( or float(, which the test asserts.
- AC2: tests/test_task_policy.py runs on a temporary copy of CargoQuote. block_levels = "absent" and = 7 each give a check_subject block-level error, gate_cli exit 2 with '[tasks.codegen] block_levels:' on stderr and no report, and an MCP gate_verdict isError result naming the same field (stdio, KG_TODAY pinned). ["absent"]: gate_cli --publish S2 is BLOCKED, exit 1, with response|hold_presence absent; gate_verdict on that store is BLOCKED. The coordinator agreed (2026-11-09) on the fail-closed reading: a malformed class makes the subject unloadable, so every gate call exits 2. This is said in CHANGELOG, subjects/README.md and instance/README.md.
- AC3: comparator CQ 0 differences over 7 scenarios; J-F 0 over 6. Round trip rdflib CQ and J-F C,D3: every answer survives. check_mcp_server CQ S1,S2,S6 and J-F C,D3: every check holds. check_subject on cargo_quote, jef_data_load and minimal: exit 0. check_instance: layout holds. Suites: pins 900/901 (903/904 after d294a03), no PyYAML 844/901, J-F 851/901, 0 failed. CHANGELOG Unreleased > Changes; 0.8.0 byte-identical.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
One task-policy validator for the checker and the runtime (doc-0033 R1). harness/task_policy.py checks every [tasks.<class>] field's type, values and range, and coerces nothing. tools/check_subject.py reports through it, and harness/tasks.py builds every class through it, so the gate, gate_cli, the MCP reader, run.py and the agent-key path read a validated policy.
The reviewer's probe is the regression test. block_levels = "absent" (once a set of letters, so nothing blocked and the gate read QUALIFIED, exit 0) and 7 are now a checker error, gate_cli's exit 2 and an MCP error result, each naming [tasks.codegen] block_levels. ["absent"] still blocks S2. A subject with a malformed task class does not load. The record is unchanged on both subjects.
<!-- SECTION:FINAL_SUMMARY:END -->
