---
id: TASK-0123
title: >-
  Register ids stamped into the source tool: an identity-only write of the
  register id into ARIS's id attribute
status: To Do
assignee: []
created_date: '2026-11-04T19:05:00Z'
labels:
  - aris
  - connector
milestone: m-8
dependencies:
  - TASK-0063
priority: low
type: feature
ordinal: 123000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0015 (2026-11-04, maintainer's go). ARIS rewrites element ids on BPMN import (only process ids survive), so the register id must ride in an attribute the tool keeps: AT_ID by default, configured in connectors.toml (task-0063, task-0121). A narrow, identity-only write: for each register node whose source is the tool, write its register id into the configured attribute of the matching object, via the client's ARIS API or report script, run in the client's environment. Never content, never status: the tool stays the author (ieam-register: a node file never copies a tool's attributes). knowgov ships the script template and its dry-run report, not a live integration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A dry run over the synthetic CargoQuote AML lists, per object, the register id it would write and the objects it cannot match, writing nothing
- [ ] #2 The write path is a template the client runs in its own environment; nothing under harness/ or demo/app calls the tool
- [ ] #3 The README states it writes identity only and why (the tool stays the author); verified on a real ARIS only at the pilot
<!-- AC:END -->
