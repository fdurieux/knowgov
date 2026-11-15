---
id: TASK-0057
title: Pre-register the outcome study on the lighthouse pilot's backlog
status: To Do
assignee: []
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-15T10:31:00Z'
labels:
  - lighthouse
  - evidence
milestone: m-8
dependencies:
  - TASK-0062
references:
  - >-
    https://github.com/fdurieux/pumllint/blob/main/docs/neo4j-governed-knowledge-evaluation.md
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: medium
type: spike
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The proof of concept supports the mechanism and leaves the outcome unproven (pumllint docs/neo4j-governed-knowledge-evaluation.md: "supported for the mechanism, unproven for the outcome"). doc-0012 §7: a null outcome turns the position from Visionary into a niche player with a strong method, and buyers and analysts ask for the outcome first. Pre-registering before the pilot starts is what makes its result citable, the way kg_experiment/PREREGISTRATION.md made the proof of concept citable. The study itself runs in S2; this task only fixes its design before any pilot data exists.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A pre-registration is committed before the pilot's first governed change: hypotheses, the governed and ungoverned arms, the measures (defect escape, rework, review time), the sample, the stopping rule and the analysis
- [ ] #2 Each measure states its source in the pilot's own systems, and what is kept private and what may be published
- [ ] #3 The expectations are stated so that each can fail, and a null result is named as an outcome the study reports
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-15, from the private fdurieux/knowgov-bench (its study record, package XR-11 "Close lighthouse readiness without changing frozen contracts", from a cross-repository roadmap of 2026-11-14 pinned at knowgov 538618f, recorded there by the maintainer's go of 2026-11-15). Nothing new is minted; XR-11 restates this task and its neighbours. Its acceptance criteria, verbatim:
1. "Existing task-0285 acceptance checks are walked from an empty instance; each third-party dependency is named rather than represented as complete."
2. "The task-0057 pilot-outcome template remains distinct from this synthetic experiment and is ready before any pilot's first governed change."
3. "Decision-0016 A1's 30-day soak and patch condition are evidenced; 1.0 means ready for lighthouse. New public contracts follow the accepted release policy."
Completion evidence, verbatim: "task-0285 record, onboarding replay, release checklist and known limits."
"This synthetic experiment" is knowgov-bench's study MSX-01, a synthetic benchmark kept in that private repository; nothing of it comes here. The release policy for criterion 3 is decision-0016 with decision-0041: contract changes after 0.9.x wait for 1.1.0.
<!-- SECTION:NOTES:END -->
