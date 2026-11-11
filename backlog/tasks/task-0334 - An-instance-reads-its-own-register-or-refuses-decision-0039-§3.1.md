---
id: TASK-0334
title: An instance reads its own register or refuses (decision-0039 §3.1)
status: To Do
assignee: []
created_date: '2026-11-11T22:53:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 326000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.1 (a), doc-0038 §3.1. Today harness/cadence.py register_root (about :35) and harness/capture.py register_root (about :71) fall back to demo/register, the public register, when KG_REGISTER is unset; instance/ci/knowgov-gate.sh and instance/ci/claude/knowgov_hook.py never set it. A client's verdicts, review cadence and accepted givers then follow the public register. Build: one shared helper. When the subject (KG_SUBJECT, --subject) lies outside the knowgov checkout (the test execution_guard already uses) and KG_REGISTER is unset, every register-reading tool refuses with exit 2 naming KG_REGISTER: gate_cli, run.py, trace, capture.py, register_impact, proposal_impact, register_nodes, upward, the MCP server at start, and cadence's lifecycle months. knowgov-gate.sh and knowgov_hook.py pass KG_REGISTER=<instance>/register unless one is set. instance/README's 'Running the gates' and 'Capturing what people know' say so, and docs/contracts or the KG_* settings table updates KG_REGISTER's effective default. Subjects inside the checkout keep demo/register, so the record does not move.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 On a copy of the example instance outside the checkout with KG_REGISTER unset, each listed tool exits 2 naming KG_REGISTER; with it set, the instance's lifecycle months and handles decide; tests
- [ ] #2 knowgov-gate.sh and the hook pass <instance>/register by default; tools/check_ci_wrappers.py holds it
- [ ] #3 Subjects inside the checkout read demo/register as before; the record holds; docs updated, tests/test_docs_* hold
<!-- AC:END -->
