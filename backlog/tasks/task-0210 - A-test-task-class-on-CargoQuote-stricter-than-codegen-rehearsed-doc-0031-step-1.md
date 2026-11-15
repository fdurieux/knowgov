---
id: TASK-0210
title: >-
  A test task class on CargoQuote, stricter than codegen, rehearsed (doc-0031
  step 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T08:46:00Z'
updated_date: '2026-11-15T16:54:00Z'
labels:
  - gate
  - subjects
  - tests
milestone: m-8
dependencies: []
references:
  - TASK-0101
documentation:
  - >-
    backlog/docs/doc-0031 -
    Generated-test-cases-on-a-green-kit-validated-against-the-records-code-a-test-task-class-a-deterministic-deriver-a-pre-registered-study.-Sense-and-nonsense-opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: feature
ordinal: 210000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0031 (step 1). The design class rationale says "the test-side trace (a requirement's verified_by) belongs to the test stage", yet no test class exists. On 2026-11-07 an MCP session asked whether knowgov knows enough about CargoQuote to write test scenarios, picked its own keys (each REQ's `verified_by`, G1-G7 `title` and `expects_status`) and read BLOCKED. Those keys block the pristine kit too (S1: `REQ-05|verified_by` absent, 14 G keys proposed by construction), because a test-writing task produces `verified_by` and reads the G file as context; doc-0014 C4 wants a mandatory check to read a declared scope, not one an agent picks. Tests are the oracle: in the degradation test 6 of 15 planted defects reached the code, all 6 concealed by the arm's own suite. So the class rests on what a test asserts and is stricter than codegen: doc-0031 section 2 drafted it (`REQ-01..08|text` plus codegen's 36 keys; codegen's block levels plus `proposed`; bar 0) and measured it on a scratch copy: S1 and S6 PROCEED 44/44, S3 BLOCKED on exactly the four proposed band boundaries behind the record's 41-boundary defect, every other scenario as codegen. It is subject content, not a format change; codegen and the frozen record stay untouched. It is the precondition of the deriver (doc-0031 step 3).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 subjects/cargo_quote/subject.toml carries `[tasks.test]` with the 44 keys of doc-0031 section 2, codegen's block levels plus `proposed`, `max_unverified_share = 0`, and a rationale naming `verified_by` as the task's output and G1-G7 as context; a test holds that no `|verified_by` and no `G<n>|` key is among them
- [x] #2 `gate_cli.py --task test` runs on S1-S7 and on S6 stage 2 (before and after `--reverify`); the verdicts are recorded in the task notes and match doc-0031 section 2, or each difference is explained
- [x] #3 The comparator over S1-S7 and the codegen record are unchanged; `store_status` lists the class with its rationale; `tools/lighthouse_evidence.py` shows it
- [x] #4 docs/lighthouse-evaluation.md states that no hook stage uses the class (the hook's stages are plan, spec and push), and CHANGELOG.md's Unreleased names the class
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. [tasks.test] in subjects/cargo_quote/subject.toml per doc-0031 §2 (test_strict). 2. tests/test_subject.py guard. 3. gate_cli --task test on S1-S7 and S6 stage 2 (before/after --reverify), rdflib and Neo4j. 4. Comparator both stores, round trip, check_mcp_server, lighthouse evidence, full suite; task_profile of codegen and design unchanged. 5. docs/lighthouse-evaluation.md, CHANGELOG Unreleased.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verdicts, gate_cli.py --task test --as-of record (rdflib; Neo4j 5.26.0 Community identical in verdict, why and levels on every row):
| Scenario | codegen | test |
|---|---|---|
| S1 | PROCEED 36/36 | PROCEED 44/44 |
| S2 | BLOCKED (2) | BLOCKED (3: REQ-06|text absent, QuoteAPI|on_screening_outage declared_gap, response|hold_presence absent) |
| S3 | QUALIFIED (4 below, 13 flagged) | BLOCKED: S-accept|max, S-review|min, S-review|max, S-refuse|min (proposed) |
| S4 | BLOCKED (outage disputed) | BLOCKED (outage disputed) |
| S5 | BLOCKED (2) | BLOCKED (3, as S2) |
| S6 stage 1 | PROCEED | PROCEED 44/44 |
| S6 stage 2 | BLOCKED (P2|threshold, P2|surcharge invalidated) | BLOCKED (the two P2 keys invalidated, P3|order proposed) |
| S6 stage 2 --reverify | PROCEED, exit 1 (suspect derived output) | PROCEED 44/44, exit 1 (the same suspect output) |
| S7 | BLOCKED (36/36 below) | BLOCKED (19 keys at a blocking level, REQ texts among them, proposed) |
All match doc-0031 §2's test_strict column; S6 stage 2 after --reverify, not in §2, reads as codegen.
Comparator: rdflib 'OK: 0 differing leaf/leaves over 7 scenario(s)'; Neo4j the same line. Record and comparator not edited.
task_profile: codegen 42781013abbc… and design f644a4c5bed0… equal before and after; test 85181c327454…. The gate report's configuration (subject.toml's raw sha256) moves, as for any subject content change.
check_round_trip.py --chain rdflib,rdflib: every answer survives. check_mcp_server.py (rdflib): every check holds (register_impact and proposal_impact under test). store_status lists codegen, design, test with test's rationale. lighthouse_evidence.py: 'Gate, test class (no record): S1 PROCEED, S2 BLOCKED, S3 BLOCKED, S6 PROCEED'; 'store_status lists: codegen, design, test'.
Owner rows: REQ-01..08|text have none in register_map.toml; all eight are among the design class's 21 the sibling session adds (decision-0044 point 3). The other 36 are codegen's, all owned.

Full suite KG_CLOCK=pinned python tests/run_tests.py: 1324/1325 passed, 1 skipped, 0 failed. Final status left to the coordinating session (CI pending).

Merged as fdurieux/knowgov#555 (24ba636), 2026-11-15, on the whole matrix with stack, under decision-0044 point 2 (subject content in 0.9.x with the record untouched). The class's eight REQ-0n|text keys gained owner rows in #557 (decision-0044 point 3).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CargoQuote gains [tasks.test] (doc-0031 §2's test_strict): codegen's 36 keys plus REQ-01..08|text, codegen's block levels plus proposed, bar 0, a rationale naming verified_by as output and G1-G7 as context; tests/test_subject.py guards it. Verdicts on S1-S7 and S6 stage 2 match §2 on rdflib and Neo4j; comparator 0 differing leaves on both, record and comparator untouched; codegen and design task_profile unchanged. The lighthouse doc says no hook stage uses the class; CHANGELOG Unreleased names it. Follow-up: REQ-01..08|text owner rows arrive with the sibling's design-key rows.
<!-- SECTION:FINAL_SUMMARY:END -->
