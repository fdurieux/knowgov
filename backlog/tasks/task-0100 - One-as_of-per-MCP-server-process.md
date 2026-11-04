---
id: TASK-0100
title: One as_of per MCP server process
status: To Do
assignee: []
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-04T10:47:00Z'
labels:
  - mcp
  - clock
milestone: m-8
dependencies: []
priority: high
type: feature
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C2). harness/mcp_server.py reads KG_AS_OF (YYYY-MM-DD, record or today) once at start; gate_verdict and evidence_bundle use it unless a call names its own date, and both results and store_status carry the date read. The default is the maintainer's decision recorded in doc-0014 DECIDE 1 (recommended: today for both tools, as the CLI; a minor contract change under decision-0003). check_mcp_server.py and lighthouse_evidence.py already pass record and are unaffected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With no argument, one session's verdict and bundle carry the same as_of
- [ ] #2 tests/test_clock.py names the new read and holds it pinned
- [ ] #3 CHANGELOG names the changed default
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Decided 2026-11-04 by the maintainer (doc-0014 §11, #170): the default is today for both gate_verdict and evidence_bundle; evidence_bundle loses its record default, which stays an explicit choice. A contract change under decision-0003, so a minor version, named in the CHANGELOG. The split default is not kept as documentation.
<!-- SECTION:NOTES:END -->
