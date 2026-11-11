---
id: TASK-0327
title: >-
  register_impact attributes a suspect output by used_changed as well (doc-0038
  §4 P4)
status: Done
assignee: []
created_date: '2026-11-11T13:34:00Z'
updated_date: '2026-11-11T15:47:00Z'
labels:
  - impact
  - 0.9.0
dependencies: []
priority: high
ordinal: 319000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled before the 0.9.0 cut under decision-0032 (fails open). Redo group B's N3 (doc-0038 §4 P4). register_impact.py (about line 339) attributes a suspect_derived finding to a key only where its related ids meet the key's stale statements. After an in-place document edit an output is suspect through used_changed, with no stale statement, so register_impact CAP-0002 gives P2|surcharge suspect [] while derived_outputs key=P2|surcharge and gate_verdict hold derived:code@c0ffee1:reference_impl.py suspect. proposal_impact's reused keys and step-grid cells inherit it. Fix: attribute by used_changed as well, so the tools answer alike.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 After an in-place edit on the example instance, register_impact on the key's node lists the suspect output, as derived_outputs and gate_verdict do; a test
- [x] #2 S6 stage 2's answers are unchanged; the record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built in #481 (session_01HTAA1UjvoTDDjusu1chtAs), merged in train #484 as a214137; recorded by the coordinator, the builder having no backlog CLI. register_impact.statement_keys and with_levels(keys, report, key_of), passed by mcp_server and the three proposal_impact sites; check_mcp_server holds the server to the same rule. Live repro on the example instance (gate --publish, trace register, edit, gate --publish, trace check): register_impact CAP-0002 lists the output suspect on P2|surcharge and P2|threshold, as derived_outputs and gate_verdict do; main's harness/ gives suspect []. Re-check sent to group B.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
register_impact, and the keys and step-grid cells proposal_impact reads, attribute a suspect derived output to a key by used_changed as well as by stale statements, so they answer as derived_outputs and gate_verdict do after an in-place edit. Test: test_p4_an_output_suspect_by_used_changed_is_attributed_to_its_key (fails on main), plus the live repro (AC1); S6 stage 2 unchanged, the record holds (AC2).
<!-- SECTION:FINAL_SUMMARY:END -->
