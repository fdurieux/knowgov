---
id: TASK-0234
title: >-
  Twenty KG_* settings documented as 1.0 contracts, each with what it does, its
  default and who sets it (decision-0027)
status: To Do
assignee:
  - '@claude'
created_date: '2026-11-08T21:18:00Z'
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
- [ ] #1 Each of the twenty is documented in instance/README.md, the worker limits in docs/security.md, with what it does, its default as the code reads it ("none" where there is none) and who sets it, in the adopter register
- [ ] #2 tests/test_adopter_docs.py holds each of the twenty documented in one of the two files and read in code, and none of the nineteen named there; it fails on main first
- [ ] #3 CHANGELOG has one line under Unreleased, Contract changes
<!-- AC:END -->
