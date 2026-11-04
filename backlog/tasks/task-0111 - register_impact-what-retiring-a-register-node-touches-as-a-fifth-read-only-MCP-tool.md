---
id: TASK-0111
title: >-
  register_impact: what retiring a register node touches, as a fifth read-only
  MCP tool
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T14:45:00Z'
updated_date: '2026-11-04T15:24:00Z'
labels:
  - mcp
  - register
milestone: m-8
dependencies: []
references:
  - harness/mcp_server.py
  - demo/app/register_view.py
  - subjects/cargo_quote/register_map.toml
  - https://github.com/fdurieux/ieam-register/blob/main/METAMODEL.md
priority: medium
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Asked over MCP (Claude Desktop, cargo_quote S6) what retiring CAP-0001 touches, an assistant could only answer 'not in the store': no tool takes a register id, `register_map.toml` is never exposed, and `READS` (harness/mcp_server.py) admits no register read. The page's impact panel (`GET /api/register/impact/<id>`, `register_view.impact`) and the saved Cypher answer it for a human; MCP, the route with the least exposure (read-only, loopback, token), answers it for no one. The missing step is register id -> walk -> map rows -> keys; every read after that (gate levels, stale, suspect derived) is already in `READS`.

CAP-0001 is a capability domain with no links of its own: its walk is empty in both the register and knowgov (`tests/test_register_view.py`), while all 36 codegen keys rest on its children CAP-0002..0005 or on what they reach. Descending `parent` is the register's call: ieam-register decision 0014 (proposed) offers it as `impact.py --children`; decision 0015 (proposed) makes an approved child of a deprecated parent a checker error. This tool follows whatever the vendored register's walk does and never descends `parent` on its own.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 harness/mcp_server.py offers a fifth tool, register_impact, marked read-only like the other four, taking a register id, the walk (dependants by default, realisers), the scenario and as_of; READS is unchanged and the store is never written
- [x] #2 Its walk and reached set equal register_view.impact for every node of the vendored register, on both subjects; an unknown or malformed id is an isError result
- [x] #3 It returns the node (kind, name, state, owner, parent), its approved children listed as not walked unless the vendored register offers the descent, each reached node's owning unit, and the register_map keys whose rows name the start or a reached node, each with the node it came through
- [ ] #4 With a scenario held, each key carries its gate level, stale finding and suspect derived outputs as gate_verdict and evidence_bundle report them on the same as_of; tools/check_mcp_server.py shows CAP-0002 on S6 naming P2|surcharge stale and derived:S1:G:run1 suspect, on rdflib and on Neo4j
- [x] #5 CAP-0001 answers an empty walk with CAP-0002..CAP-0005 as children, until a vendored register carries decision 0014; then its children option reaches the keys through them
- [x] #6 INSTRUCTIONS, instance/README.md's tool table and the 'four tools' wording (tests, doc-0014) say five; nothing in harness/ names a subject, a register id or a key
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/register_impact.py: load the register's register.py/impact.py by path from KG_REGISTER (cadence.register_root); walk(node, walk) -> register {tag, commit}, node, children (listed, walked false), edges with live, reached by prefix with owning_unit; landed_rows from register_map.toml with via; with_levels from gate_cli.evaluate over the landed keys (task keys, route codegen), so each key reads as gate_verdict reports it.
2. mcp_server.py: fifth tool register_impact (READ_ONLY), inputs node/walk/scenario/as_of; READS unchanged; answers without a store when no scenario is named.
3. Tests: five tools; walk/reached/owners equal register_view.impact for every node; CAP-0001 children; isError; levels equal gate_verdict, no write.
4. tools/check_mcp_server.py: stage 1 levels equal gate_verdict; S6 stage 2 names each stale key's statement and suspect derived output.
5. Docs: INSTRUCTIONS, instance/README.md table, docs/security.md, doc-0014, CLAUDE.md, CHANGELOG Unreleased.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR #190. Children: CAP-0005 is proposed, so AC#3 (approved children) and AC#5 (CAP-0002..0005) disagree; every child is listed with its state, walked false. The S6 suspect check reads gate_verdict's live report, not the record: d3check/S6 holds no Derived node (task-0018). Verified: tests 333/333 both subjects; check_mcp_server rdflib S1,S6 and J-F C hold.
<!-- SECTION:NOTES:END -->
