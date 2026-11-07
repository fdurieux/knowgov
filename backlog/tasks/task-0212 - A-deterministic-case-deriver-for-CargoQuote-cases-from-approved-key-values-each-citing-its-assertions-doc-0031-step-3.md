---
id: TASK-0212
title: >-
  A deterministic case deriver for CargoQuote: cases from approved key values,
  each citing its assertions (doc-0031 step 3)
status: To Do
assignee: []
created_date: '2026-11-07T08:46:00Z'
labels:
  - evidence
  - tests
  - subjects
milestone: m-8
dependencies:
  - TASK-0211
references:
  - TASK-0051
documentation:
  - >-
    backlog/docs/doc-0031 -
    Generated-test-cases-on-a-green-kit-validated-against-the-records-code-a-test-task-class-a-deterministic-deriver-a-pre-registered-study.-Sense-and-nonsense-opportunity-canvas-fit-gap-SWOT-advice.md
priority: low
type: feature
ordinal: 212000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0031 (step 3). On CargoQuote the expected outcome of a test case can be computed from approved key values without a model: `P1|formula` holds '0.87 * weight_kg + 1.13 * distance_km', `P2|threshold` holds '1244', and the bounds, band edges and failure behaviours are values of the codegen keys. A case that cites the assertions it rests on is a derived output, so after a change like S6's it goes suspect the way `derived:S1:G:run1` does today; a model-written test cannot say which statement it rests on. The frozen oracle's scenarios are data (`SUITE["scenarios"]` in `vendor/tools/acceptance/cargo_quote_suite.py`: stubs, request, expect, must_call, must_not_call, failure_like, with driver-side overlays) that `runner_child.py` drives over code of any interface, so cases in that shape need no generated test code. `harness/` names no subject (task-0002), so the deriver lives under the subject root, as `subjects/jef_data_load/oracle/` does. Running the cases against code is step 4 of doc-0031 (a worker job kind, not created yet); this task derives and checks the cases only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A deriver under subjects/cargo_quote/ (nothing in harness/ or demo/ names it) writes the case families the pre-registration lists, as JSON in the frozen suite's scenario shape plus its overlay, pinned by a schema
- [ ] #2 It derives only from what the gate resolves for `--task test`: on PROCEED every case; on QUALIFIED each case resting on a key below verified marked as an assumption naming its assertion; on BLOCKED no case and exit 1, under the gate contract
- [ ] #3 Every case cites the assertion ids its expected outcome rests on, and every expected value is computed from those assertions' values, never from the kit's files, the frozen suite or reference_impl.py
- [ ] #4 A test holds that no verification scope, suite scenario name or suite file reaches the deriver's input
- [ ] #5 A rerun is byte-identical; S1's case count per family is recorded in the notes; S3 is refused; on S6 stage 2 the verdict before and after `--reverify` is recorded and, where it proceeds, the cases differ from S1's only on the keys the change touched
- [ ] #6 Every case is accepted by runner_child.py's spec format, checked by building the spec without executing any code
- [ ] #7 The case file registers with `harness/trace.py register` citing its keys, and after S6's change `trace.py check` reports it suspect
<!-- AC:END -->
