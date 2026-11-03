---
id: TASK-0037
title: >-
  A review record for captured statements: rulings, a declared gap closed by its
  owner, and the six-month lapse
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T22:33:00Z'
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
- [x] #1 A review file, append-only beside the captures, is checked on load: a reviewer handle that is also the capture's `from` is refused, as is a ruling on an assertion id the store does not hold
- [x] #2 An approved elicited statement loads as approved with an approval {by, on, record}; a rejected statement, elicited or extracted, leaves the live set the gate reads
- [x] #3 A declared gap is closed only by a ruling whose record names the gap's owner; any other reviewer's close is refused
- [x] #4 After `until` an approval lapses and the statement reads proposed again
- [ ] #5 CI shows S2' (REQ-06 not declared open) going BLOCKED, then QUALIFIED after capture, then PROCEED after a review, by gate_cli exit codes, on both store adapters
- [x] #6 instance/README.md "Capturing what people know" describes the review step in the adopter register
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Governed by decision-0002 and ieam-register decision 0009 (vendored v0.2.4, people/handles.toml).
1. harness/review.py: the pure checks. A review file ([review] by, on, record, scenario; [[ruling]] assertion, outcome approved|rejected|referred, note; [[closes]] gap) is refused whole, each reason naming its rule: by not issued, withdrawn or issued after on; on in the future; a ruling on an id the store does not hold; an elicited ruling by its own giver or without approves; a ruling on a document's or a disputed statement without closes; a unit not owning the key (register_map); a declared-gap close without closes or by a unit other than the owner the declaration names (or, if none, the key's owners); a dispute half-settled (a disputed statement of a ruled key left unruled) or settled on two values.
2. Store port, both adapters, basis-agnostic: assertion_brief, apply_ruling (approved -> Approval {by, on, record, until} and status approved; rejected -> status rejected, node kept), close_declared_gap (kind closed, history kept), settle_conflicts (kind settled), declared_gap.
3. load.py load_reviews after run_all in gate_cli._load and run.py: files under captures/reviews/, for their scenario; refused files skipped with the reasons on stderr; an elicited approval lapses six months after the capture's on (KG_TODAY for a fixed date).
4. capture.py review FILE: checks against the loaded scenario and writes the file, append-only, into captures/reviews/.
5. Tests (stdlib) and CI: S2' BLOCKED exit 1 -> capture QUALIFIED exit 0 -> reviews PROCEED exit 0 with --fail-on major, rdflib in harness.yml and Neo4j in the stack job; S4 one side approved refused, settled by a ruling; lapse by KG_TODAY.
6. instance/README.md: the review step in the adopter register.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Governed by decision-0002 (proposed 2026-11-03): who may approve, close a declared gap or settle a dispute, and what the tool refuses; and by ieam-register decision 0009 (proposed, its #12): issued handles with roles gives, approves, closes.

Built as planned. harness/review.py holds decision-0002's rules; the adapters gained five basis-agnostic port operations (assertion_brief, declared_gap, apply_ruling, close_declared_gap, settle_conflicts); load_reviews runs after the rules in gate_cli._load and run.py; capture.py review checks and writes. Choices: a review is refused whole; it applies to the scenario its [review] names; ruling on a document's statement (approve or reject) needs closes, an elicited one approves; a rejected statement takes status rejected (out of LIVE, node kept); a closed gap takes kind closed, a settled conflict kind settled; the lapse is computed from the capture's on, never trusted from the file; a review written by hand into captures/reviews/ is re-checked on every load, skipped with its reasons on stderr.
Verified: tests/run_tests.py 136/136; tools/check_review_walkthrough.py passes on rdflib and on Neo4j 5.26 (community tarball, Java 21): S2' BLOCKED exit 1 -> capture QUALIFIED exit 0 (major 1) -> reviews PROCEED exit 0 with --fail-on major; KG_TODAY=2027-05-03 QUALIFIED; S4 half-settled refused, settled whole PROCEED with conflicts 0. The deterministic comparator stays at 0 differing leaves over S1-S7 on both stores.
Finding: S2 itself cannot reach PROCEED on the example register. OD-1 names compliance as its owner, and the register has no compliance unit, so decision-0002 point 3 refuses every close (the walkthrough asserts the refusal). doc-0009's S2 measure needs a compliance unit and a closes handle in ieam-register, or a declaration naming an existing unit.
Order: decision-0002 put task-0038 first; this task was started on the maintainer's request before it. Until 0038, a person contradicting a document is visible to the reviewer only in the bundle, not as a conflict gap.
Not in scope, left for its own change: capture ingest still checks from against the pattern only, not the issued list (decision-0002 consequence 3); the existing capture CI step answers as steward-1, which is not issued.
<!-- SECTION:NOTES:END -->
