---
id: TASK-0099
title: A fail-closed hook recipe for the gate, with a managed-settings variant
status: To Do
assignee: []
created_date: '2026-11-04T09:47:00Z'
labels:
  - ci
  - gate
  - security
milestone: m-8
dependencies: []
priority: high
type: feature
ordinal: 102000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C1, C4); supersedes doc-0004's fail-open exit-code adapter. instance/ci/claude/ gains a hook script and two settings snippets: a repository .claude/settings.json, and a managed-settings fragment (allowManagedHooksOnly, the knowgov MCP server allowlisted). The script calls knowgov-gate.sh gate with a task class; exit 1 and exit 2 both map to the vendor's blocking exit, with a message naming the cause (a finding, or the gate unavailable) and the route to approval; a report produced with an agent-chosen keys set is refused. It fires at stage transitions (plan accepted, spec committed, before push), never on every edit (playbook p. 27). An advisory profile, labelled fail-open, is offered separately. The recipe states one store per worktree (C5, isolation); task-0097 is compatible.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test runs the script against PROCEED, BLOCKED, an unreachable store and a missing subject; only PROCEED lets the action through
- [ ] #2 The instance README says where each settings file goes and that only the managed one is mandatory
- [ ] #3 The recipe's header cites doc-0004's exit-code paragraph as superseded by doc-0014
<!-- AC:END -->
