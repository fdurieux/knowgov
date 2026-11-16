---
id: TASK-0360
title: >-
  who_knows: a read-only MCP tool naming the handles, and their holders, whose
  attested evidence touches a node, a key or a code path (decision-0047 step 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-16T19:16:00Z'
updated_date: '2026-11-16T21:11:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
references:
  - backlog/decisions/decision-0047
priority: high
ordinal: 350000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0047 point 2. knowgov holds who said what under a handle (captures, reviews, declared-gap closes) and, after ieam-register decision 0021, who holds each handle; nothing lets a reader ask who knows about a register node, a key or a code path. Ships in 0.10.0 (decision-0047 point 4, the maintainer's option (A)). Never a score or ranking, never across registers (point 6).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 who_knows takes exactly one of a register node id, a key, or a code path under code_map.toml's root, and refuses anything else with -32602
- [x] #2 Its answer lists, per handle, unit, roles, holder (the register's person, or null with why) and evidence items of kinds answered, approved/rejected, closed and owns, sorted by kind, key and date, handles by id, with no rank, weight or score
- [x] #3 It reads the reader's subjects and their one register from files, so the report is equal on the Neo4j and rdflib stacks and over stdio and HTTP; schema who-knows; check_mcp_server.py holds it
- [x] #4 CHANGELOG Unreleased carries it under its contract-change heading; the adopter docs say an organisation serves holders only under its recorded basis (ieam-register 0021 §4)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/who_knows.py: scope (node, key or code path) from the reader's subjects' register_map.toml rows, code_map.toml and the file's citation header; evidence per handle from each subject's captures ([capture] dir) and reviews (rulings, closes of capture-declared gaps), owns from the register's owning unit; holder from people/handles.toml person, else null with why. Files only, no store. Also a CLI.
2. MCP tool who_knows in harness/mcp_server.py: exactly one of node, key, path refused -32602 otherwise (argument_refusal, no top-level oneOf, which some clients' model APIs reject); no subject argument (it spans the reader's subjects, as list_subjects); OUTPUT_SCHEMAS who-knows.
3. harness/schemas/who-knows.schema.json.
4. Fixture tools/fixtures/knowledge_probe/: an instance-shaped root, one unlisted subject with captures and reviews on the demo register's synthetic handles, code_map.toml and a cited code file, and the expected reports.
5. tools/check_mcp_server.py: who_knows on the fixture over stdio and HTTP equal to the module's report and to the frozen expected reports, so the rdflib and Neo4j jobs hold one answer.
6. tests/test_who_knows.py (stdlib), test_mcp_server tool list, test_mcp_output_schemas.
7. CHANGELOG Unreleased contract-change heading; instance/README.md: the tool, and holders served only under the organisation's recorded basis (ieam-register 0021 §4).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built: harness/who_knows.py (module and CLI), the MCP tool who_knows, harness/schemas/who-knows.schema.json, the fixture tools/fixtures/knowledge_probe (an unlisted subject with three captures and two reviews on the demo register's synthetic handles, one unlisted handle, a code map and a cited file, and the expected reports), check_mcp_server.py's check_who_knows (stdio both eras and HTTP, equal to the expected reports, -32602 refusals; the store's census unchanged), tests/test_who_knows.py.
Choices: exactly one of node, key and path is enforced in argument_refusal (mcp_server.EXACTLY_ONE), not by a top-level oneOf, which some clients' model APIs refuse in a tool's input schema and schema_check does not read. who_knows takes no subject argument (mcp_server.ACROSS_SUBJECTS, with list_subjects): it reads every subject the reader serves. A path reads code_map.toml against KG_REGISTER's applications, the one register the subjects share. Item order: kind alphabetical (answered, approved, closed, owns, rejected), then key (a node for owns), then date.
Where the decision's text meets the files: (1) closed reads only a capture-declared gap's key (gap:declared:capture:<stem>:<n>); a [[closes]] entry records gap and digest, no key, so a close of a gap a document declares cannot be placed on a key without the store; (2) review files are read as written, not as the load applied them (a refused review still names its rulings); (3) handles.toml carries no person in the vendored register (v0.2.13), so every holder reads null with holder_why until task-0362.
Local proof: python tests/run_tests.py 1244/1349 passed, 105 skipped, 0 failed; KG_STORE=rdflib python tools/check_mcp_server.py --scenarios S1: every check holds, who_knows 9 answers equal to the expected reports.

CI on ff6556a (PR #574): tests, rdflib, rdflib-readers and stack green; stack step 14 ran tools/check_mcp_server.py --scenarios S1,S2,S6 on the Neo4j store, check_who_knows included, and the rdflib job the same check on rdflib, both against the knowledge probe's one set of expected reports: equal on both stores and over stdio and HTTP. The merge of main (decision-0047 accepted, #575) changed no code.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
who_knows (decision-0047 point 2) is a read-only MCP tool and CLI, harness/who_knows.py. For exactly one register node, key or code path (anything else -32602), it names the handles whose attested evidence touches it, one hop: their unit, roles, dates and holder (the register's person, or null with holder_why), and their evidence by kind (answered, approved, rejected, closed, owns), sorted, never scored. It reads files only across the reader's subjects, so it answers the same on Neo4j and rdflib; schema who-knows; held by check_mcp_server.py to tools/fixtures/knowledge_probe's expected reports in the rdflib and stack jobs. Limits named in the notes: closed reads only captured gaps' keys; review files are read as written; holders are null until task-0362 re-vendors the register with person.
<!-- SECTION:FINAL_SUMMARY:END -->
