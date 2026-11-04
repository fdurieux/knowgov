---
id: TASK-0111
title: >-
  register_impact: what retiring a register node touches, as a fifth read-only
  MCP tool
status: To Do
assignee: []
created_date: '2026-11-04T14:45:00Z'
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
- [ ] #1 harness/mcp_server.py offers a fifth tool, register_impact, marked read-only like the other four, taking a register id, the walk (dependants by default, realisers), the scenario and as_of; READS is unchanged and the store is never written
- [ ] #2 Its walk and reached set equal register_view.impact for every node of the vendored register, on both subjects; an unknown or malformed id is an isError result
- [ ] #3 It returns the node (kind, name, state, owner, parent), its approved children listed as not walked unless the vendored register offers the descent, each reached node's owning unit, and the register_map keys whose rows name the start or a reached node, each with the node it came through
- [ ] #4 With a scenario held, each key carries its gate level, stale finding and suspect derived outputs as gate_verdict and evidence_bundle report them on the same as_of; tools/check_mcp_server.py shows CAP-0002 on S6 naming P2|surcharge stale and derived:S1:G:run1 suspect, on rdflib and on Neo4j
- [ ] #5 CAP-0001 answers an empty walk with CAP-0002..CAP-0005 as children, until a vendored register carries decision 0014; then its children option reaches the keys through them
- [ ] #6 INSTRUCTIONS, instance/README.md's tool table and the 'four tools' wording (tests, doc-0014) say five; nothing in harness/ names a subject, a register id or a key
<!-- AC:END -->
