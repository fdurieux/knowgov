---
id: TASK-0210
title: >-
  A test task class on CargoQuote, stricter than codegen, rehearsed (doc-0031
  step 1)
status: To Do
assignee: []
created_date: '2026-11-07T08:46:00Z'
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
- [ ] #1 subjects/cargo_quote/subject.toml carries `[tasks.test]` with the 44 keys of doc-0031 section 2, codegen's block levels plus `proposed`, `max_unverified_share = 0`, and a rationale naming `verified_by` as the task's output and G1-G7 as context; a test holds that no `|verified_by` and no `G<n>|` key is among them
- [ ] #2 `gate_cli.py --task test` runs on S1-S7 and on S6 stage 2 (before and after `--reverify`); the verdicts are recorded in the task notes and match doc-0031 section 2, or each difference is explained
- [ ] #3 The comparator over S1-S7 and the codegen record are unchanged; `store_status` lists the class with its rationale; `tools/lighthouse_evidence.py` shows it
- [ ] #4 docs/lighthouse-evaluation.md states that no hook stage uses the class (the hook's stages are plan, spec and push), and CHANGELOG.md's Unreleased names the class
<!-- AC:END -->
