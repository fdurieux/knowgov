---
id: TASK-0273
title: >-
  One command runs the whole suite in the record's image, with the pins
  installed and nothing skipped for want of a library
status: To Do
assignee: []
created_date: '2026-11-09T09:50:00Z'
labels: []
dependencies: []
references:
  - demo/Dockerfile
  - demo/Dockerfile.dockerignore
  - .github/workflows/harness.yml
  - tests/run_tests.py
  - tests/_skip.py
priority: low
ordinal: 251000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A standard-library run of tests/run_tests.py skips 50 tests for want of the record's pins: 46 for rdflib, one each for pyshacl, pumllint and openai, and one needing KG_HOOK_LIVE=1 (seen on task-0251's merged tree: 886 of 936 passed, 50 skipped). Today a contributor gets them only by installing the pins by hand in a venv, or from CI's rdflib job (harness.yml), which installs them on the runner and sets KG_TEST_REQUIRE=rdflib,node,openai. The record's own image (demo/Dockerfile: CPython 3.12-slim with every pin) is the natural place, but demo/Dockerfile.dockerignore keeps tests/ and backlog/ out of it, and the image has no Node, which KG_TEST_REQUIRE names. Context: task-0248 plans to change the image's user; the worker-isolation tests count processes, so the suite runs alone.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One documented command runs tests/run_tests.py on CPython 3.12 with the record's pins as demo/Dockerfile names them, without installing anything on the host
- [ ] #2 The run sets KG_TEST_REQUIRE=rdflib,node,openai and KG_HOOK_LIVE=1 as harness.yml's rdflib job does, so a skip for a missing pin fails it
- [ ] #3 The app image shipped to ghcr.io still carries no tests/ or backlog/, and its contents and pins are unchanged (a test holds it)
- [ ] #4 The pins are named once: the test run reads them from the same place demo/Dockerfile and harness.yml do, or a test holds the three equal (tests/test_demo.py, tests/test_pins.py)
- [ ] #5 CONTRIBUTING or the README names the command beside the standard-library one
<!-- AC:END -->
