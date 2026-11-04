---
id: TASK-0107
title: >-
  Managed hook fragment without the MCP lock; the MCP allowlist as an opt-in
  fragment
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T11:45:00Z'
updated_date: '2026-11-04T12:36:00Z'
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
- [x] #1 managed-settings.json carries no allowManagedMcpServersOnly or allowedMcpServers; the opt-in fragment carries both
- [x] #2 instance/README.md names the opt-in, what it replaces, and that the hook stays mandatory without it
- [x] #3 A test holds both fragments' keys and the hook command equal to the repository snippet's
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Drop the MCP keys from managed-settings.json; add managed-mcp-allowlist.json with them.
2. README: name the opt-in, the list replacement, the hook mandatory without it.
3. Test: both fragments' keys exact; managed hook's command and gate args equal to settings.json's.
4. CHANGELOG line under Unreleased > Also since 0.3.0.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Split done; both suites 324/324. Managed hook args are the repository snippet's plus --knowgov KG_HOME (managed settings carry no repository env); the test holds that exactly.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
managed-settings.json now carries allowManagedHooksOnly and the hook only; managed-mcp-allowlist.json carries allowManagedMcpServersOnly and allowedMcpServers as an opt-in. instance/README.md lists the new file, says both lists replace lower settings sources' and must be merged, and that the hook stays mandatory without the opt-in. tests/test_claude_hook.py holds both fragments' exact keys and the managed hook's command equal to settings.json's (args = the snippet's + --knowgov KG_HOME). CHANGELOG under Unreleased > Also since 0.3.0. python tests/run_tests.py 324/324, J-F subject 324/324.
<!-- SECTION:FINAL_SUMMARY:END -->
