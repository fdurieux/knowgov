---
id: TASK-0172
title: >-
  Pinned JSON schemas for the MCP tools' outputs, held by the suite (doc-0029
  P5, doc-0028 G9)
status: To Do
assignee: []
created_date: '2026-11-06T13:03:00Z'
labels:
  - mcp
  - contracts
dependencies: []
priority: medium
ordinal: 173000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0029 advice 1. The MCP reader's and knowgov-runs' tool outputs are contracts at 1.0 under decision-0016 point 3 (proposed), but only harness/schemas/ pins JSON shapes today (gate, trace, preload, subject-check, register-nodes, key-nodes, code-path, document-links, held-keys, derived-outputs, document-statements, proposal-impact); other tool outputs are described in prose only, and task-0168 noted run_options has none. Add a schema per tool output not yet pinned, check every tool's output against its schema in the suite through harness/schema_check.py (standard library), and name each schema in the tool's description. Additive: no output changes shape. If the key-check PR (task-0171, another session) changes run_options first, rebase onto it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every tool the MCP reader and knowgov-runs list (both transports) has a JSON schema for its output under harness/schemas/, or names the existing one it returns
- [ ] #2 A test calls each tool on the public subjects (rdflib, no network) and validates the output against its schema with harness/schema_check.py; a field added without the schema fails it
- [ ] #3 Each tool's description names its schema; no output changes shape; CHANGELOG line under Unreleased > Changes
<!-- AC:END -->
