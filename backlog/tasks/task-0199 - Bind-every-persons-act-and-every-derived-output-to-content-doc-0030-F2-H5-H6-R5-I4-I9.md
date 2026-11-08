---
id: TASK-0199
title: >-
  Bind every person's act and every derived output to content (doc-0030 F2: H5,
  H6, R5, I4, I9)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T09:11:00Z'
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
- [x] #1 A ruling records its statement's value and fragment digest; a ruling whose statement has changed is skipped and listed in the gate report
- [x] #2 The trace ledger records each used statement's value or Version digest; trace check reports suspect when it differs or no longer resolves (the P2 316.00 to 341.00 edit reads suspect)
- [x] #3 Suspect is computed from the used statements' statuses by one port read the gate, the MCP server and trace share
- [x] #4 authored, approval, review and a stage-2 reverify require `at` and an attester, refused otherwise by check_subject; a ruling other than rejected or referred on an inferred, assumed or hypothesised statement is refused
- [x] #5 CHANGELOG.md has the line under Unreleased's contract heading, with the read rule for existing review files and ledgers
- [x] #6 The scored record (S1 to S7), the deterministic run and the comparator stay equal
- [x] #7 A re-run neither loses nor misplaces an act (doc-0032 §6): an act (ruling, review approval, gap close, attestation) whose statement is unchanged re-applies after a reload or a re-extraction; one whose statement changed is not applied and is a gate finding naming the act, its author's handle, the change (old value and digest to new) and the owning unit's route from register_map.toml; never silent, never stderr only
- [x] #8 Statements pair by content across two extractions of one document at two commits (doc-0032 §6): a test with a reordered table or a renumbered fragment shows that no act moves onto another statement
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Two PRs, each green alone (coordinator's SHAPE).
PR A, claude/task-0199-f2 (AC 1, 4, 7, 8; 5 and 6 for its part): review.bind binds a ruling to its key, value and content digest (store fragments' sha256s); capture.py review writes them; a load re-pairs by content, sets aside an act that no longer binds and records it (port write record_act_finding, read act_findings, both adapters); the gate reports kind act (major changed/gone/ambiguous; info refused or read-rule unbound) with owner and route; stage 2 rechecks rulings; I4 refused in review.check; I9 load.attestation and check_subject's attestation rule; cadence.lapse's empty min an assertion. tools/check_act_binding.py.
PR B, claude/task-0199-f2-trace (AC 2, 3; 5 and 6 for its part): the ledger's used list (id, key, value, sha256), kept on the Derived node; store.suspicion the one rule for suspect_derived, all_derived and derived_outputs on both adapters, no stored flag read; trace.check reads it; the read rule an info unbound finding. tools/check_ledger_binding.py.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Shipped in two PRs: #342 (ruling side, AC 1, 4, 7, 8) and #343 (ledger and suspect side, AC 2, 3), both merged on whole green; #343 carried main after #342 and was checked combined (run_tests pins/no-yaml/J-F, both new tools on rdflib and Neo4j 5.26, the comparator on S1-S7 and J-F, round trips both chains on both subjects, trace walkthrough, gate_after_change). Severity of an act finding: major for changed, gone or ambiguous; info for a file refused whole or read under the read rule. review.content_digest is store.content_digest. Not built, put to the maintainer by the coordinator: binding [verification] authored/approval attestations to document versions (decision-0009's choice; it would change what the scored record reads). Follow-up candidate, not opened: the page's (suspect) annotation still reads the stored flag.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A person's act and a derived output now bind to content (doc-0030 F2: H5, H6, R5, I4, I9; doc-0032 §6 items 6-8). A ruling records its statement's key, value and content digest, a close its gap's text digest; every load binds each act by content, so a reordered table or renumbered answers move none, and one whose statement changed or vanished is not applied but reported as an act finding (major; owner and route named), never stderr only; stage 2 rebinds rulings. A ruling may not approve an inferred, assumed or hypothesised statement. Attestations need their own at and an attester (check_subject refuses; the load applies none). trace's ledger records each used statement's value and digest, and store.suspicion is the one rule the gate, the MCP reader and trace share, so an edit and reload under the same id reads suspect. Read rules accept review files and ledgers from before 0.9.0, at info. Contract change gathered for 0.9.0 in CHANGELOG. Verified by tools/check_act_binding.py and tools/check_ledger_binding.py (each failing on main, green on rdflib and Neo4j), the suites, and the record unchanged. Open: attestation binding to document versions, with the maintainer.
<!-- SECTION:FINAL_SUMMARY:END -->
