---
id: TASK-0051
title: >-
  knowgov-trace register and check: a CI hook from a code change to the
  knowledge
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:41:00Z'
updated_date: '2026-11-03T23:54:00Z'
labels:
  - traceability
  - gate
milestone: m-7
dependencies:
  - TASK-0048
  - TASK-0049
  - TASK-0050
priority: medium
type: feature
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 3 sketch: a platform-neutral command with two subcommands. register records a build's output as a derived node with the assertions it used (store.register_derived, USED_ASSERTION) and its file digests; check, on a later change, finds the registered outputs whose files or whose assertions changed and reports them through the gate's contract (exit 0/1/2, JSON under a schema). Nothing platform-specific in harness/.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 register and check subcommands with explicit inputs, the 0/1/2 exit and a shipped JSON schema
- [x] #2 On the example instance, S6 as acceptance: a registered build becomes suspect after the stage-2 change and check exits 1, naming the APP from code_map.toml
- [x] #3 harness.yml runs the walkthrough on rdflib
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/code_map.py: the code_map.toml reader (moved from tools/check_instance.py, which re-exports it), so harness/ does not import tools/.
2. harness/trace.py, two subcommands, explicit flags only (no CI variables): register --instance --commit --file PATH... [--assertion ID...] --ledger FILE: digests each file under the map's root, names its APP, takes the assertions the task's gate serves (or the named ones), calls store.register_derived(derived:<repo>@<commit>:<path>) and writes the ledger, superseding an entry for the same path. check --instance --ledger [--changed PATH...] [--commit]: re-registers ledger entries the store lost to a reload, then per registered output in scope: drift (digest differs, minor), missing (major), suspect (a used statement now invalidated, blocker, naming its APP); changed code in no glob (major); the task's gate findings (store suspect_derived dropped: the ledger's are reported). Exit 0/1/2, --fail-on, -f json|text, -o.
3. The ledger is needed because a load wipes the store; a registration must outlive the next load.
4. harness/schemas/trace-report.schema.json, validated before print.
5. tools/check_trace_walkthrough.py: example instance, rdflib persisted: gate S6 stage 1, register reference_impl.py, check 0, gate --stage 2, check 1 naming APP-0001; harness.yml runs it.
6. tests/test_trace.py, stdlib: a fake store for register/check; schema; instance README/guide doc.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built as planned. Deviations from doc-0011's sketch, deliberate: a changed code path no row maps is a major finding (unmapped), not exit 2, so a PR adding a file is reported rather than refused to run; the registration also lives in a JSON ledger, because every load wipes the store (gate_cli, run.py, the page), and check re-registers from it what the store lost; suspect is computed from the used statements' current status, not the store's Derived.suspect flag, which a re-registration after the invalidation would not set; --base REF (the core running git diff) is left to the wrappers (TASK-0052), --changed is repeatable; the task is a flag, not a code_map column. The gate's suspect_derived findings are dropped in check: the ledger's are reported. register's assertions default to every statement the task's gate serves at registration (88 on S6 stage 1; 3 of them invalidated by the change, the record's derived:S1:G:run1 count). Verified: tests 166/166 (tests/test_trace.py, five, fake store); tools/check_trace_walkthrough.py on rdflib locally with the pins: register 0, check 0 at stage 1, gate --stage 2 1, check 1 with one suspect blocker naming APP-0001, check --changed drift minor + unmapped major, nothing on a non-code file.

Maintainer's decision (2026-11-03, relayed by the coordinating session): the registrations stay in the JSON ledger beside the client's code; the load is unchanged and does not keep Derived nodes across its wipe.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Adds knowgov-trace, harness/trace.py: register records built files as derived outputs (store.register_derived and a JSON ledger that outlives a load's wipe) with their digest, their APP from code_map.toml and the statements they used; check reports suspect (blocker, naming the APP, the invalidated statements and their successors), missing and unmapped (major), drift (minor) and the task's gate on the store as it is, exit 0/1/2 with --fail-on, JSON pinned by harness/schemas/trace-report.schema.json. The code_map reader moves to harness/code_map.py (check_instance re-exports it). tools/check_trace_walkthrough.py is the S6 acceptance on the example instance; harness.yml runs it on rdflib. Documented in instance/README.md, docs/guide.md and CLAUDE.md; tests/test_trace.py on a fake store. Follow-up: platform wrappers (TASK-0052) map CI variables and git diff to the flags; a Neo4j run of the walkthrough is not in the stack job.
<!-- SECTION:FINAL_SUMMARY:END -->
