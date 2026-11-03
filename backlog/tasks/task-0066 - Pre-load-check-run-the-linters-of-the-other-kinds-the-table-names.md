---
id: TASK-0066
title: 'Pre-load check: run the linters of the other kinds the table names'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:04:00Z'
updated_date: '2026-11-03T23:50:00Z'
labels:
  - instance
  - gate
milestone: m-6
dependencies:
  - TASK-0045
references:
  - backlog/docs/doc-0008
priority: medium
type: feature
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tools/preload_check.py (task-0045) runs one linter, pumllint for plantuml-models (RUNNERS in the tool); every other kind is reported "unchecked", naming the tool instance/kinds.toml gives. Several of those kinds have a mapper and a gate-capable tool, so a malformed file reaches the mapper unchecked: api-contracts (Spectral, vacuum, Redocly), specification-prose (Vale, markdownlint), acceptance-scenarios (gplint), decision-tables (dmnlint, for .dmn only). doc-0008 §5 counts five kinds with a working tool and a mapper, where the check is worth most. The linters are not Python and not in the image, so each needs an install route the instance CI template can carry, and a pin.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 At least the api-contracts kind runs a linter the table names (Spectral or vacuum), pinned, through the same exit contract; each further kind added is listed in the task notes
- [x] #2 A kind whose linter is not installed in the environment is still reported unchecked naming the tool, never passed silently and never failed as cannot-run
- [x] #3 The CI template (instance/ci/) installs the pinned linters it runs; harness.yml proves each added kind on the example instance with a clean file (0) and a planted broken one (1)
- [x] #4 kinds.toml and the RUNNERS table name the same tool for every kind that runs (tests/test_instance.py or tests/test_preload.py holds it)
- [x] #5 instance/README.md and docs/guide.md §5 list which kinds are now checked
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. RUNNERS gains api-contracts -> Spectral (run_spectral): @stoplight/spectral-cli 6.17.0, KG_SPECTRAL or spectral on PATH, the instance's .spectral.yaml at its root else instance/ci/spectral.yaml (spectral:oas + spectral:asyncapi); severities error->major, warn->minor, info/hint->info; rc from the mapped findings at the threshold.
2. A runner whose tool is not installed leaves its files unchecked naming it (both runners, pumllint included), exit unaffected; an installed linter that fails stays cannot-run (2).
3. kinds.toml lint.runs = the tool RUNNERS runs (pumllint, Spectral), one of the tools lint.tool names; tests/test_preload.py holds them equal and the template's pins equal to harness.yml's.
4. instance/ci/preload-check.yml installs Spectral pinned; harness.yml installs it after the task-0045 step (which still shows api-contracts unchecked without it) and proves clean 0, a planted broken $ref 1, through the template's script and --since.
5. instance/README.md, docs/guide.md §5 and Limits, CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Kinds added: api-contracts (Spectral 6.17.0). Not added: specification-prose (Vale needs a styles package per organisation; markdownlint checks Markdown form only), acceptance-scenarios (gplint), bpmn-process-models (bpmnlint), decision-tables (dmnlint, .dmn only): each a further runner with its own pin. Spectral over vacuum: vacuum installs a Go binary fetched from GitHub releases at npm install time; Spectral is plain npm, and its exit is 0/1/2. Change to task-0045's contract, as AC #2 asks: a linter not installed is now 'unchecked' (exit 0), not 'cannot run' (2), for pumllint too; doc-0008 §5 had listed 'a linter missing' under 2. Measured: the example's openapi.yaml has 4 Spectral warnings and no error (clean at major); a dangling $ref is an invalid-ref error (major, exit 1). Verified: tests 160/160 (also a bare venv); harness.yml's new step run locally with Spectral 6.17.0 from npm (KG_SPECTRAL in place of npm -g).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
API contracts are now checked before the load: tools/preload_check.py runs Spectral 6.17.0 (pinned in the CI template and harness.yml) on artefacts/api-contracts/, with the instance's .spectral.yaml or the shipped spectral:oas + spectral:asyncapi ruleset; Spectral errors are major findings, warnings minor, under the same 0/1/2 contract. A linter that is not installed now leaves its kind unchecked naming the tool (exit unaffected), for pumllint too; an installed linter that fails stays cannot-run. kinds.toml lint.runs names the tool RUNNERS runs, held equal by a test, as are the template's pins and harness.yml's. harness.yml proves a clean contract 0 and a broken $ref 1 through the template's script. README, guide §5 and Limits, CLAUDE.md list the checked kinds. Further kinds (Vale/markdownlint, gplint, bpmnlint, dmnlint) are recorded in the notes, not built.
<!-- SECTION:FINAL_SUMMARY:END -->
