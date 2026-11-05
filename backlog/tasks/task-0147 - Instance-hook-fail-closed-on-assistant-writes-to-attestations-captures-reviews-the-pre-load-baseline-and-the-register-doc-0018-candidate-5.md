---
id: TASK-0147
title: >-
  Instance hook: fail-closed on assistant writes to attestations, captures,
  reviews, the pre-load baseline and the register (doc-0018 candidate 5)
status: To Do
assignee: []
created_date: '2026-11-05T21:24:00Z'
labels: []
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0018 -
    A-subject-wizard-over-MCP-creating-a-subject-and-adding-its-artefacts-with-an-assistant.-Pipeline-sense-and-nonsense-fit-gap-opportunity-canvas-SWOT.md
priority: medium
type: feature
ordinal: 153000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A wizard that scaffolds a subject must never attest for a person: decision-0009 makes a load approve only what subject.toml declares, so an assistant writing [verification] or [provenance], a capture, a review file, the pre-load baseline or the register would manufacture the approval the decision exists to keep human. knowgov already guards its own protected paths this way (task-0105, through task-0099's decide); an instance needs the same for these paths. Approved by the maintainer on 2026-11-05.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A PreToolUse hook shipped under instance/ci/claude/ refuses, fail-closed, an assistant Edit, Write, MultiEdit or NotebookEdit that adds or changes subject.toml's [verification] or [provenance] tables, or writes under captures/, a review file, preload-baseline.json or register/; it maps through task-0099's decide
- [ ] #2 An ordinary edit to subject.toml (an [[artefact]], a task class) is allowed; a malformed hook input or an unreadable file fails closed
- [ ] #3 A settings snippet wires it, instance/README.md says what it guards and what it does not see (a shell command writing the same file), and CHANGELOG Unreleased carries the line
<!-- AC:END -->
