---
id: TASK-0317
title: >-
  demo.yml: the held-store check compares real generations, not two empty
  strings
status: To Do
assignee: []
created_date: '2026-11-10T01:41:00Z'
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
- [ ] #1 gen() prints the extraction activities and a real generation pair on Neo4j; the step fails if gen() fails or prints nothing
- [ ] #2 held before equals held after on a green run, and a deliberately published S2 makes them differ (shown once locally or in the PR)
- [ ] #3 No other workflow step reads a private attribute that does not exist (grep the workflows for _inner.)
<!-- AC:END -->
