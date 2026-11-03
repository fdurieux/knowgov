---
id: TASK-0063
title: >-
  Connector for the lighthouse incumbent: its export read into an instance as a
  dated mirror, verified on a real installation
status: To Do
assignee: []
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-03T23:08:00Z'
labels:
  - lighthouse
milestone: m-8
dependencies:
  - TASK-0062
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: high
type: feature
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0012 §3, E3 = 1: every row of the register's mapping/matrix.toml reads unverified, and no export route has met a target installation. The connector is the first route from an incumbent's record (an API, its MCP server, or a file export) into the instance layout the platform already reads, so the gate and the walk answer on the client's own design. The register's contracts bind it: exports are append-only under exports/<system>/<date>/ with MANIFEST.toml and RECONCILE.json, a vanished external id is a stale finding never a deletion, and a node file never copies a tool's attributes. The register's matrix row and its evidence are ieam-register's record, moved by a pull request there.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A dated export from the incumbent lands in the example instance with a manifest and a reconciliation report, and a second export lands beside it without overwriting the first
- [ ] #2 The same export run against the pilot's installation produces a reconciliation report with no error, kept in the private record
- [ ] #3 A vanished external id between two exports is reported stale and deletes nothing
- [ ] #4 The connector names its system only through instance configuration; nothing under harness/ or demo/app names the vendor
- [ ] #5 An ieam-register pull request moves the incumbent's mapping row off unverified, with the evidence of the run
<!-- AC:END -->
