---
id: TASK-0217
title: >-
  Step 4's checks in preload_check: pumllint trace --features, the glossary
  check, the DMN gap check (decision-0018 point 1)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T13:40:00Z'
labels:
  - process
  - reverse-engineering
  - preload
dependencies:
  - TASK-0216
  - TASK-0224
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: feature
ordinal: 217000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 1, step 4 (doc-0032 §2 step 4 and §10 item 3). pumllint's trace --features, the lab's glossary check and its DMN gap check (gaps, overlaps, untyped outputs; pumllint recreate_experiment/harness/glossary_check.py and dmn_check.py) find what the experiment found, but they do not run in tools/preload_check.py. Port or call them so the lint step runs them on a kit and the gathered artefacts, under the gate contract's exit codes, their findings feeding task-0216's routed gaps. Provisional on F6 (task-0200, the uniform exit wrapper): use today's exit handling and say what F6 will change. pumllint is a released library knowgov installs; nothing is copied from pumllint's lab without its licence and a SOURCE note, and pumllint imports nothing from here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 preload_check runs the three checks on an instance's documents of the kinds they read, each finding in the preload report with its tool
- [ ] #2 A kind whose check cannot run here is listed as unchecked, as today
- [ ] #3 tools/check_preload_linters.py proves each check finds its planted defect
- [ ] #4 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/step4_checks.py: the trace (pumllint trace --features on the harness's pinned pumllint; unchecked naming 0.35.0 when older, or without the instance's requirement-id pattern), the glossary check and the DMN gap check, both reimplemented from the published description (pumllint is GPL-3.0-or-later: nothing of the lab copied).
2. preload_check: the checks after the kinds' linters; each finding names its check as tool; a checks block; a document its kind's linter left unchecked and a check read is judged by the check alone; one settle pass for every row; a failing check is cannot-run.
3. preload.verdicts and lint_gaps: a finding's own tool and version, so task-0216's gaps name the check.
4. Schema (additive): finding tool, checks block.
5. check_preload_linters part 4: each check on its planted defect, the trace on the pinned pumllint (exit 2 on one older than 0.35.0).
6. instance/README (adopter register: which pumllint the trace needs), CHANGELOG, tests failing on the old code first.
7. Built after task-0224 (pumllint 0.35.0 as the pin) merges.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08: the maintainer chose to bump pumllint to 0.35.0 as the record's pin (task-0224). task-0217 is built after task-0224 merges, calling pumllint trace --features from the pinned library directly; the side install (option b, approved by the coordinator earlier the same day) is dropped unless task-0224 finds the record moves, in which case option b resumes.

Plan amended (coordinator, on the maintainer's word, 2026-11-08): pumllint 0.35.0 becomes the record's pin through task-0224; option (b) dropped. The trace runs the harness's pumllint (preload_check.pumllint_cmd); KG_PUMLLINT_TRACE and the side install are gone; an older pumllint leaves the trace unchecked naming 0.35.0, and check_preload_linters exits 2 on it. The PR waits for task-0224 on main. Evidence on the build before the amendment: four suites 0 failed (bare 741/778, J-F bare 741/778, pinned 776/778, pinned J-F 775/778); comparator 0 diffs S1-S7 and J-F; round trip --chain --expect-preload rdflib (S1, S6) and neo4j,rdflib,neo4j (S1); plain round trip both subjects; check_mcp_server, check_gate_after_change, check_lint_gaps on Neo4j hold. After it: check_preload_linters holds on pumllint 0.35.0 with the Node linters and exits 2 on 0.33.0. The example's screening table has two DMN gaps (41 to 42, 66 to 67 on a number input): found, not fixed, the kit being vendored.
<!-- SECTION:NOTES:END -->
