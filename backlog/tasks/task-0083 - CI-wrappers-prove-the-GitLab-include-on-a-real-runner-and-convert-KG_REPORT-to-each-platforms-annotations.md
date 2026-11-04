---
id: TASK-0083
title: >-
  CI wrappers: prove the GitLab include on a real runner, and convert KG_REPORT
  to each platform's annotations
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T11:45:00Z'
labels:
  - ci
milestone: m-7
dependencies:
  - TASK-0052
priority: low
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0052's GitLab template is checked by running its script lines in sh, not on a GitLab runner; the gate report stays JSON where platforms show annotations (GitHub checks, GitLab code quality, SARIF).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The GitLab include runs green on a GitLab runner, evidence noted
- [x] #2 A converter turns KG_REPORT into GitHub annotations and GitLab code-quality JSON, tested on S6
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/annotate.py, standard library: a gate, trace or pre-load report to GitHub workflow commands (::error/::warning/::notice, at or above the report's threshold an error), a GitHub step-summary table, GitLab code-quality JSON (severity ladder maps one to one; fingerprint from tool, kind, key, ref, path) and SARIF 2.1.0. Location: a trace finding's path under the instance's code root, a pre-load finding's file and line, else the subject's subject.toml; paths relative to the workspace.
2. knowgov-gate.sh: KG_ANNOTATE=format[:file],...; runs the core command, converts its report (a temporary one when KG_REPORT is unset), exits the command's code. Action: input annotate (default true): github to the log, summary to GITHUB_STEP_SUMMARY. GitLab include: KG_ANNOTATE=gitlab:gl-code-quality-report.json, artifacts:reports:codequality.
3. tests/test_annotate.py on schema-valid reports; tools/check_ci_wrappers.py and harness.yml on S6 --stage 2 (suspect, stale): the code-quality file and the action's annotations.
4. GitLab runner: try to reach gitlab.com from this session; if not, say so, AC #1 unchecked, DECIDE.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/annotate.py (stdlib): gate, trace and pre-load reports to GitHub workflow commands, a job-summary table, GitLab code quality and SARIF 2.1.0. Wired through knowgov-gate.sh's KG_ANNOTATE (exit code untouched; a run that exits 2 annotates nothing, never an earlier report): the action annotates by default (input annotate), the GitLab include writes gl-code-quality-report.json under artifacts:reports:codequality. Proven on S6 --stage 2: tools/check_ci_wrappers.py (the include's script lines; code-quality issues for suspect_derived blocker, stale major and info, the suspect build on reference_impl.py), harness.yml's new step on the action's real reports, tests/test_annotate.py on schema-valid samples. Locally: run_tests 231/231 plain and with KG_SUBJECT=subjects/jef_data_load; check_ci_wrappers on rdflib green.
AC #1 not met: this hosted session holds no GitLab account, project or runner token (gitlab.com answers 401 unauthenticated), so the include has not run on a GitLab runner. Not faked; left unchecked for the maintainer to run once on gitlab.com.

Closed 2026-11-04 on the maintainer's decision (coordinator's canvas, option C recorded as B): AC #1 is not met and is carried by task-0108, which depends on the lighthouse choice (task-0062). The shell proof stands: tools/check_ci_wrappers.py runs the include's script lines, and since #172 (task-0106) proves the code-quality report on a broken diagram; CHANGELOG 0.3.0 lists it as a known limit.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AC #2 delivered: harness/annotate.py converts gate, trace and pre-load reports to GitHub annotations, a job summary, GitLab code quality and SARIF, wired through KG_ANNOTATE (pre-load since task-0106). AC #1 (a real GitLab runner) not met from a hosted session; carried by task-0108 at the pilot. Done with that limit recorded.
<!-- SECTION:FINAL_SUMMARY:END -->
