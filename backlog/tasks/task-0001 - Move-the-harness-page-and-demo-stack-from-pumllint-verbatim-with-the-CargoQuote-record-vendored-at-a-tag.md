---
id: TASK-0001
title: >-
  Move the harness, page and demo stack from pumllint, verbatim, with the
  CargoQuote record vendored at a tag
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:58:00Z'
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
- [x] #1 Harness, demo app, Dockerfile, compose files, comparator, vendoring tool and tests live here and import nothing from a pumllint checkout
- [x] #2 The CargoQuote subject (kit, cargo_quote documents) and the record (results, pre-registration, SHA256SUMS) are vendored from pumllint at a named tag, or, until a pumllint tag carries the experiment, at a named commit the SOURCE note marks untagged; the note lists commit and sha256 per file, and a test holds every file to its digest
- [x] #3 The register copy is byte-identical to ieam-register at v0.1.1, written by tools/vendor_register.py, its SOURCE note the tool's output here, held by its test
- [x] #4 A deterministic re-run of S1 to S7 against a Neo4j 5.26 community container matches the record field by field through the comparator
- [x] #5 The image builds from this repository and docker compose up serves the page with replay, deterministic and arms modes as the README of the demo describes
- [x] #6 A CI workflow runs the tests and the comparator on every pull request
- [x] #7 CLAUDE.md states the house rules: record versus view, pull requests, the backlog as the queue, decisions through the backlog
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Vendor the subject from pumllint at commit fd8bef4 (no pumllint tag contains kg_experiment yet; v0.34.0 predates it) into subjects/cargo_quote/ keeping pumllint's relative layout (kg_experiment/kit, kg_experiment/results, kg_experiment/PREREGISTRATION.md, stack_experiment/cargo_quote, stack_experiment/smoke_test.py, tools/acceptance) so the oracle's own path logic and the record's SHA256SUMS paths stay valid; tools/vendor_subject.py generalised from vendor_register.py writes SOURCE.md with tag-or-commit and digests; a test holds every file to its digest.
2. Move harness/ and demo/ (app, model, register, tools, Dockerfile, compose files, README, GLOSSARY) verbatim; change only the path constants (kitio EXP/REPO/CARGO, measures REPO, run.py RESULTS and the harness rglob, views/server EXP and RESULTS, compare_deterministic RECORD, cascade DECK_TOOLS) to point at the subject root and the new tree; copy the deck layout tables as demo/model/cascade_layout.py with their origin in model/SOURCE.md.
3. Demo runs go to runs/ (gitignored, KG_DEMO_RUNS default); Dockerfile and compose paths follow; image renamed ghcr.io/fdurieux/knowgov.
4. Tests: run_tests.py runner, test_demo.py, test_register_view.py, test_vendor_register.py, test_vendor_subject.py with paths moved; pumllint-only assertions (docs, deck html) dropped or re-pointed.
5. CI: tests.yml (unit tests, no store) and demo.yml (compose stack, deterministic S1 through the app, comparator; publish on main), ported from pumllint's kg-demo.yml.
6. Local proof: Neo4j 5.26 community run directly in the session (no Docker daemon here), run.py --deterministic for S1 to S7, comparator green; CI proves the compose stack.
7. PR, merge on green; pumllint retirement PR is separate.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Moved verbatim: harness/ and demo/ from pumllint fd8bef4; path constants only (kitio, run, measures, views, server, compare_deterministic, cascade). Subject vendored by tools/vendor_subject.py at fd8bef4 (no pumllint tag carries kg_experiment yet; the note says untagged). Register re-vendored at v0.1.1 by the tool (its note starts here without pumllint's earlier-copies row). Layout tables copied as demo/model/cascade_layout.py, digest in model/SOURCE.md. One real pumllint import found inside a function (extract.py, the sequence mapper uses pumllint.parser): pinned pumllint==0.33.0 from PyPI in the Dockerfile. Local proof without Docker: Neo4j 5.26.0 community tarball on Java 21, venv with the pins, run.py --deterministic for S1 to S7, comparator 0 differing leaves over 7 scenarios; the page served locally passed every check of the CI job (menu, replay S6, register 27/28, impact APP-0002, footprint S2, refs, deterministic S1 through the app, projection 179 relationships at v0.1.1, comparator). 38/38 unit tests.

AC evidence. 1: the stack job builds the image from this repository alone; pumllint enters as the released package 0.33.0 from PyPI (the sequence mapper's parser), not a checkout. 2: no pumllint tag carries kg_experiment (v0.34.0 predates it), so the subject is pinned at fd8bef4 and SOURCE.md says untagged; AC reworded to say so; re-vendor at the next pumllint tag. 3: register copy diffed byte for byte against pumllint's; only the note differs, lacking pumllint's earlier-copies row, since this repository's first copy is v0.1.1; AC reworded; test_vendor_register holds the note to the tool's output. 4: locally against Neo4j 5.26.0 community (the server from the tarball, same edition the container runs), S1 to S7, 0 differing leaves; in CI the container, S1 through the page, comparator OK. 5: the stack job built the image, started both services and read menu, replay S6, register, impact, footprint, refs, a deterministic S1 and the projection; arms correctly reported disabled with no key. 6: tests.yml and demo.yml both ran on PR #2, green. 7: CLAUDE.md sections Record and views, Pull requests, Layout and checks, Boundaries.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The platform runs from this repository. harness/ and demo/ are pumllint's kg_experiment code at fd8bef4 with path constants changed and nothing else; subjects/cargo_quote/ is the CargoQuote subject and the proof-of-concept record vendored by tools/vendor_subject.py at that commit, in pumllint's relative layout, with a SOURCE note and a digest test; demo/register/ is ieam-register v0.1.1 by tools/vendor_register.py; the deck layout tables travel as demo/model/cascade_layout.py. Re-runs land in runs/. Verification: 38/38 unit tests; locally, Neo4j 5.26.0 community and the deterministic half for S1 to S7 with the comparator at 0 differing leaves; the page served locally passed every check of the CI job; on PR #2 the tests job and the stack job (image build, compose stack, S1 deterministic through the page, projection, comparator) are green. Risks and follow-ups: the subject pin is a commit until pumllint tags the experiment (one command re-vendors); pumllint 0.33.0 from PyPI reproduces the record although the harness was written against a later checkout, so a later pumllint release that changes the parser must be re-pinned with the comparator as the oracle; retiring pumllint's copy and its kg-demo workflow is a pumllint pull request still to open, recorded in its ROADMAP.
<!-- SECTION:FINAL_SUMMARY:END -->
