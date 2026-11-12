---
id: TASK-0339
title: >-
  Every instance entry reads its own register (task-0334 residues, decision-0039
  §3.1)
status: To Do
assignee: []
created_date: '2026-11-12T00:45:00Z'
labels:
  - fix-only
  - 0.9.0
dependencies: []
priority: high
ordinal: 331000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Group C's re-check of task-0334 at c425ebf (decision-0039 §3.1 (a)) found two paths that still fall back to the public register (demo/register), failing open on the promise that an instance reads its own register. Pulled before the cut under decision-0032 (fails open; behind the contract task-0334 set). R1: harness/instance_register.unnamed tests KG_SUBJECT only, so KG_SUBJECTS pointing at an instance's subjects root outside the checkout, with KG_SUBJECT and KG_REGISTER unset, starts harness/mcp_server.py and demo/app/server.py on demo/register: register_impact on APP-0002 answers the public register's name, the page's /api/register/impact the same, gate_verdict's register.files the public digest; instance/README's 'without it, the server refuses to start' is false on this path. Fix: any KG_SUBJECTS root outside the checkout counts as an instance for the guard, as KG_SUBJECT does. Also low, same setup: list_subjects lists cargo_quote twice, both default true (the server's own default and the instance's); the MCP list should name each subject once, as the page does. R2: tools/check_subject.py (about :753) falls back to DEFAULT_REGISTER for a subject outside the checkout, so a standalone check passes a map row valid only against the public register; apply the same refusal (exit 2 naming KG_REGISTER or --register), check_instance already passes <instance>/register. Note only: tools/lighthouse_evidence.py (:188) defaults to demo/register too; a check tool, apply the same rule if it reads an instance subject.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 KG_SUBJECTS at an instance's subjects root outside the checkout with KG_SUBJECT and KG_REGISTER unset: the MCP server (stdio and --http) and the page refuse at start with exit 2 naming KG_REGISTER; with KG_REGISTER set they answer from the instance's register; tests on group C's repro (an instance register whose APP-0002 is renamed)
- [ ] #2 list_subjects names each subject id once
- [ ] #3 tools/check_subject.py on a subject outside the checkout with KG_REGISTER unset and no --register exits 2 naming them; check_instance unchanged; tests
- [ ] #4 Subjects inside the checkout and the compose stack (KG_REGISTER=/instance/register) unchanged; the record holds; instance/README's sentence true on every path; CHANGELOG line
<!-- AC:END -->
