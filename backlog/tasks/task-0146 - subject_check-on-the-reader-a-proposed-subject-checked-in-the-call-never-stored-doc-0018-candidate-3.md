---
id: TASK-0146
title: >-
  subject_check on the reader: a proposed subject checked in the call, never
  stored (doc-0018 candidate 3)
status: To Do
assignee: []
created_date: '2026-11-05T21:24:00Z'
updated_date: '2026-11-05T21:25:00Z'
labels: []
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0018 -
    A-subject-wizard-over-MCP-creating-a-subject-and-adding-its-artefacts-with-an-assistant.-Pipeline-sense-and-nonsense-fit-gap-opportunity-canvas-SWOT.md
priority: medium
type: feature
ordinal: 152000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tools/check_subject.py (task-0135) checks a subject root before anything is loaded, from the command line. In Claude Desktop, or any client without a shell, an assistant scaffolding a subject cannot run it. The same check as a read-only tool lets the wizard (task-0148) check after every write without a store and without writing anything. Approved by the maintainer on 2026-11-05 ("go on candidates 3, 4 and 5").
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A read-only MCP tool takes a proposed subject.toml, register_map.toml, scenarios.toml and the documents' text in the call, and returns check_subject.py's report (schema subject-check), checked against the served register and the instance's kinds by check_subject's own functions
- [ ] #2 Nothing is stored or written outside a temporary directory removed after the call; the mappers' yield runs in a child process as check_subject does; the call's size is bounded and an oversized call is refused
- [ ] #3 On tools/fixtures/subject_probe the tool's report equals check_subject.py's on the same files; check_mcp_server.py exercises it
- [ ] #4 Served by the read-only knowgov server over stdio and Streamable HTTP and admitted by the shipped allowlist by name; the server's instructions, instance/README.md's tool table, CLAUDE.md and CHANGELOG Unreleased carry it
<!-- AC:END -->
