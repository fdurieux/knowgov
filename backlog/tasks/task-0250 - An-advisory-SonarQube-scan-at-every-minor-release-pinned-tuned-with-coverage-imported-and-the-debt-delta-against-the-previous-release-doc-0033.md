---
id: TASK-0250
title: >-
  An advisory SonarQube scan at every minor release: pinned, tuned, with
  coverage imported and the debt delta against the previous release (doc-0033)
status: Done
assignee: []
created_date: '2026-11-09T07:10:00Z'
updated_date: '2026-11-09T09:00:00Z'
labels:
  - quality
  - ci
  - tooling
dependencies: []
priority: medium
ordinal: 244000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-09: "yes, mint and dispatch both", on the coordinator's advice (doc-0033, Answered): not a gate, and per minor release rather than per major, majors being years apart. A separate .github/workflows/quality.yml, on the release tag v* (as release.yml) and on workflow_dispatch with an input ref, so a past tag such as v0.9.0 can be scanned once the workflow is on main, and on a pull request that touches the workflow or its tools, so the PR that adds it proves it. It starts SonarQube Community Build in a service container and runs the scanner, both pinned to exact versions, with an ephemeral local token and no repository secret. The quality profile is pinned in the repository (exported), tuned to drop the rules that fight the stdlib runner (split composite assertions, pytest monkeypatch) and keep bugs, vulnerabilities, hotspots, cognitive complexity and duplication. The exclusions are the review's: vendored register, model and subject bytes, recorded outputs, fixtures, backlog and docs. Coverage comes from tools/coverage_stdlib.py (outcomes/coverage.json) through a stdlib converter to Sonar's generic coverage format, with no new dependency. It writes the issues and measures as a run artefact, and a debt delta (new and gone issues by type and severity, complexity hotspots, duplication, coverage) against the previous release's artefact and against an in-repository triage baseline, in the job summary. Accepted findings carry their reason in code (# NOSONAR: <why>, beside the existing noqa) or in the baseline file. It never fails a release: a red run means the scan could not run. Not a cut condition; the first scan is the 0.9.0 baseline.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 quality.yml runs on a v* tag, on workflow_dispatch with a ref input, and on a pull request touching it or its tools; Community Build and the scanner are pinned by exact version, the profile is exported in the repository, no secret is needed, and the PR that adds it shows one complete run
- [x] #2 Coverage from tools/coverage_stdlib.py is imported through a stdlib converter, and the run's measures show it with its declared denominator
- [x] #3 The run uploads issues and measures as an artefact and writes a debt delta against the previous release's artefact and the in-repository triage baseline to the job summary; the workflow fails only when the scan cannot run
- [x] #4 docs/ (maintainer register) or CLAUDE.md states the cadence, how a finding is accepted with a reason, and that the scan is advisory, never a gate
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on PR #401 (branch claude/task-0250-quality-scan).
- Pins: SonarQube Community Build 26.11.0.134175-community by tag and digest (sha256:1ce19747...), published on 127.0.0.1; SonarScanner CLI 8.3.1.16491 from binaries.sonarsource.com, checked against its published SHA-256 (0f304e4c...). On the fresh server the admin password is changed to a random value and a USER_TOKEN minted, both masked; no repository secret.
- Profile: tools/quality/knowgov-python.xml, Sonar way comprehensive (405 rules) without python:S9073 (split composite assertions, 1,496 findings at main 6d27961) and python:S8997 (monkeypatch, 162). It restores with 405 rules succeeding and 0 failing.
- Old refs: the workflow's own commit is checked out and moved outside the scanned checkout. The first PR run measured with a second tree in the workspace, and tests/test_outcomes.py's every-file check failed under the measurer. tools/coverage_stdlib.py gains --root and --lines (additive; the default output is unchanged).
- PR #401's own runs: run 42580782792 at 9232d22 completed; the suite had 1 failure under the measurer (the second-tree layout above), which was fixed. Run 42583974140 at 10c3ded completed clean:
  - suite 856/912, 0 failed;
  - coverage statements 14192/24138 (58.8%), branches 9061/21292 (42.6%), imported for 114 files; the 115th, tools/fixtures/claim_probe/code/probe.py, is excluded from the analysis as a fixture;
  - profile 405/0; scanner EXECUTION SUCCESS;
  - export 516 issues, 0 hotspots, 16 measures;
  - no kept scan of v0.8.0, so the delta is the baseline;
  - artefact quality-pr-401 kept.
  The measures' line and branch coverage equal the measurer's percentages, on the same denominator as tests.yml (CPython 3.13, no extra packages).
- Baseline: tools/quality/baseline.json, 12 entries accepting 21 findings, each with a reason and a count cap, following doc-0033's triage. Findings tasked elsewhere stay open: docker:S6471 (task-0248), python:S1764 and javascript:S3923 (task-0246), python:S8786 (task-0249), python:S3776 (task-0251).
- Divergence from the brief (accepted by the coordinator, 2026-11-09): the brief's '# NOSONAR: <why>' suppresses nothing in SonarQube's Python analyser and is itself flagged (python:S7632); tried on a local 26.11 server. '# NOSONAR(<rule>) <why>' suppresses that rule on that line without a flag, so docs/quality-scan.md documents that form.
- A 90-day retention limit: a scan's artefact is kept 90 days, so a previous release older than that has none. docs/quality-scan.md says to dispatch the workflow with that tag first.
- Unrelated to this task: #401's first stack run at 10c3ded failed SNAP-04 in tools/check_snapshots.py on Neo4j, 'every one of 13 reads during the race was a complete generation; partial: [{held: null, nodes: 564, ...}]'. Re-run once, it passed. A race that shows under runner load, reported to the coordinator.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An advisory SonarQube scan for every minor release: .github/workflows/quality.yml runs on v* tags, on workflow_dispatch with a ref, and on its own PRs. Community Build and the scanner are pinned, and the token is minted per run. tools/quality/ holds the exported Python profile (without S9073 and S8997), the analysis settings and exclusions, coverage_xml.py (coverage_stdlib.py --lines to generic coverage, stdlib) and report.py (export, and the debt delta against the previous release's artefact and baseline.json). docs/quality-scan.md gives the cadence, the pins, how a finding is accepted (# NOSONAR(<rule>) <why>, or a baseline entry) and that the scan is advisory, never a gate; it is red only when the scan cannot run. PR #401's own run at 10c3ded completed clean: suite 0 failed, coverage 58.8%/42.6% imported, 516 issues exported, artefact kept. tests/test_quality_scan.py holds the triggers, pins, no secret, the advisory steps, the profile, exclusions, the converter, the baseline cap and the delta. No change to tests.yml, harness.yml or demo.yml.
<!-- SECTION:FINAL_SUMMARY:END -->
