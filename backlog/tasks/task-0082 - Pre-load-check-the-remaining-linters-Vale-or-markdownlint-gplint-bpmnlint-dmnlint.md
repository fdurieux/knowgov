---
id: TASK-0082
title: >-
  Pre-load check: the remaining linters (Vale or markdownlint, gplint, bpmnlint,
  dmnlint)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:12:00Z'
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
- [x] #1 Each added kind runs its pinned linter through the same exit contract, proven in harness.yml clean (0) and broken (1)
- [x] #2 kinds.toml and RUNNERS agree; the CI template installs what it runs
- [x] #3 Kinds not added are listed with the reason
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. RUNNERS: markdownlint (markdownlint-cli2), gplint, bpmnlint, dmnlint; KG_<TOOL> or PATH; instance config at root else instance/ci/; SUFFIXES keeps decision-tables to .dmn.
2. kinds.toml lint.runs for the four; test holds RUNNERS equal.
3. tools/check_preload_linters.py: the example instance's clean files, clean planted files exit 0 and broken exit 1 through instance/ci/preload-check.sh; run in harness.yml with the pins (Node 24).
4. Template preload-check.yml installs the four pinned; README and guide §5; Vale not added, with reason.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR #132. Runners added; harness step proven locally with real pins (Node 22 warns for bpmnlint 12/dmnlint 2; CI uses setup-node 24). Vale not added: ships no rules of its own. The example's quote_process.bpmn fails bpmnlint:recommended (97 errors: no BPMNDI, no incoming/outgoing): vendored, not edited. GitLab include and composite action leave linter installs to the caller, as for Spectral.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/preload_check.py runs markdownlint (markdownlint-cli2 0.24.0) for specification-prose, gplint 2.6.0 for acceptance-scenarios, bpmnlint 12.0.0 for bpmn-process-models and dmnlint 2.0.0 for the .dmn files of decision-tables (SUFFIXES), under the same 0/1/2 contract: errors major, warnings minor; KG_<TOOL> or PATH; the instance's own config at its root, else instance/ci/{markdownlint.jsonc,gplintrc,bpmnlintrc,dmnlintrc}; a linter not installed leaves its kind unchecked naming it. kinds.toml lint.runs equals RUNNERS (test). instance/ci/preload-check.yml pins and installs the four on Node 24; a test holds its pins to harness.yml's. tools/check_preload_linters.py in harness.yml: a clean file of each kind exits 0 and a broken one exits 1 through instance/ci/preload-check.sh; PR #132 matrix green (tests, rdflib, stack). Not added: Vale (ships no rules of its own; a style is the organisation's). Finding: the vendored example's quote_process.bpmn fails bpmnlint:recommended (97 errors). Follow-ups: the GitLab include and composite action leave linter installs to the caller.
<!-- SECTION:FINAL_SUMMARY:END -->
