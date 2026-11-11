---
id: TASK-0337
title: Document what an execution verification's at means (decision-0039 §3.4)
status: To Do
assignee: []
created_date: '2026-11-11T22:53:00Z'
labels:
  - docs
  - 0.9.0
dependencies: []
priority: high
ordinal: 329000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.4 (b), doc-0038 §3.4, A-N3. load_verifications stamps an execution verification with the load's clock. State it where at is read: docs/guide.md (the verification section), the three_valued_answer, held_keys and document_statements tool descriptions where they show at, and the release's Known limits draft (doc-0038 §6). The text: at is when the load recorded the attestation; the run is identified by its digests (decision-0038 N-b: the document Versions, implementation and suite), not by a date. No code change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The guide and the tool descriptions say at is the load's time and name the digests as the run's identity; tests/test_docs_* hold
<!-- AC:END -->
