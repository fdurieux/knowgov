---
id: TASK-0009
title: Gap-driven questionnaire per owner and the capture fields
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-01T14:30:00Z'
updated_date: '2026-11-02T22:54:00Z'
labels:
  - instance
  - capture
milestone: m-2
dependencies:
  - TASK-0002
  - TASK-0006
priority: medium
type: feature
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Knowledge that lives only in people shows up as unknown or a declared gap and blocks the gate; there is no capture path. The brief (doc-0001, section 0, tacit knowledge) names three cheap routes: a static questionnaire generated from the gate's gap list per owner; required fields in the register (rationale, exception reason, decision record, and a source-of-this-knowledge person-and-date field); review-driven elicitation on review_due. A model may propose, as inferred and proposed, and never promote; the transcript is never the record. The two metamodel additions (a person as a source kind, an elicited evidence class with a shorter review period) are ieam-register's decision, referenced here, not made here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 From a loaded subject, a command writes one questionnaire per owner listing every absent key, declared gap and unverified assertion on what that owner owns, with the denominator
- [ ] #2 An answered questionnaire is ingested as authored assertions attributed to the person and dated, at status proposed, or as a declared gap when the answer is 'nobody knows'
- [ ] #3 No path exists by which a model's output reaches a status above proposed
- [ ] #4 The register's required capture fields are documented with a pointer to the ieam-register decision that adds them
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. ieam-register decision 0008 (its #10, proposed, the maintainer approves by the merge): types.toml [elicited] from/on/record with an opaque-handle pattern, lifecycle.toml [review.evidence] elicited = 6 months, check_register enforcing both.
2. harness/capture.py questionnaire: load as the gate command does, resolve, one TOML questionnaire per owner (the register owners of the nodes a key's map row names; unassigned otherwise) listing absent, declared-gap and below-verified keys with what the store holds, keys_owned as the denominator.
3. harness/capture.py ingest: check an answered questionnaire (a handle per decision 0008, a date not in the future, one of answer or nobody_knows per item) and write it normalised into the subject's captures/ ([capture] dir), never overwriting.
4. load_captures in every load (run.py, gate_cli): an answer -> an assertion basis elicited, status proposed, attributed to person:<handle>, the activity dated; nobody_knows -> a declared gap naming the handle and date. Store port ensure_person in both adapters.
5. AC 3: the adapters verify only extracted and authored assertions; a test holds both adapters to that, and harness.yml re-runs the verifications over a store with captures and the inferred assertion and requires both at proposed.
6. instance/README.md: the capture path in the adopter register, and the register's capture fields with the pointer to decision 0008.
<!-- SECTION:PLAN:END -->
