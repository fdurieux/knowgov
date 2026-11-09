---
id: TASK-0284
title: >-
  The register's own tools load per root, so two register roots in one process
  never share a module (architecture review C3, 0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T13:34:00Z'
labels:
  - register
  - correctness
dependencies: []
priority: low
ordinal: 277000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Four loaders import the register's own tools:
- `harness/register_impact.py` `load_tools`;
- `harness/proposal_impact.py` `check_module`;
- `demo/app/register_view.py` `_load_tools`;
- `tools/connector.py` `_register_tool`.

Three of them use bare `sys.modules` names (`register`, `impact`, `check_register`), and each root's `tools/` goes in at `sys.path[0]`. So `check_register`'s own `from register import …`, `from impact import …` and `from reconcile import …` bind to whichever root was loaded last, not to the root `check_module` was asked for.

Probe, verified by the coordinator on main `ada71ce`: load root A, load a copy B, then call `check_module(A)`. Its `ROOT` is B's, and so are `TAXONOMIES`, `kind_taxonomy`, `load_register`, `load_toml` and impact's `THREAD`, `WITHDRAWN` and `walk_children`.

No shipped path triggers it today:
- the MCP server reads `KG_REGISTER` only;
- the page loads one root;
- `evaluate_branch` loads the checkout, then the temporary merge base, then `check_module(tmp)`.

A multi-root reader would, as would a branch read in another order with differing tool code. The fix is fix-only: no schema, exit code, flag, setting or format changes, and the gate report's register identity (task-0237) stays equal.

Source: the architecture review, session_01HTAA1RxXzHVmn2MeDc34NM, 2026-11-09. C3's remainder (one `Register(root)` value, the six layout readers, the two SOURCE.md parsers) is task-0247's scoping.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each register root's tools load under module names private to that root (for example keyed by its resolved path), and no loader shares the bare names `register`, `impact`, `check_register` or `reconcile` across roots.
- [ ] #2 The review's probe is a test: after loading a root and a copy of it, `check_module(A)` resolves A's `ROOT` and A's `register`/`impact` objects. The test fails on main and passes with the fix.
- [ ] #3 All four loaders use the one mechanism. `check_proposal_branch`, `check_register_change`, the register view and the connector checks pass.
- [ ] #4 The record and the gate report's register identity are unchanged, and `tools/complexity.py --check` holds.
<!-- AC:END -->
