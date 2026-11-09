---
id: TASK-0303
title: >-
  code_path's ledger leg returns the assertion ids and keys, and the leg's
  suspect state (decision-0035 B1)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-09T21:29:00Z'
updated_date: '2026-11-09T22:04:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0035
  - backlog/docs/doc-0037
priority: high
ordinal: 296000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0035, accepted 2026-11-09 ("Option (A)", doc-0037 §3.4). Found by the functional review, group B, at main f194aac.

`code_path`'s ledger leg returns `entry.assertions` as a count (88) and `keys` as a count, though the ledger holds both the assertion ids and the keys. So "this generated file → its keys → key_nodes" breaks over MCP. `derived_outputs` cannot stand in, because a load wipes the store's registration (the trace walkthrough's step 4). The leg has no suspect state either, only drift.

Repro: `tools/check_trace_walkthrough.py $T/tw`, then `harness/upward.py code --instance $T/tw/inst --ledger $T/tw/ledger.json reference_impl.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `code_path`'s ledger leg returns the entry's assertion ids and its keys, sorted, and states whether the entry is suspect, drifted or current, as `trace check` reads it.
- [ ] #2 The code-path schema says so, and `check_mcp_server` holds the leg's ids and keys on the walkthrough's ledger.
- [ ] #3 From the returned keys, `key_nodes` reaches the register's nodes in a test: file → keys → nodes.
- [ ] #4 The record does not move, and a CHANGELOG line names it under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. upward._entry: assertions sorted; keys always present (trace.entry_keys: the registration's keys with those of the used records); state current|drift|missing by the file's digest, as trace check reads it; suspect as a leg.
2. suspect, choice (b) (coordinator, 2026-11-09): the MCP reader reads it on one read handle (Tools._ledger_suspect -> _store_read -> trace.ledger_suspicion, store.suspicion over the entry's own record); unchecked with the reason when the store holds another subject's scenario or none, a run is loading or the store cannot be opened; always unchecked from upward.py code, which opens no store. mcp_server.READS gains assertion_brief.
3. code-path.schema.json requires keys, state and suspect; check_mcp_server (check_ledger_leg) and check_trace_walkthrough (check_code_path) hold the leg on the walkthrough's ledger.
4. tests/test_traceability_answers.py: ids and keys sorted, the three states, the schema, the suspect leg against trace check's finding, file -> keys -> key_nodes -> register nodes.
5. Wording: files, and the store for the ledger leg's suspect when it holds the subject (tool description, instructions, FILE_TOOLS note, docstrings, instance/README.md); CHANGELOG Contract changes line; the record held by the comparators, round trips and check_mcp_server.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Correction to the finding, at main f194aac: the leg already returned entry.assertions as a list of ids, not a count, but unsorted, and keys was absent for an entry registered without --keys/--cited (its keys only in the used records), which is what broke file -> keys -> key_nodes. The fix is sorted ids, keys always present, state, and a suspect leg.

Choice (b) for suspect, confirmed by the coordinator: it delivers decision-0035's 'the leg's suspect state' within the tool's read-or-unchecked convention, reading the store only through the MCP reader's read handle when it holds the subject, so the CLI stays files-only. (a), unchecked everywhere, would have left the leg without the suspect state the decision names; (c), opening a store from upward.py, would have made a files-only command store-backed. It is implementation within the accepted decision, so it needs no new word from the maintainer.

Verified: the MCP leg's suspect equals trace check's stage-2 report on the walkthrough (reference_impl.py and hand/tariff_rules.py suspect, hand/Screening.java not); check_mcp_server S1 reads 88 statement ids, 36 keys, current, suspect False.
<!-- SECTION:NOTES:END -->
