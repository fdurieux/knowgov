---
id: TASK-0009
title: Gap-driven questionnaire per owner and the capture fields
status: To Do
assignee: []
created_date: '2026-11-01T14:30:00Z'
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
