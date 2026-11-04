---
id: TASK-0082
title: >-
  Pre-load check: the remaining linters (Vale or markdownlint, gplint, bpmnlint,
  dmnlint)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:45:00Z'
labels:
  - preload
milestone: m-6
dependencies:
  - TASK-0066
priority: medium
ordinal: 86000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0066 runs Spectral for api-contracts; the kinds with a mapper and a named tool still report unchecked: specification-prose, acceptance-scenarios, bpmn-process-models, decision-tables (.dmn).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each added kind runs its pinned linter through the same exit contract, proven in harness.yml clean (0) and broken (1)
- [ ] #2 kinds.toml and RUNNERS agree; the CI template installs what it runs
- [ ] #3 Kinds not added are listed with the reason
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. RUNNERS: markdownlint (markdownlint-cli2), gplint, bpmnlint, dmnlint; KG_<TOOL> or PATH; instance config at root else instance/ci/; SUFFIXES keeps decision-tables to .dmn.
2. kinds.toml lint.runs for the four; test holds RUNNERS equal.
3. tools/check_preload_linters.py: the example instance's clean files, clean planted files exit 0 and broken exit 1 through instance/ci/preload-check.sh; run in harness.yml with the pins (Node 24).
4. Template preload-check.yml installs the four pinned; README and guide §5; Vale not added, with reason.
<!-- SECTION:PLAN:END -->
