---
id: TASK-0116
title: Optional SARIF upload to GitHub code scanning in the instance CI templates
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T14:56:00Z'
updated_date: '2026-11-06T04:14:00Z'
labels:
  - ci
milestone: m-8
dependencies: []
priority: low
type: task
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0106; chosen by the maintainer 2026-11-04. harness/annotate.py already writes SARIF 2.1.0; the GitHub action could upload it to code scanning when the instance opts in.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 instance/ci/github/action.yml has an opt-in input that uploads the SARIF; off by default
- [ ] #2 harness.yml exercises it once; the README says what it needs (permissions, code scanning enabled)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/github/action.yml: inputs sarif (default false) and sarif-category; the run step adds sarif:$RUNNER_TEMP/knowgov-<gate>.sarif to KG_ANNOTATE, keeps the gate's exit, writes the file to an output; a second step, if always() and sarif and a file, github/codeql-action/upload-sarif pinned by commit (v4.39.1, 9b32540); output sarif-id. 2. harness.yml: security-events: write on the rdflib job only; the existing S1 as-of step (exit 1, 30 located results) with sarif on except a fork's pull request; the check step asserts sarif-id. 3. README: what an instance needs. 4. Tests: test_ci_wrappers (input, pin, condition, permission scope, README), test_pins covers the pin. 5. CHANGELOG Unreleased > Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the pin github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1 (2026-10-21, the commit its annotated tag names; v4.39.2 and v4.39.3 are under two weeks old). The run block, run locally: sarif true, the S1 as-of gate exits 1 and writes sarif=<file> to GITHUB_OUTPUT; sarif false writes nothing, the same exit. The SARIF has 30 results, every one located (annotate.py falls back to subject.toml). tests/test_ci_wrappers.py test_the_action_uploads_sarif_only_when_asked_pinned_and_after_any_exit; tests/test_pins.py holds the pin's form. The inline-inputs check now reads the run block itself, to the next step, since the upload step's with: names inputs. run_tests.py after merging main (task-0113): 536/552 stdlib, 551/552 pinned, 0 failed. AC2 waits on harness.yml's run on the PR: the upload's sarif-id asserted.

2026-11-06, the coordinator on #274: the first PR upload worked (code scanning's 'knowgov gate' check, github-advanced-security set up). The exercise is now same-repository pull requests only, never main or the nightly run: a default branch's upload would keep the example instance's lapsed-review findings, a fixture, as standing alerts. A PR's upload is analysed against its merge ref. README and test say so.
<!-- SECTION:NOTES:END -->
