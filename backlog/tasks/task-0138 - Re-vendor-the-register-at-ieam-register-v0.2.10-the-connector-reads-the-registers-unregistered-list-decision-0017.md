---
id: TASK-0138
title: >-
  Re-vendor the register at ieam-register v0.2.10: the connector reads the
  register's unregistered list (decision 0017)
status: To Do
assignee: []
created_date: '2026-11-05T10:41:00Z'
labels:
  - register
  - connector
milestone: m-8
dependencies: []
priority: medium
type: task
ordinal: 138000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On the maintainer's go of 2026-11-05. ieam-register v0.2.10 (4149e06, decision 0017) adds `unregistered` to `RECONCILE.json`: the export's ids (`MANIFEST.toml` `[ids]` keys) that no node's `[source]` carries, keyed by the system's `id_field`, and a per-system `exports` count in `check_register.py --report`. knowgov vendors the register at a tag (`tools/vendor_register.py`) and its connector imports the vendored `reconcile.py` (task-0121), adding its own extensions, among them `unknown_ids`: carried register ids the register does not hold. Re-vendor at v0.2.10 and let the connector's RECONCILE.json carry the register's `unregistered` as computed by the vendored code. Then compare `unknown_ids` with `unregistered` on the synthetic ARIS fixtures: if they are the same set, drop the extension (the register's field replaces it); if they answer different questions (an unknown register id typed in the tool versus an export object no node carries), keep both and document the difference. Either outcome is recorded in the task notes with the fixture numbers. Tags v0.2.9 → v0.2.10 in tests and workflows; CargoQuote's and J-F's records unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 vendor_register.py at v0.2.10 from a clean checkout; SOURCE.md and every digest test pass; the vendored reconcile.py writes unregistered
- [ ] #2 connector.py's RECONCILE.json carries unregistered for the synthetic ARIS exports (first and later), as the register computes it; tests hold the entries
- [ ] #3 unknown_ids is either dropped (same set as unregistered, shown on the fixtures) or kept with its distinct meaning documented in instance/README.md; the comparison is in the task notes
- [ ] #4 The record and the comparator are unchanged on both subjects; CHANGELOG line under Unreleased (a contract change if unknown_ids is dropped)
<!-- AC:END -->
