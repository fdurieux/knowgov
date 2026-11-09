---
id: TASK-0255
title: >-
  An annotated proposal template: every field proposal_impact reads, explained
  in plain English, held by a test
status: To Do
assignee: []
created_date: '2026-11-09T07:58:00Z'
labels:
  - docs
  - proposal
  - template
dependencies: []
priority: medium
ordinal: 249000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-09: "yes, extend task-0253, mint the view and the template". No feature-proposal template exists: the format lives in harness/proposal_impact.py's docstring and the MCP tool's input description, with one worked example (tools/fixtures/proposal_contract_quote.json) and demo/README.md's "A proposal read before approval". A product owner needs a blank, annotated starting point. instance/templates/proposal.toml (or wherever instance/kinds.toml's layout puts templates): title; nodes (id, kind, name, parent, owner, optional source); links (type, source, target, rationale, optional owner); reused (as_is or changed); optional exceptions (rule, scope, expires, rationale). Its comments say, in plain English, what each field means, how to choose a provisional id that does not collide with the register's, and how to find register ids to reuse (register_nodes). Documentation only, no contract change: a 0.9.x patch under decision-0016 point 2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/templates/proposal.toml (or the layout's place) carries every field proposal_impact reads, each commented in plain English, with how to choose provisional ids and find reusable register ids
- [ ] #2 A test holds that proposal_impact reads the template with its placeholders filled from the example register (tools/example_instance.py), and that every field the reader accepts appears in it
- [ ] #3 demo/README.md's proposal section and the slicing guidance point to the template
<!-- AC:END -->
