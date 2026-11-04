---
id: TASK-0100
title: One as_of per MCP server process
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-04T11:18:00Z'
labels:
  - mcp
  - clock
milestone: m-8
dependencies: []
priority: high
type: feature
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C2). harness/mcp_server.py reads KG_AS_OF (YYYY-MM-DD, record or today) once at start; gate_verdict and evidence_bundle use it unless a call names its own date, and both results and store_status carry the date read. The default is the maintainer's decision recorded in doc-0014 DECIDE 1 (recommended: today for both tools, as the CLI; a minor contract change under decision-0003). check_mcp_server.py and lighthouse_evidence.py already pass record and are unaffected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With no argument, one session's verdict and bundle carry the same as_of
- [ ] #2 tests/test_clock.py names the new read and holds it pinned
- [ ] #3 CHANGELOG names the changed default
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. mcp_server.Tools: read KG_AS_OF (default today) once, resolve today/record once per process (cached, locked); gate_verdict and evidence_bundle default to the session date; an explicit argument wins. main() resolves at start, exits 2 on a bad KG_AS_OF or a pinned clock without KG_TODAY; --as-of flag over KG_AS_OF.
2. store_status carries as_of and its source.
3. Tests: test_mcp_server (one session, verdict and bundle same as_of; explicit record still wins), test_clock (names the KG_AS_OF read, holds it pinned).
4. CHANGELOG Unreleased: evidence_bundle default record -> session date; store_status as_of.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Decided 2026-11-04 by the maintainer (doc-0014 §11, #170): the default is today for both gate_verdict and evidence_bundle; evidence_bundle loses its record default, which stays an explicit choice. A contract change under decision-0003, so a minor version, named in the CHANGELOG. The split default is not kept as documentation.

Implemented: Tools(as_of) reads KG_AS_OF once (Tools.__init__), resolves today/record once per process under a lock; main() resolves at start (exit 2 on a bad date or a pinned clock without KG_TODAY), --as-of flag; the HTTP start line names the date. store_status carries as_of and as_of_from. evidence_bundle default record -> session date. tests: test_mcp_server one-session test, test_clock names the read and holds it pinned, test_lighthouse and the stdio test pin KG_TODAY for the server start. CHANGELOG ## Unreleased (test_release now admits one leading Unreleased section; release.yml stays strict at tag time). instance/README and CLAUDE.md updated.
<!-- SECTION:NOTES:END -->
