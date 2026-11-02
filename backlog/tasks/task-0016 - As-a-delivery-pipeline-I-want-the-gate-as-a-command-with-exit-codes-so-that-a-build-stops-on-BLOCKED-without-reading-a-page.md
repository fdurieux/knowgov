---
id: TASK-0016
title: >-
  As a delivery pipeline, I want the gate as a command with exit codes, so that
  a build stops on BLOCKED without reading a page
status: Done
assignee: []
created_date: '2026-11-01T14:30:00Z'
updated_date: '2026-11-02T23:11:00Z'
labels:
  - story
milestone: m-3
dependencies:
  - TASK-0007
priority: low
type: story
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Story for milestone m-3. The site's gate contract: exit codes, threshold, baseline, JSON under a schema, evidence tags.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 task-0007 is Done; the command exits 0, 1 or 2 as the contract says
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
task-0007 is Done (#68): harness/gate_cli.py exits 0, 1 or 2 as the contract says, on rdflib and on Neo4j in CI.
<!-- SECTION:FINAL_SUMMARY:END -->
