---
id: TASK-0067
title: >-
  Decide whether a document's verification by review lapses by date, under the
  register's review cadence
status: To Do
assignee: []
created_date: '2026-11-03T23:53:00Z'
labels:
  - capture
  - gate
milestone: m-5
dependencies:
  - TASK-0039
references:
  - backlog/docs/doc-0013
priority: medium
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P1. A review verification never lapses by date: a statement verified by review stays verified however long its document goes untouched, while a person's answer lapses in six months (register decision 0008). The register already sets review months per kind (metamodel/lifecycle.toml). Needs a maintainer decision first: options (a) no date lapse, documented; (b) the owning kind's review months, then the statement reads validated (recommended by doc-0013); (c) one default.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A knowgov decision record (proposed, the maintainer approves by merging) weighs the options with their effect on the record's S1–S7 verdicts and on gate_cli --baseline record
- [ ] #2 The record is consistent with decision-0004 (option B) and names the contract change under decision-0003
<!-- AC:END -->
