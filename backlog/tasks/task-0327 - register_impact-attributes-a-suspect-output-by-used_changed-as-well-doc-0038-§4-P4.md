---
id: TASK-0327
title: >-
  register_impact attributes a suspect output by used_changed as well (doc-0038
  §4 P4)
status: To Do
assignee: []
created_date: '2026-11-11T13:34:00Z'
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
- [ ] #1 After an in-place edit on the example instance, register_impact on the key's node lists the suspect output, as derived_outputs and gate_verdict do; a test
- [ ] #2 S6 stage 2's answers are unchanged; the record holds
<!-- AC:END -->
