---
id: TASK-0147
title: >-
  Instance hook: fail-closed on assistant writes to attestations, captures,
  reviews, the pre-load baseline and the register (doc-0018 candidate 5)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:24:00Z'
updated_date: '2026-11-05T22:10:00Z'
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
- [x] #1 A PreToolUse hook shipped under instance/ci/claude/ refuses, fail-closed, an assistant Edit, Write, MultiEdit or NotebookEdit that adds or changes subject.toml's [verification] or [provenance] tables, or writes under captures/, a review file, preload-baseline.json or register/; it maps through task-0099's decide
- [x] #2 An ordinary edit to subject.toml (an [[artefact]], a task class) is allowed; a malformed hook input or an unreadable file fails closed
- [x] #3 A settings snippet wires it, instance/README.md says what it guards and what it does not see (a shell command writing the same file), and CHANGELOG Unreleased carries the line
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/claude/attestation_paths.py through task-0099's decide, task-0105's pattern. 2. settings.attestations.json. 3. README, CHANGELOG, CLAUDE.md, tests/test_attestation_hook.py.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Merged as fdurieux/knowgov#241 (506b9a5). Evidence: tests/test_attestation_hook.py (6 tests: add/change of [verification]/[provenance] blocked, compared parsed before against after; an [[artefact]] or task class edit and removing both tables pass; removing [provenance] alone while [verification] stays blocked; captures/, the manifest's [capture] dir, its [verification] map, review files anywhere, preload-baseline.json and register/ blocked; malformed event, missing old_string, unparsable manifest fail closed; decide imported, never copied; the snippet wired fail-closed). run_tests 453/454 (1 skipped) on the merged head; CI tests and rdflib green.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An instance hook, `instance/ci/claude/attestation_paths.py`, refuses fail-closed an assistant's Edit, Write, MultiEdit or NotebookEdit that would attest for a person: adding or changing `subject.toml`'s `[verification]` or `[provenance]` (parsed, before against after), or writing under `captures/` (or a manifest's `[capture] dir`), its `[verification] map`, a review file, `preload-baseline.json` or `register/`. It maps through task-0099's `decide` and calls nothing else. `settings.attestations.json` wires it (repository settings or a second managed drop-in); instance/README.md's "Guarding what people attest" says what it guards and that a shell command writing the same file is unseen. Merged as #241.
<!-- SECTION:FINAL_SUMMARY:END -->
