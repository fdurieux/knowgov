---
id: TASK-0247
title: >-
  SOLID refactoring after 1.0: narrow store-consumer protocols, an explicit
  validated context in place of the import-time globals, MCP transport apart
  from its use cases, the three complexity hotspots (parked)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T13:35:00Z'
labels:
  - refactoring
  - architecture
milestone: m-4
dependencies: []
priority: low
ordinal: 241000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). Store declares 91 methods and consumers use small subsets; SUBJECT and TASKS are built at import and 48 modules import subject; harness/mcp_server.py (1,498 lines) carries tools, dispatch, both protocol eras and both transports; review.check, proposal_impact's main function and preload_check run at cognitive complexity 148, 127 and 111. None caused R1 to R4, and decision-0016 makes the contracts stable from 0.9.0, so the refactors wait until after 1.0 (doc-0033 advice 2); before then, only the refactor a fix needs (task-0242's validator). The store port's method set is a 1.0 contract and does not shrink: narrow protocols are views a consumer is held to, by an AST guard as the Cypher guard is; the context object respects decision-0013's process per other subject.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts chooses the order and the scope after 1.0
- [ ] #2 Each refactor keeps the comparator, the round trip and the adapter parity tests equal, with characterisation tests in front of each hotspot
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**2026-11-09: scoping from the architecture review** (session_01HTAA1RxXzHVmn2MeDc34NM, at main `ee84120`; report only). The order the review advises is C1, C2, C5, C3's remainder, C4(a), C4(b), C6, C7, C8. Timing stays after 1.0 (doc-0033). No candidate changes a schema, exit code, flag, setting, format or the store port's method set, under the caveats named below.

- **C1. One load pipeline.** The stage-1 order is written four times:
  - `run.deterministic`, run.py:71;
  - `gate_cli._load`, :713, called at 19 sites in 13 files;
  - `check_stage2_reload.load_fresh`, :50;
  - `check_claim_probe`, :83, which omits `load_inferred`.

  Stage 2 has its own copy at change.py:64. The fix: `load.load(st, scenario, kit, tag, note) -> record`. The record must stay equal.
- **C2. The gate as a library.** `evaluate`, :624, and its helpers live in `gate_cli`, with 16 importers. The `SUBJECT.id == subject` branches at :638 and :642 decide owners, closers and the profile. The gate's parameters are defined three times. The fix: `evaluate(store, subject, request) -> report` in a gate module, with a characterisation test first and the report byte-equal.
- **C5. One retrying read.** The retry on `StoreChanged` is written four times: `store.read`, :747; `mcp_server._with_store`, :631; `server._read`, :267; `gate_cli`, :559. `mcp_server.ReadOnlyStore` is redundant. `is_loopback` is written three times, and only the page's copy strips whitespace and ignores case. Small.
- **C3's remainder.** One `Register(root)` value: identity, nodes, organisation, handles, lifecycle and tools. It absorbs:
  - the six layout readers (capture.py:73,87,356; review.py:139,156; code_map.py:40; cadence.py:60-65; check_subject.py:106);
  - the three resolutions of the `KG_REGISTER` default;
  - the two `SOURCE.md` parsers.

  The loader fix itself is task-0284, in 0.9.x.
- **C4(a)** The compositions both adapters share: `suspect_derived` and `all_derived` are identical in both, `held` goes through `held_from`, and `by_id` is applied 14 and 13 times. The base `Store` implements them once.
- **C4(b)** The rdflib-specific lines are 95-445 only. Over them, a stdlib dict backend, test-only and never a `KG_STORE` value, replaces the partial fakes in 10 test modules.
- **C6. An explicit context.** The global `SUBJECT` loads at import (48 modules, 105 uses of `SUBJECT.id`). `KG_STORE` is read at 19 sites. Code writes `os.environ` before an import. There are 144 `sys.path` edits in 82 files and 127 subprocess calls in the tests. `demo/app/page_subject.py` is the precedent.
- **C7. Each use case declared once.** Argparse, the `TOOLS` table and the hand checks become one registry, with flags' spellings and inputSchemas unchanged (`test_docs_flags`).
- **C8. Hotspots.**
  - `review.py`: the clock, register reads, `bind`, and `check` at 148;
  - `proposal_impact`: its eight `# ----` sections are the split lines;
  - `preload_check` at 111.

  Characterisation tests come first, then the clock module.

Not a candidate: `harness/extract.py`'s kit wording (`_STEP_CANON`) is a product question about the mapper extension point.
<!-- SECTION:NOTES:END -->
