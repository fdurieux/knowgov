---
id: TASK-0007
title: Gate CLI conforming to the site's gate contract
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-02T22:47:00Z'
labels:
  - platform
  - gate
milestone: m-3
dependencies:
  - TASK-0003
priority: low
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gate returns PROCEED, QUALIFIED or BLOCKED to an assistant and writes files; it has no command-line form and no exit code. The programme's gate contract on fdurieux.github.io asks for exit codes 0, 1 and 2, a severity threshold, a baseline and ratchet, JSON under a published schema, and evidence tags. A CLI form makes knowgov a programme project in the site's sense and lets it claim table rows honestly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A command resolves a task against a loaded subject and exits 0 on PROCEED, 1 on BLOCKED or on QUALIFIED above a chosen threshold, 2 when it cannot run
- [ ] #2 The JSON report is validated against a shipped schema
- [ ] #3 The record is the baseline: a verdict worse than the record's for the same subject and task is a regression
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/gate_cli.py: load the scenario as a deterministic run does (stage 1, rules included), resolve the task through harness/gate.py, findings on the contract's ladder (blocker: a key at a block level, or the task blocked by its unverified share; major: below verified; minor: flagged), exit 0/1/2.
2. --fail-on sets the threshold (blocker by default: PROCEED and QUALIFIED pass).
3. --baseline record|FILE ratchets: exit 1 only on a verdict worse than the baseline's or a key at a lower level; the gate never writes a baseline (-o writes a report, keeping it is a commit).
4. harness/schemas/gate-report.schema.json, checked before printing by harness/schema_check.py (a stdlib subset validator modelled on pumllint's, refusing unknown keywords).
5. --no-load reads the store as the page left it and refuses another scenario.
6. Tests on every record scenario (stdlib); harness.yml on rdflib; the stack job on Neo4j. README section in the adopter register.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Out of scope, said here: SARIF (the contract's second format) and evidence tags (a project-claims property, not the command's); the AC asks for JSON under a schema. Verified on rdflib: S1 0, S2 1, S3 0 and 1 with --fail-on major, S2 --baseline record 0, S2 against a saved S1 report 1 (verdict worse, three keys lower), J-F C --baseline record 0, minimal 1, unknown scenario or task 2, empty store with --no-load 2, Neo4j unreachable 2. Tests 118/118.
<!-- SECTION:NOTES:END -->
