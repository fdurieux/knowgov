---
id: TASK-0306
title: >-
  An execution verification holds only for the document Versions it was attested
  on (decision-0036)
status: To Do
assignee: []
created_date: '2026-11-09T21:32:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0036
  - backlog/decisions/decision-0019
  - backlog/docs/doc-0037
priority: high
ordinal: 299000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0036, accepted 2026-11-09 ("Agreed", doc-0037 §3.1). Found by the functional review, groups A (F1) and C (C2-2), at main f194aac, and confirmed by the coordinator.

`harness/load.py` `load_verifications` writes `verify_by_execution` (`outcome: pass`, `evidence_sha256` the reference code's digest) for every live statement whose (key, value) the pristine kit states. No suite runs. On an instance the pristine kit is the documents on disk, so an edited value inherits "verified by execution".

Repro, the example instance's S1 with P2's surcharge changed from 316.00 to 341.00 in decision_table.md:
- with the shipped `versions`: QUALIFIED, and P2|surcharge reads VERIFIED at 341;
- with `versions` removed: PROCEED.

`docs/guide.md:686` says "the oracle runs again on every load".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An execution verification is written only for a statement whose document Version digest the subject's execution attestation lists (decision-0019's `versions`, extended to the execution declaration); an unlisted Version is not verified by execution.
- [ ] #2 Every other verification kind written per load (review, wherever not yet version-bound) follows the same rule, or the task records why it already does.
- [ ] #3 Both repros are tests. The edited P2 falls below verified and is not approved, so the gate is not PROCEED on it; the pristine documents read as before.
- [ ] #4 The record does not move: the public subjects' attestations list their Versions where needed. Both comparators, the round trip and `check_mcp_server` hold.
- [ ] #5 `docs/guide.md` §9 and :686 say what an execution verification is (the subject's attested result, bound to the Versions it lists; no oracle runs at load), and a CHANGELOG line names it under Contract changes.
<!-- AC:END -->
