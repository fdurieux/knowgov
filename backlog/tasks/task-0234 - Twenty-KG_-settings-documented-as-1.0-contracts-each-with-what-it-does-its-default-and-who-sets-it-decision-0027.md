---
id: TASK-0234
title: >-
  Twenty KG_* settings documented as 1.0 contracts, each with what it does, its
  default and who sets it (decision-0027)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T21:18:00Z'
updated_date: '2026-11-08T21:31:00Z'
labels:
  - docs
  - contract
  - release
dependencies: []
priority: high
ordinal: 230000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0027 (accepted 2026-11-08, the maintainer: "settings as advised") makes twenty KG_* settings 1.0 contracts by documenting them, under decision-0016 point 3 (a KG_* setting documented in instance/README.md or docs/security.md is a contract; an undocumented one is not). task-0230 found them read in code and named by no adopter doc. The groups: the CI-template and hook inputs (KG_TASK, KG_STAGE, KG_NO_LOAD, KG_GATE, KG_CODE_REPO, KG_SUBJECT_IN, KG_HOME); the store (KG_NEO4J_URI, KG_NEO4J_USER); the worker limits, in docs/security.md (KG_WORKERS, KG_WORKER_CPUS, KG_WORKER_MEM, KG_WORKER_JOBS, KG_WORKER_JOB_SECONDS, KG_WORKER_WORK); cross-subject calls (KG_SUBJECT_CALL_TIMEOUT); the model endpoint (KG_ARMS_MODEL, KG_MODEL_API_KEY_VAR, KG_MODEL_API_KEY, KG_MODELS). Nineteen stay out (internals, demo knobs, arms experiment knobs) and must not appear in the two contract documents. Docs only: every default is read from the code, "none" where there is none, never invented.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each of the twenty is documented in instance/README.md, the worker limits in docs/security.md, with what it does, its default as the code reads it ("none" where there is none) and who sets it, in the adopter register
- [x] #2 tests/test_adopter_docs.py holds each of the twenty documented in one of the two files and read in code, and none of the nineteen named there; it fails on main first
- [x] #3 CHANGELOG has one line under Unreleased, Contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tests/test_adopter_docs.py: CONTRACT_SETTINGS (the twenty, each with its document) and NOT_CONTRACTS (the nineteen), from decision-0027. Each of the twenty is named in its document and read in code; none of the nineteen is in instance/README.md or docs/security.md. Run on main first.
2. instance/README.md: a section, "The settings an instance may rely on", before the contracts section. Four tables (CI and hook; store; another subject; model endpoint), each row with what it does, its default and who sets it.
3. docs/security.md: the worker's six limits as a list after the worker's evidence. A table there would shift the one test_security reads by position.
4. Every default read from the code, none invented. CHANGELOG under Unreleased, Contract changes. Suites.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
On main 44ef5c8 the new test failed on all twenty (none documented); the nineteen were already absent from both files.
Each default was read from the code:
- knowgov-gate.sh: KG_TASK codegen, KG_CODE_REPO code;
- action.yml: code-repo falls back to the repository name; subject to KG_SUBJECT_IN to KG_SUBJECT;
- knowgov.gitlab-ci.yml: KG_GATE gate, KG_CODE_REPO the project name;
- knowgov_hook.py: KG_HOME, else the hook's own checkout; settings.json /opt/knowgov;
- store_neo4j.py: bolt://localhost:7687 and neo4j; the image and compose set bolt://neo4j:7687;
- mcp_server.py: CHILD_TIMEOUT 300, answered with an error naming the subject;
- arms.py: KG_ARMS_MODEL, else the record model, else gpt-5.5; KG_MODEL_API_KEY_VAR OPENAI_API_KEY;
- compose: KG_MODEL_API_KEY passed to the app, empty by default; KG_WORKER_CPUS 2, KG_WORKER_MEM 4g;
- models.py: DEFAULT_TABLE demo/models.toml;
- execution.py: JOB_SECONDS 900; no KG_WORKER_JOBS means refused;
- worker.py: /jobs and /work;
- run.py: KG_WORKERS 5, the page 2.
KG_WORKERS bounds how many of an arm's runs are in flight, not the worker container, and the doc says so. KG_NEO4J_PASSWORD, already a contract through docs/security.md, is named beside KG_NEO4J_USER.
Suites:
- bare 3.13: 821/876, 55 skips;
- pins: 875/876, 1 skip.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0027 built: the twenty KG_* settings are documented as 1.0 contracts.
- instance/README.md gets a new section, "The settings an instance may rely on". Its fourteen rows cover the CI and hook inputs, the store, the cross-subject timeout and the model endpoint.
- docs/security.md gets the worker's six limits.
- Each entry says what the setting does, its default as the code reads it, and who sets it.
- tests/test_adopter_docs.py holds the twenty documented and read in code, and keeps the nineteen out of both contract documents. It failed on main first.
- One CHANGELOG line under Unreleased, Contract changes.
- Docs and a test only; both suites pass.
<!-- SECTION:FINAL_SUMMARY:END -->
