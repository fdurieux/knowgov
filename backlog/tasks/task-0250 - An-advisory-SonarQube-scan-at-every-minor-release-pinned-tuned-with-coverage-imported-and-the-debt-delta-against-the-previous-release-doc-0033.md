---
id: TASK-0250
title: >-
  An advisory SonarQube scan at every minor release: pinned, tuned, with
  coverage imported and the debt delta against the previous release (doc-0033)
status: To Do
assignee: []
created_date: '2026-11-09T07:10:00Z'
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
- [ ] #1 quality.yml runs on a v* tag, on workflow_dispatch with a ref input, and on a pull request touching it or its tools; Community Build and the scanner are pinned by exact version, the profile is exported in the repository, no secret is needed, and the PR that adds it shows one complete run
- [ ] #2 Coverage from tools/coverage_stdlib.py is imported through a stdlib converter, and the run's measures show it with its declared denominator
- [ ] #3 The run uploads issues and measures as an artefact and writes a debt delta against the previous release's artefact and the in-repository triage baseline to the job summary; the workflow fails only when the scan cannot run
- [ ] #4 docs/ (maintainer register) or CLAUDE.md states the cadence, how a finding is accepted with a reason, and that the scan is advisory, never a gate
<!-- AC:END -->
