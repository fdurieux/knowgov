---
id: TASK-0255
title: >-
  An annotated proposal template: every field proposal_impact reads, explained
  in plain English, held by a test
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T07:58:00Z'
updated_date: '2026-11-09T08:26:00Z'
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
- [x] #1 instance/templates/proposal.toml (or the layout's place) carries every field proposal_impact reads, each commented in plain English, with how to choose provisional ids and find reusable register ids
- [x] #2 A test holds that proposal_impact reads the template with its placeholders filled from the example register (tools/example_instance.py), and that every field the reader accepts appears in it
- [x] #3 demo/README.md's proposal section and the slicing guidance point to the template
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/templates/proposal.toml: every field harness/proposal_impact.py reads (title; nodes id, kind, name, parent, owner, source; links id, type, source, target, rationale, owner; reused id with mode as_is and changed; exceptions id, rule, scope, expires, rationale), each commented in plain English: the metamodel's kinds and parents, the relationship types, provisional ids that cannot collide ('new-contract-quote'; knowgov never mints a register id; a register-shaped one the register does not hold is kept, one it holds refused), and {{PLACEHOLDER}} register ids found with register_nodes. instance/README.md's 'Writing a proposal before the pull request'; demo/README.md points to it from 'A proposal read before approval' and 'What exists, step by step'. tests/test_proposal_template.py fills the placeholders from a tools/example_instance.py build's register, reads the template with read_proposal and evaluate (nodes hypothetical, provisional ids kept and none a register id, reused modes as written, no placement error), and holds its fields equal to the reader's top-level set, NODE_FIELDS, LINK_FIELDS, EXC_FIELDS and MODES; it passes without PyYAML. CHANGELOG under Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
