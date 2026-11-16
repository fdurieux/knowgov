---
id: TASK-0364
title: >-
  gate_verdict: a summary mode that returns counts by owner unit, level,
  severity and kind, the full findings only on request (0.10.0)
status: To Do
assignee: []
created_date: '2026-11-16T20:24:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
priority: medium
ordinal: 354000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer asked a Claude Desktop session over MCP for a private subject's gate verdict (197 keys). The full report was about 156,000 characters, over the reader's response limit; the assistant read it back from a saved file and summarised it, and stated one count wrongly (every key's owner as one unit, where the report holds 104 and 93 across two). A large subject's report is too big for an assistant to read whole. The maintainer, 2026-11-16: "yes, note the gate_verdict summary mode for 0.10.0"; it joins 0.10.0 beside decision-0047's tools, an additive contract change in the same restarted soak.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 gate_verdict takes an optional argument selecting a summary: the verdict, why, the bar, the identity fields, and counts by owner unit, by level, by severity and by finding kind, with no per-key findings
- [ ] #2 The default answer is unchanged (no existing caller sees a difference), unless the coordinator records otherwise in the PR with the reason
- [ ] #3 The summary's counts equal those computed from the full report on the same store, on Neo4j and rdflib and over both transports; check_mcp_server.py holds it; a schema for the summary shape
- [ ] #4 A finding filter (by owner, level, kind or key) returns only those findings, so an assistant can ask narrowly instead of reading the whole report
- [ ] #5 CHANGELOG Unreleased under contract changes; the MCP reader docs name the summary as the first call for a large subject
<!-- AC:END -->
