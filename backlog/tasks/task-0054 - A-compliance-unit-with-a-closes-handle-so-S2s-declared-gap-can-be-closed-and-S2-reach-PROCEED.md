---
id: TASK-0054
title: >-
  A compliance unit with a closes handle, so S2's declared gap can be closed and
  S2 reach PROCEED
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:50:00Z'
updated_date: '2026-11-03T23:26:00Z'
labels:
  - capture
  - register
milestone: m-5
dependencies:
  - TASK-0037
references:
  - backlog/docs/doc-0009
priority: high
type: feature
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0037 (#82): CargoQuote's open decision OD-1 names compliance as the declared gap's owner, and the example register has no compliance unit, so decision-0002 point 3 refuses every close and real S2 cannot reach PROCEED; doc-0009's milestone measure (S2 BLOCKED to PROCEED by command) needs it. Register side: an organisation node for compliance (stand-in, synthetic), approved under a decision record, and an issued handle with roles closes (and approves) in people/handles.toml (ieam-register decision 0009). knowgov side: re-vendor at the tag, map OD-1's owner to that unit, and extend tools/check_review_walkthrough.py to run real S2 from BLOCKED to PROCEED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ieam-register gains an approved compliance organisation node and an issued closes handle in its unit, under a decision record the maintainer approves
- [x] #2 knowgov re-vendors at that tag; OD-1's owner resolves to the unit
- [x] #3 check_review_walkthrough.py runs real S2 from BLOCKED (exit 1) through capture and the owner's close to PROCEED (exit 0), on rdflib and on Neo4j in CI
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Vendor ieam-register v0.2.6 (decision 0011: ORG-0004 Compliance (stand-in), employee-4 with closes). 2. OD-1's owner 'compliance' resolves to ORG-0004 by review.gap_owner's name match; tests/test_review.py holds it and keeps the unknown-owner refusal. 3. tools/check_review_walkthrough.py: real S2 BLOCKED -> employee-3's close refused -> capture and rulings, still BLOCKED on the declared gap -> employee-4 closes -> PROCEED; plus a close-first instance showing the key absent, still BLOCKED. 4. Run on rdflib and Neo4j.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Register v0.2.6 carries decision 0011: ORG-0004 Compliance (stand-in), approved; employee-4 in ORG-0004 with gives, approves, closes. OD-1's 'compliance' resolves to ORG-0004 through review.gap_owner's name match, no code change. Walkthrough run green locally on KG_STORE=rdflib and on Neo4j 5.26; CI runs it in harness.yml (rdflib) and the stack job (Neo4j).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Re-vendored the register at v0.2.6 (decision 0011). OD-1's owner resolves to ORG-0004; tests/test_review.py holds employee-3 refused, employee-4 closing, and an owner the register lacks still refused. tools/check_review_walkthrough.py now takes real S2 from BLOCKED (exit 1) through employee-3's refused close, capture and rulings (still BLOCKED on the declared gap) to employee-4's close and PROCEED (exit 0, --fail-on major), and shows on a fresh instance that a close alone leaves the key absent, still BLOCKED (decision-0002). Green on rdflib and Neo4j locally.
<!-- SECTION:FINAL_SUMMARY:END -->
