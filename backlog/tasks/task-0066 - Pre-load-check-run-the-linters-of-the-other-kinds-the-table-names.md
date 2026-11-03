---
id: TASK-0066
title: 'Pre-load check: run the linters of the other kinds the table names'
status: To Do
assignee: []
created_date: '2026-11-03T23:04:00Z'
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
- [ ] #1 At least the api-contracts kind runs a linter the table names (Spectral or vacuum), pinned, through the same exit contract; each further kind added is listed in the task notes
- [ ] #2 A kind whose linter is not installed in the environment is still reported unchecked naming the tool, never passed silently and never failed as cannot-run
- [ ] #3 The CI template (instance/ci/) installs the pinned linters it runs; harness.yml proves each added kind on the example instance with a clean file (0) and a planted broken one (1)
- [ ] #4 kinds.toml and the RUNNERS table name the same tool for every kind that runs (tests/test_instance.py or tests/test_preload.py holds it)
- [ ] #5 instance/README.md and docs/guide.md §5 list which kinds are now checked
<!-- AC:END -->
