---
id: TASK-0064
title: >-
  Record each document's pre-load verdict on its Version in the store and in the
  gate's bundle
status: To Do
assignee: []
created_date: '2026-11-03T23:04:00Z'
labels:
  - instance
  - gate
  - store
milestone: m-6
dependencies:
  - TASK-0045
references:
  - backlog/docs/doc-0008
priority: low
type: feature
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The pre-load check (task-0045) runs on the pull request and its result stays in CI. Once merged, the load reads the document with no memory of whether its form was checked, by which tool, or whether it was left unchecked. A document loaded without a passing check is invisible in the store, in the gate's bundle and on the page. doc-0008 §5 proposed recording "each document's linter verdict (tool, version, digest of the file it judged) on its Version node, so a document loaded without a passing check is visible in the store and in the gate's bundle". The load does not re-run linters: the merge is the check; it only reads the verdict a CI run left.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A load given a preload report (a path or an instance-relative default) records on each document version the tool, its version, the state (clean, findings, unchecked) and the digest of the file judged, through the store port in both adapters
- [ ] #2 A version whose bytes do not match the digest judged, or that no report covers, is recorded as unchecked, never as clean
- [ ] #3 The gate's bundle and gate_cli.py's JSON list the documents behind the task's keys whose form was unchecked or had findings, as info-level findings that do not change the exit code unless a threshold asks
- [ ] #4 The page shows the verdict per document in the ingest stage panel
- [ ] #5 The comparator still matches the record for every scenario when no report is given (the field is absent, not empty), and tests cover both adapters
<!-- AC:END -->
