---
id: TASK-0106
title: >-
  Pre-load wrapper: write the pre-load report so KG_REPORT and KG_ANNOTATE cover
  the pre-load gate
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T10:53:00Z'
updated_date: '2026-11-04T10:56:00Z'
labels:
  - ci
  - preload
dependencies:
  - TASK-0083
priority: low
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0083 wired harness/annotate.py into knowgov-gate.sh for gate and trace-*; the preload gate execs instance/ci/preload-check.sh, which writes no report, so KG_REPORT and KG_ANNOTATE do nothing there and pre-load findings reach no platform's annotation surface. annotate.py already reads pre-load reports.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 preload-check.sh writes preload_check.py's JSON report to KG_REPORT when set; knowgov-gate.sh's preload gate annotates it under KG_ANNOTATE with the exit code unchanged
- [ ] #2 A finding the baseline holds is never an error annotation
- [ ] #3 Proven on a broken document: the GitLab job's script lines leave a code-quality issue on its file and line, and the action's preload step on GitHub
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. preload-check.sh: KG_REPORT set -> preload_check.py -o it (relative to the caller's directory).
2. knowgov-gate.sh: the preload gate runs through the same report and annotate path as gate and trace-*; exit code the check's.
3. annotate.py: a finding the baseline holds (held) is at most a warning.
4. Proof: check_ci_wrappers.py runs the GitLab job's preload on a broken .puml (code-quality issue on its file and line); harness.yml runs the action's preload on it with a report; test_annotate for held.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
preload-check.sh passes KG_REPORT to preload_check.py -o; knowgov-gate.sh's preload gate runs through the same report and annotate path as gate and trace-* (finish(): annotate, then the check's exit code). annotate.py: a held finding is at most a warning (title says held by the baseline). The layout check's problems stay in the log: they are not in the report. Local: run_tests 298/298 plain and with KG_SUBJECT=subjects/jef_data_load; check_ci_wrappers.py on rdflib: the GitLab job's preload on a committed broken.puml exits 1 and the code-quality report puts SEQ001 (critical) on instance/artefacts/plantuml-models/broken.puml line 3. harness.yml: the action's preload on the same diagram, report and ::error on its line.
<!-- SECTION:NOTES:END -->
