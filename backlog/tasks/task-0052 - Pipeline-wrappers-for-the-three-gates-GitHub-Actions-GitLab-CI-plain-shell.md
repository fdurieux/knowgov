---
id: TASK-0052
title: 'Pipeline wrappers for the three gates: GitHub Actions, GitLab CI, plain shell'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:41:00Z'
updated_date: '2026-11-04T00:42:00Z'
labels:
  - ci
milestone: m-7
dependencies: []
priority: low
type: feature
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 11: thin per-platform wrappers that map platform variables to the core commands' flags (gate_cli.py now; the pre-load check and knowgov-trace when they exist), selected by the client. Run on the example instance.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A GitHub Actions composite action, a GitLab CI include template and a shell snippet, each calling the core with the same flags
- [x] #2 Each is exercised on the example instance in CI where the platform allows (GitHub here; the others by a shell run of the same command line)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/knowgov-gate.sh: the platform-neutral core call, one script for the three gates: preload (delegates to preload-check.sh), gate (harness/gate_cli.py), trace-check and trace-register (harness/trace.py). Inputs are KG_* variables only (KG_COMMIT, KG_BASE, KG_LEDGER, KG_CODE_REPO, KG_FAIL_ON, KG_SCENARIO, KG_TASK, KG_STAGE, KG_SUBJECT); changed code paths from git diff --relative in the code map's root against KG_BASE. Exit is the core command's.
2. instance/ci/github/action.yml: a composite action mapping github.sha and the pull request's base to KG_COMMIT/KG_BASE and calling the script from the action's own checkout.
3. instance/ci/gitlab/knowgov.gitlab-ci.yml: an include template, hidden jobs per gate, mapping CI_COMMIT_SHA and CI_MERGE_REQUEST_DIFF_BASE_SHA.
4. Exercise: harness.yml uses ./instance/ci/github on the example instance (gate, trace register/check across S6's change) and runs the GitLab template's script lines in a shell with CI_* values set; a stdlib test holds the three to the same script and the same variable set.
5. demo.yml stack job: check_trace_walkthrough.py on Neo4j.
6. instance/README.md documents the wrappers.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
One core script, instance/ci/knowgov-gate.sh (preload, gate, trace-check, trace-register), reads KG_* only and computes changed code with git diff --relative in the code map's root (non-code paths dropped; deletions excluded for register). The GitHub composite action maps github.sha and the PR base, passes every input through env (no inline expression in the shell), and calls the script from its own checkout, so the pinned tag is what runs. The GitLab include maps CI_COMMIT_SHA, CI_MERGE_REQUEST_DIFF_BASE_SHA, CI_PROJECT_NAME and clones knowgov at KNOWGOV_REF. KG_REPORT (-o) added so a platform step can annotate or keep the report, and so CI reads the exit code of a step that is allowed to fail. Exercised: harness.yml uses ./instance/ci/github on the example instance as a git repo (preload 0, gate S6 0, trace-register 0, gate --stage 2 1, edit, trace-check 1 naming APP-0001, by the reports); tools/check_ci_wrappers.py runs the GitLab job's script lines by sh with CI_* values, same sequence. Also, as the coordinator asked, the stack job runs tools/check_trace_walkthrough.py on Neo4j. Verified locally on rdflib: the action's run line in the same sequence, check_ci_wrappers.py, tests 204/204. Not proven: a real GitLab runner.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Adds the pipeline wrappers: instance/ci/knowgov-gate.sh, one platform-neutral call for the pre-load check, the gate and knowgov-trace (KG_* variables to the core flags, changed code from git in the code map's root, exit 0/1/2 of the core command, KG_REPORT for the JSON); a GitHub composite action (instance/ci/github/action.yml) and a GitLab CI include (instance/ci/gitlab/knowgov.gitlab-ci.yml) that map their platform's commit and base to those variables. harness.yml runs the action on the example instance through S6 (the change fails trace-check naming APP-0001) and runs the GitLab job's script lines by a shell (tools/check_ci_wrappers.py); the stack job now also runs the trace walkthrough on Neo4j. Documented in instance/README.md ('Running the gates in your pipeline') and CLAUDE.md; tests/test_ci_wrappers.py holds both wrappers to the script and its variables. Risk: the GitLab template is not run on a GitLab runner; its remote include URL and image are as documented, untested here.
<!-- SECTION:FINAL_SUMMARY:END -->
