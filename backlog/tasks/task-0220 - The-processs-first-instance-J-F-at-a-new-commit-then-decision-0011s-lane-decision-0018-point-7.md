---
id: TASK-0220
title: >-
  The process's first instance: J-F at a new commit, then decision-0011's lane
  (decision-0018 point 7)
status: To Do
assignee: []
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-15T21:56:00Z'
labels:
  - process
  - reverse-engineering
  - jef
dependencies:
  - TASK-0214
  - TASK-0215
  - TASK-0216
  - TASK-0217
  - TASK-0218
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: task
ordinal: 220000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 7. The cheapest proof of repeatability is the same subject at a new commit with its oracle in hand. Steps 1 and 2 read J-F's code, which is private and must remain private (the maintainer): the run needs the commit to read and a private route to the code, and what it may publish (a new kit, findings, scores) is the maintainer's call before anything is written to a public repository. Then decision-0011's lane, once that record is approved. Waits on the maintainer for the J-F commit and the route, and on tasks 0214 to 0218 for the steps it runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The maintainer names the J-F commit, the route to its code and what may be published, recorded here before step 1 starts
- [ ] #2 The run follows task-0218's pre-registration and leaves its record with its instance, every step's record named
- [ ] #3 Nothing of J-F's private code reaches a public repository
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #1 recorded (the maintainer, 2026-11-15: "R7(b) option a; Q4-Q14 as recommended; go").

- Commit: 9b9cebc of the private J-F repository (its main on 2026-11-15).
- Route: hosted sessions on the maintainer's account with read access to that repository; the extraction is an assistant session under the organisation account on terms excluding training on inputs, recorded privately; knowgov runs from the maintainer's EC2 host on the 5.26 container, loopback only.
- Publication: nothing of J-F's code, kit or answers in a public repository; outcome lines and counts only, each approved by the maintainer before it is written.
- Where: a separate private instance repository beside J-F, never a folder inside J-F (J-F's own rules keep experiments/ and its gates untouched).

The maintainer redirects the first instance. It is not the data-load lane at a new commit but J-F's model lane: the training and inference program, co-written, its logic the co-author's, with code only and no record of its meaning. Run 01 extracts it in a full clean room (the frozen file alone). The co-author answers the modelling keys and the maintainer approves; for the architecture keys the roles swap. Step 8 runs on the lane's next version, which J-F holds unread until its own adjudication. The maintainer ruled that this run counts as that adjudication's evidence and decides none of its groups. Step 7 is off. A demonstration case for a lighthouse prospect, not the lighthouse (doc-0028). decision-0011's lane follows later, as before.
<!-- SECTION:NOTES:END -->
