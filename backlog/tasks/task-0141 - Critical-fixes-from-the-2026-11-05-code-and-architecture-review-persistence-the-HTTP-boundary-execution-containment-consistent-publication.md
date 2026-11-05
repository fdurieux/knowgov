---
id: TASK-0141
title: >-
  Critical fixes from the 2026-11-05 code and architecture review: persistence,
  the HTTP boundary, execution containment, consistent publication
status: To Do
assignee: []
created_date: '2026-11-05T20:33:00Z'
labels:
  - security
dependencies: []
priority: high
type: bug
ordinal: 141000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
An external review of knowgov at 98fc796 (2026-11-05) found defects that lose or misreport evidence without an attacker, and gaps at the trust boundaries: a file-backed store reader can publish a stale snapshot over a newer one on close; the page and the MCP server do not check the request authority and the browser origin independently; request bodies, connections and admitted work are unbounded; code an arm generates runs with the orchestrator's environment and filesystem; and a reader can see a store part-way through a rebuild. Its implementation plan (work packages E0, S1, H1, H2, X1, S2 and V1, with regression ids ENV-, ST-, HTTP-, LIMIT-, EXEC- and SNAP-) is the acceptance contract. It travels in the implementing session's brief and is not committed while the fixes are open, the repository being public. Order set by the maintainer: E0, S1, H1, H2, X1, S2, with V1 throughout, each package validated before the next. Out of scope: framework migration, evidence levels or approval rules, the record, bulk dependency upgrades.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every subtask's regression ids are implemented, executed and linked to their evidence; a package is complete on its safety property and acceptance tests, never on an overall green suite
- [ ] #2 A required check that is skipped or blocked by its environment is reported apart from the passes, and a required security job fails when its backend is absent (V1)
- [ ] #3 The record, vendored bytes, deterministic results, schema versions and exit codes are unchanged, or the change is a recorded contract change with its CHANGELOG line
- [ ] #4 The final summary carries the work-package matrix: regression ids and results, integration evidence, compatibility changes, remaining blockers
<!-- AC:END -->
