---
id: TASK-0095
title: The lighthouse evidence script reads evidence_bundle over MCP
status: To Do
assignee: []
created_date: '2026-11-04T07:29:00Z'
labels:
  - lighthouse
  - mcp
milestone: m-8
dependencies:
  - TASK-0080
  - TASK-0069
priority: low
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by the task-0080 session: tools/lighthouse_evidence.py (task-0069) rebuilds the bundle itself; reading it through the MCP server's evidence_bundle (task-0080) proves criterion 4 (agent grounding) by the path an agent uses.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 lighthouse_evidence.py takes the bundle from evidence_bundle and the run's evidence is unchanged
- [ ] #2 harness.yml's lighthouse step still passes on the PR subset and the full set
<!-- AC:END -->
