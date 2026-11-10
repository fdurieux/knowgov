---
id: TASK-0317
title: >-
  demo.yml: the held-store check compares real generations, not two empty
  strings
status: Done
assignee: []
created_date: '2026-11-10T01:41:00Z'
updated_date: '2026-11-10T02:48:00Z'
labels:
  - ci
  - integrity
  - 0.9.0
dependencies: []
priority: high
ordinal: 310000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut: CI evidence that cannot fail (the coordinator, 2026-11-10). Seen in #458's stack log by session_01HTAA1S4moCRD3gDtqgMWw1; the cause is on main.

`.github/workflows/demo.yml`, the step that holds `gate_cli` (S2, private, and the --no-load runs) to leave the held store unchanged, defines
`gen() { docker compose exec -T app python -c '... st = open_store(access="read"); print(st.extraction_activities(), st._inner.generation()); ...'; }`.
`generation()` lives on `store_neo4j._Unit` (the store's `_pub`), not on `Neo4jStore`, so each call raises `AttributeError: 'Neo4jStore' object has no attribute 'generation'`. Under `set +e` both captures are empty, and `test "$before" = "$after"` compares two empty strings, which always passes. The check came in with e22975e (task-0184) and has probably never compared anything.

Fix: read the generation through a supported path (a read method of the port, or the store's publication), make `gen()` fail the step when it cannot read, and assert that `before` is non-empty. A test or check fails if the helper returns nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 gen() prints the extraction activities and a real generation pair on Neo4j; the step fails if gen() fails or prints nothing
- [x] #2 held before equals held after on a green run, and a deliberately published S2 makes them differ (shown once locally or in the PR)
- [x] #3 No other workflow step reads a private attribute that does not exist (grep the workflows for _inner.)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Read the held store's generation through the store's publication (the port has no public generation read), fail the step when gen() cannot read or prints no pair, and guard both captures.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1RoY1BKE3uQdhMuyKK (#461, merged as 1977356 on a whole green matrix with stack); recorded by the coordinator, the builder having no backlog CLI. gen() reads st._inner._pub.generation() with a comment: ReadOnly passes store.READS only and generation() lives on _Unit; the port is unchanged. #461's stack log shows 'held before: ['act:extract:S1:v1'] (6, 6)' and 'held after:  ['act:extract:S1:v1'] (6, 6)', where both were empty before, and no AttributeError. Locally on Neo4j 5.26 a deliberate --publish moved (1, 1) to (2, 2). The workflows' other underscore reads (t._old_list_runs, t._old_sources_for, gate_cli._load) resolve. tests/test_workflow_shell.py holds the step: no _inner.generation( call, generation defined on _Unit, both captures guarded.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
demo.yml's held-store check now compares real generations: gen() reads the store's publication, fails the step when it cannot read or prints no pair, and both captures are guarded, so the check can fail again. It had compared two empty strings since task-0184. Proven by #461's stack log ((6, 6) before and after), a local Neo4j publish moving the pair, and tests/test_workflow_shell.py. No harness or contract change.
<!-- SECTION:FINAL_SUMMARY:END -->
