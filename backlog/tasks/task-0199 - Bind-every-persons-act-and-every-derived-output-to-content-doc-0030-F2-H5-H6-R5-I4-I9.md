---
id: TASK-0199
title: >-
  Bind every person's act and every derived output to content (doc-0030 F2: H5,
  H6, R5, I4, I9)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T07:39:00Z'
labels:
  - review
  - reviews
  - trace
  - contract
dependencies:
  - TASK-0193
priority: high
type: feature
ordinal: 199000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

H5 (high): a ruling binds to a positional assertion id with no value or digest (review.py:192-203), so after an edit the approval sits on the new value, and a vanished id refuses the whole review on stderr only. H6 (high): trace's ledger keeps ids only and a reload re-mints the same id for the new value (load.py:108, trace.py:259), so code built on the old value reads clean. R5: suspect is a stored flag for the gate and a status reading for trace. I4: a reviewer holding `closes` can approve a model's statement. I9: an undated attestation is dated by each load, so it never lapses, and the attester defaults to agent:maintainer. A contract change (the review file, the ledger), so it gathers for 0.9.0 with a read rule for files already written; doc-0028 G9-11.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A ruling records its statement's value and fragment digest; a ruling whose statement has changed is skipped and listed in the gate report
- [ ] #2 The trace ledger records each used statement's value or Version digest; trace check reports suspect when it differs or no longer resolves (the P2 316.00 to 341.00 edit reads suspect)
- [ ] #3 Suspect is computed from the used statements' statuses by one port read the gate, the MCP server and trace share
- [ ] #4 authored, approval, review and a stage-2 reverify require `at` and an attester, refused otherwise by check_subject; a ruling other than rejected or referred on an inferred, assumed or hypothesised statement is refused
- [ ] #5 CHANGELOG.md has the line under Unreleased's contract heading, with the read rule for existing review files and ledgers
- [ ] #6 The scored record (S1 to S7), the deterministic run and the comparator stay equal
- [ ] #7 A re-run neither loses nor misplaces an act (doc-0032 §6): an act (ruling, review approval, gap close, attestation) whose statement is unchanged re-applies after a reload or a re-extraction; one whose statement changed is not applied and is a gate finding naming the act, its author's handle, the change (old value and digest to new) and the owning unit's route from register_map.toml; never silent, never stderr only
- [ ] #8 Statements pair by content across two extractions of one document at two commits (doc-0032 §6): a test with a reordered table or a renumbered fragment shows that no act moves onto another statement
<!-- AC:END -->
