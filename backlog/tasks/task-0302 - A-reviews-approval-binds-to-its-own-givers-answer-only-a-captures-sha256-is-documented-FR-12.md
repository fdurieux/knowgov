---
id: TASK-0302
title: >-
  A review's approval binds to its own giver's answer only; a capture's sha256
  is documented (FR-12)
status: To Do
assignee: []
created_date: '2026-11-09T21:25:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/docs/doc-0037
  - backlog/decisions/decision-0019
priority: high
ordinal: 295000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the functional review of the 0.9.0 release candidate, group C at main f194aac (C2-1), recorded in doc-0037 §3.2. Fix-only, behind an unchanged contract. It breaks FR-12's binding claim, so the coordinator pulls it before the 0.9.0 cut.

`harness/review.py` `bind()`: when the named assertion id is gone, exactly one statement with the same key, value and sha256 wins ("repaired"). For a captured answer, sha256 is the empty-text digest e3b0c442…, so binding is by key and value only.

Repro:
1. employee-1 answers response|hold_presence; employee-2 approves A:cap:2026-11-05-ORG-0002-employee-1:1@capture.
2. Delete that capture file.
3. employee-3 ingests the same value.
4. The gate reads the key approved, with no act finding.

The self-review rule still holds: the reviewer as the new giver is refused.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A repair re-binds only to a statement from the same capture giver (the same capture stem); any other candidate leaves the approval unbound, with a finding that names the vanished id.
- [ ] #2 The repro is a test, and so is the reverse (the same giver's re-ingested answer still repairs).
- [ ] #3 The docs state that a captured answer's sha256 is the digest of empty text, and that binding is by giver, key and value.
- [ ] #4 The record does not move; a CHANGELOG line under the leading Unreleased.
<!-- AC:END -->
