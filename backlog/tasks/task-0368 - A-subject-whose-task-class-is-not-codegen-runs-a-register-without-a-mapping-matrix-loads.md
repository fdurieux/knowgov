---
id: TASK-0368
title: >-
  A subject whose task class is not codegen runs; a register without a mapping
  matrix loads
status: In Progress
assignee: []
created_date: '2026-11-16T21:25:00Z'
labels:
  - fix
  - run
  - page
dependencies: []
modified_files:
  - harness/subject.py
  - harness/run.py
  - harness/gate_cli.py
  - harness/mcp_server.py
  - demo/app/page_subject.py
  - demo/app/register_view.py
priority: high
ordinal: 358000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-16: the page's Deterministic button on a private instance subject (one task class, not named codegen) failed with 'run: cannot run: KeyError: 'codegen'', and the register panel failed whole: '[Errno 2] No such file or directory: /instance/register/mapping/matrix.toml'. run.py resolved the gate on the literal codegen class (as did gate_cli's record baseline, _change and _register_change, and the page's key count); register_view read the matrix unconditionally though the register's own checker never reads it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 run.py resolves the gate, stage 2 and the arms' default prompt on Subject.record_task (codegen where declared, else the first class); a subject with no class exits 2 naming it
- [ ] #2 gate_cli's record baseline, _change and _register_change and the page's key count read the same record task
- [ ] #3 register_view loads a register without mapping/matrix.toml and says it has no mapping matrix
- [ ] #4 tests cover both; the record and the comparator are unchanged; CHANGELOG Unreleased
<!-- AC:END -->
