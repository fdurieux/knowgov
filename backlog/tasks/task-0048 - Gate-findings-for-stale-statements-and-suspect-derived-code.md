---
id: TASK-0048
title: Gate findings for stale statements and suspect derived code
status: To Do
assignee: []
created_date: '2026-11-03T22:40:00Z'
labels:
  - gate
milestone: m-7
dependencies: []
references:
  - backlog/docs/doc-0011
priority: high
type: bug
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 3, measured: harness/gate_cli.py reports stale and suspect_derived as counts only, so they never move the exit code; after S6's re-verification the gate reads PROCEED while derived:S1:G:run1 is still suspect. Make both finding classes on the contract's ladder and raise the report schema version.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Stale statements on required keys and suspect derived outputs appear as findings with a severity, and count toward --fail-on
- [ ] #2 harness/schemas/gate-report.schema.json moves to version 2, with the change documented; tests validate every record scenario against it
- [ ] #3 A gate run after S6's stage 2 no longer exits 0 while a derived output it names is suspect, shown in harness.yml
<!-- AC:END -->
