---
id: TASK-0051
title: >-
  knowgov-trace register and check: a CI hook from a code change to the
  knowledge
status: To Do
assignee: []
created_date: '2026-11-03T22:41:00Z'
labels:
  - traceability
  - gate
milestone: m-7
dependencies:
  - TASK-0048
  - TASK-0049
  - TASK-0050
priority: medium
type: feature
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 3 sketch: a platform-neutral command with two subcommands. register records a build's output as a derived node with the assertions it used (store.register_derived, USED_ASSERTION) and its file digests; check, on a later change, finds the registered outputs whose files or whose assertions changed and reports them through the gate's contract (exit 0/1/2, JSON under a schema). Nothing platform-specific in harness/.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register and check subcommands with explicit inputs, the 0/1/2 exit and a shipped JSON schema
- [ ] #2 On the example instance, S6 as acceptance: a registered build becomes suspect after the stage-2 change and check exits 1, naming the APP from code_map.toml
- [ ] #3 harness.yml runs the walkthrough on rdflib
<!-- AC:END -->
