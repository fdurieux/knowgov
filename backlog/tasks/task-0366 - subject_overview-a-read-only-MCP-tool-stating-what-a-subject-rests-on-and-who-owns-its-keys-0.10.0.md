---
id: TASK-0366
title: >-
  subject_overview: a read-only MCP tool stating what a subject rests on and who
  owns its keys (0.10.0)
status: In Progress
assignee: []
created_date: '2026-11-16T20:28:00Z'
updated_date: '2026-11-27T23:23:38Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
priority: medium
ordinal: 356000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-16: "yes, add them as 0.10.0 tasks", after a Claude Desktop session over MCP gave a private subject's counts and links loosely: it summarised a report too large to read whole, carried the wrong count forward, and inferred a subject-to-application link no tool states. The link from a subject to the register nodes its keys rest on is in its register_map.toml, but no tool states it, so an assistant guesses it from names. Ships in 0.10.0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 subject_overview(subject) returns, from files: the register nodes the subject's keys rest on, by kind and id with names and owners; the owner units with their key counts; the scenario the store holds for it, or none
- [ ] #2 The counts equal those of register_map.toml and of the gate's findings on the same subject; equal on both stores and both transports
- [ ] #3 Schema subject-overview; check_mcp_server.py holds it; inputSchema refusals; CHANGELOG Unreleased under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/subject_overview.py, files only, uses the register's own loader (register_impact.load_tools, as key_nodes does) and capture.routing (the gate's owner rule). It reports:
   - nodes by kind then id, with name, state, owner and the keys resting on each;
   - every key with its nodes, owner, units and classes;
   - owners with key counts, plus a null row (no_unit, several_units);
   - the held scenario, passed in by the reader.
   task narrows the keys to one class.
2. MCP subject_overview: not store-backed. The held scenario is read as list_subjects reads it (held.owner), null with why otherwise. Its inputSchema refusals are -32602.
3. Schema subject-overview. result_marks gets its count (keys) and narrower call (task).
4. Checks:
   - tests/test_subject_overview.py recounts register_map.toml independently, and checks each key's owner against capture.finding_owners;
   - check_mcp_server, on every scenario, checks the held scenario, the map recount and every gate key finding's owner under every class, and compares stdio against HTTP.
5. instance/README.md row; CHANGELOG under Contract changes.
<!-- SECTION:PLAN:END -->
