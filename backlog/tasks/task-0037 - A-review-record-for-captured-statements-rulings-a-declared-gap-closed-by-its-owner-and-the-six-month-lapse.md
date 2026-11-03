---
id: TASK-0037
title: >-
  A review record for captured statements: rulings, a declared gap closed by its
  owner, and the six-month lapse
status: To Do
assignee: []
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T21:43:00Z'
labels:
  - capture
milestone: m-2
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: medium
type: feature
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 (the John Doe walkthrough) found that capture as built moves a key and never the verdict past QUALIFIED: no tool records the review a person gives an elicited statement, so PROCEED is unreachable through capture. Worse, a declared gap (S2, REQ-06 NOT YET SPECIFIED) outranks every assertion, and a dispute (S4) stays disputed beside a fifth, proposed statement; both end only when someone with authority rules. A simulated review in doc-0007 §3.1 reached PROCEED only when the reviewer approved the elicited statements and also rejected the documents' contrary ones; approving the wrong documented list also reached PROCEED, on knowledge that contradicts itself. doc-0007 §7 sketches the record (a review file beside the captures, append-only, `by` never equal to `from`, rulings approved/rejected/referred, a `closes` entry for a declared gap by its named owner, `until` six months after the capture per ieam-register decision 0008).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A review file, append-only beside the captures, is checked on load: a reviewer handle that is also the capture's `from` is refused, as is a ruling on an assertion id the store does not hold
- [ ] #2 An approved elicited statement loads as approved with an approval {by, on, record}; a rejected statement, elicited or extracted, leaves the live set the gate reads
- [ ] #3 A declared gap is closed only by a ruling whose record names the gap's owner; any other reviewer's close is refused
- [ ] #4 After `until` an approval lapses and the statement reads proposed again
- [ ] #5 CI shows S2' (REQ-06 not declared open) going BLOCKED, then QUALIFIED after capture, then PROCEED after a review, by gate_cli exit codes, on both store adapters
- [ ] #6 instance/README.md "Capturing what people know" describes the review step in the adopter register
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Governed by decision-0002 (proposed 2026-11-03): who may approve, close a declared gap or settle a dispute, and what the tool refuses; and by ieam-register decision 0009 (proposed, its #12): issued handles with roles gives, approves, closes.
<!-- SECTION:NOTES:END -->
