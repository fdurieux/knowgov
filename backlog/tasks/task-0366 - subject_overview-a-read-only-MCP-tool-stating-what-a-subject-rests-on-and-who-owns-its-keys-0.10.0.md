---
id: TASK-0366
title: >-
  subject_overview: a read-only MCP tool stating what a subject rests on and who
  owns its keys (0.10.0)
status: Done
assignee: []
created_date: '2026-11-16T20:28:00Z'
updated_date: '2026-11-28T00:55:00Z'
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
- [x] #1 subject_overview(subject) returns, from files: the register nodes the subject's keys rest on, by kind and id with names and owners; the owner units with their key counts; the scenario the store holds for it, or none
- [x] #2 The counts equal those of register_map.toml and of the gate's findings on the same subject; equal on both stores and both transports
- [x] #3 Schema subject-overview; check_mcp_server.py holds it; inputSchema refusals; CHANGELOG Unreleased under contract changes
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proven locally, rdflib, pinned clock (2026-11-27):
- check_mcp_server passes on CargoQuote (S1-S7), J-F C,D3 and minimal. On every scenario, subject_overview names the held scenario, and its 57 keys, 57 rows and 20 nodes (J-F: 163, 163, 24) are the register map's, recounted from the file. Every gate key finding under every class names the owner it gives: 5 to 116 findings per scenario. It answers equal over stdio and HTTP.
- tests/test_subject_overview.py: 4 tests on both subjects. They check the counts against the file, the owners against capture.finding_owners, the task narrowing, exit 2, and the -32602 refusals.
- Pinned suite: 1416/1417.
- Neo4j is left to the stack job.
- main (#605) is merged in.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in knowgov #606 (6644261), merged on the whole matrix green with stack. subject_overview is a read-only, files-only MCP tool and command with schema subject-overview. It returns the nodes register_map.toml's rows name, read by the register's own loader, with name, state, owner and key count. It returns every key with its nodes, its owner (capture.routing, the owner the gate's findings name) and its classes; the owner units with key counts, plus a null row for no_unit and several_units; and the held scenario for the subject, or null with why. task narrows to one class, and bad arguments return -32602. It never infers a link that no row names, and task-0365's marks apply. check_mcp_server.py holds it on every scenario: CargoQuote 57 keys / 57 rows / 20 nodes, J-F 163 / 163 / 24, the gate's owner per key under every class, stdio equal to HTTP.
<!-- SECTION:FINAL_SUMMARY:END -->
