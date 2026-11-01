---
id: TASK-0001
title: >-
  Move the harness, page and demo stack from pumllint, verbatim, with the
  CargoQuote record vendored at a tag
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - platform
  - move
milestone: m-0
dependencies: []
references:
  - https://github.com/fdurieux/pumllint/tree/main/kg_experiment
  - >-
    https://github.com/fdurieux/pumllint/blob/main/docs/neo4j-governed-knowledge-evaluation.md
priority: high
type: task
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The demo lives in pumllint under kg_experiment/ (harness, demo app, Dockerfile, compose files, comparator, three test modules, the vendoring tool) and the subject it governs is spread over kg_experiment/kit/, stack_experiment/cargo_quote/ and kg_experiment/results/. Decision decision-0001 moves the platform here; the record stays in pumllint, where it was made. The demo already vendors ieam-register at a tag with a SOURCE note written by tools/vendor_register.py and held by a test; the CargoQuote subject and its record take the same route from pumllint, so replay works offline from the first start and the deterministic comparator keeps its oracle. No behaviour changes in this task: the move is verbatim so the comparator proves nothing was lost. Retiring pumllint's copy and its kg-demo workflow is a pumllint pull request, recorded in pumllint's ROADMAP, not a task here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Harness, demo app, Dockerfile, compose files, comparator, vendoring tool and tests live here and import nothing from a pumllint checkout
- [ ] #2 The CargoQuote subject (kit, cargo_quote documents) and the record (results, pre-registration, SHA256SUMS) are vendored from pumllint at a named tag with a SOURCE note listing tag, commit and sha256 per file, and a test holds every file to its digest
- [ ] #3 The register copy keeps its SOURCE note and test unchanged
- [ ] #4 A deterministic re-run of S1 to S7 against a Neo4j 5.26 community container matches the record field by field through the comparator
- [ ] #5 The image builds from this repository and docker compose up serves the page with replay, deterministic and arms modes as the README of the demo describes
- [ ] #6 A CI workflow runs the tests and the comparator on every pull request
- [ ] #7 CLAUDE.md states the house rules: record versus view, pull requests, the backlog as the queue, decisions through the backlog
<!-- AC:END -->
