---
id: TASK-0110
title: >-
  A declared gap's route names the unit that closes it as well as the one that
  answers
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T12:29:00Z'
updated_date: '2026-11-04T12:47:00Z'
labels:
  - gate
  - schema
milestone: m-8
dependencies:
  - TASK-0102
priority: low
type: task
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0102, chosen by the maintainer 2026-11-04. A declared gap's finding names in route the owner that answers (ORG-0002 for CargoQuote's OD-1); under decision-0002 the gap is closed by the unit its declaration names (compliance, ORG-0004; task-0054). The route names both: who answers and who closes. Additive, schema_version stays 2 (coordinator's practice: an optional field keeps the version).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 S2's OD-1 finding names ORG-0002 as answering and ORG-0004 as closing, from the declaration, not hard-coded
- [ ] #2 The schema validates reports with and without the new field; the record and the comparator are unchanged
- [ ] #3 The hook's summary and the page's gate box show the closing unit
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.gap_closers: key -> closing unit from the declared gap's text (review.gap_owner), else the key's owners, as review.check admits a close; closing_route the close's text.
2. gate_cli.findings/report/evaluate: optional closer on a key finding at declared_gap; route ends with the close; render adds '; closed by UNIT'.
3. Schema: closer optional, description; schema_version 2.
4. Hook _summary and the page's gate box (views._closer_lines) name the closing unit.
5. Tests; record, comparator, MCP parity; CHANGELOG line under Unreleased.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
S2 via gate_cli (rdflib): OD-1's finding owner ORG-0002, closer ORG-0004, route ends with the close. Closer comes from the declaration's text through review.gap_owner, the rule review.check applies to a close; a text naming another unit names that one (tested). Comparator: 0 differing leaves over 7 scenarios (rdflib). check_mcp_server S1,S2,S6 holds. Both suites 326/326.
<!-- SECTION:NOTES:END -->
