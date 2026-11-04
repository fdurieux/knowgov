---
id: TASK-0099
title: A fail-closed hook recipe for the gate, with a managed-settings variant
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-04T10:58:00Z'
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
- [x] #1 A test runs the script against PROCEED, BLOCKED, an unreachable store and a missing subject; only PROCEED lets the action through
- [x] #2 The instance README says where each settings file goes and that only the managed one is mandatory
- [x] #3 The recipe's header cites doc-0004's exit-code paragraph as superseded by doc-0014
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/claude/knowgov_hook.py: stdlib, PreToolUse event on stdin; transitions plan (ExitPlanMode), spec (git commit carrying spec.md globs), push (git push); anything else exit 0 with no decision.
2. decide(): gate 0 -> 0; 1 -> 2 naming findings and route to approval; 2/other -> 2 naming the gate unavailable; --advisory lets 2 through with a FAIL-OPEN systemMessage. A report for keys, another task, missing or disagreeing with the exit code is refused (blocked). run -- CMD maps any contract check; decide importable (task-0105).
3. Three snippets: settings.json (repository), managed-settings.json (allowManagedHooksOnly, allowManagedMcpServersOnly, knowgov allowlisted), settings.advisory-fail-open.json; onFailure block on the two mandatory-shaped ones.
4. tests/test_claude_hook.py: stub gate for PROCEED/BLOCKED/refusals/transitions; real knowgov-gate.sh for a missing subject and an unreachable store; live rdflib PROCEED/BLOCKED under KG_HOOK_LIVE=1 in harness.yml's rdflib job.
5. instance/README.md section: where each file goes, only the managed one mandatory, one store per worktree.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Hook contract checked against code.claude.com/docs/en/hooks (2026-11-04): exit 2 blocks PreToolUse and stderr is the reason Claude sees; exit 1 is non-blocking unless onFailure: block (v2.1.295+); ExitPlanMode is a PreToolUse tool name. The snippets use one ExitPlanMode|Bash matcher with no if filter: the docs call if best-effort and git -C x push would miss Bash(git push *), so the script decides. Live check on rdflib locally: CargoQuote S1 PROCEED goes ahead, S2 BLOCKED exits 2 naming QuoteAPI|on_screening_outage and response|hold_presence; neo4j at bolt://127.0.0.1:9 exits 2 as unavailable. Both suites 307/307.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/ci/claude/ gains knowgov_hook.py (stdlib) and three settings snippets: settings.json (repository), managed-settings.json (allowManagedHooksOnly, allowManagedMcpServersOnly, knowgov allowlisted), settings.advisory-fail-open.json. The hook fires only at plan (ExitPlanMode), spec commit and push. It maps gate 1 and 2 both to Claude Code's blocking exit 2, naming a finding or the gate unavailable and the route to approval. It refuses a keys or other-task report. --advisory is doc-0004's adapter, labelled fail-open. decide() and 'run -- CMD' are the mapping for task-0105 to reuse. The header cites doc-0004's Exit codes paragraph as superseded by doc-0014. The instance README places each file and says only the managed one is mandatory, and one store per worktree. tests/test_claude_hook.py covers PROCEED, BLOCKED, an unreachable store and a missing subject; only PROCEED goes through. It runs live on rdflib in harness.yml. Risk: the vendor's hook semantics (exit 2, onFailure from v2.1.295) are as documented on 2026-11-04.
<!-- SECTION:FINAL_SUMMARY:END -->
