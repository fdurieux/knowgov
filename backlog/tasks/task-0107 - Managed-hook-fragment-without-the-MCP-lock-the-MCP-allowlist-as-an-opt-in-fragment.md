---
id: TASK-0107
title: >-
  Managed hook fragment without the MCP lock; the MCP allowlist as an opt-in
  fragment
status: To Do
assignee: []
created_date: '2026-11-04T11:45:00Z'
labels:
  - ci
  - security
milestone: m-8
dependencies:
  - TASK-0099
priority: low
type: task
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maintainer's decision 2026-11-04, option C of the coordinator's canvas: the enforcement that matters is the hook, made unremovable by allowManagedHooksOnly; the MCP allowlist (allowManagedMcpServersOnly + allowedMcpServers) is the organisation's own tool policy and, copied as is, replaces every other MCP server an organisation allows. instance/ci/claude/managed-settings.json keeps allowManagedHooksOnly and the hook; a separate managed-mcp-allowlist.json carries the MCP lock as an opt-in, with the README saying both lists replace lower sources' and must be merged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 managed-settings.json carries no allowManagedMcpServersOnly or allowedMcpServers; the opt-in fragment carries both
- [ ] #2 instance/README.md names the opt-in, what it replaces, and that the hook stays mandatory without it
- [ ] #3 A test holds both fragments' keys and the hook command equal to the repository snippet's
<!-- AC:END -->
