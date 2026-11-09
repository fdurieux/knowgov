---
id: TASK-0253
title: >-
  How knowgov's facts feed a team's prioritisation method and plan its
  refinement: the inputs recipe (WSJF, cost of delay, RICE) and refinement to
  the definition of ready (squad study, doc-0034)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T07:33:00Z'
updated_date: '2026-11-09T08:26:00Z'
labels:
  - docs
  - prioritisation
dependencies: []
priority: low
ordinal: 247000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0034 (the squad study, advice 3). knowgov supplies inputs to a prioritisation method a team already uses, and no score: time criticality (lapses before a date with --as-of; the existing products and journeys a change reaches), risk reduction and opportunity enablement (absent, declared-gap and disputed keys; required_not_reached enablers), a job-size proxy (new against reused elements, gaps, owners and handoffs per slice), dependencies (the realisers chain, node before link approval, both owners across domains). It supplies nothing on value, user reach, confidence in value or effort, and key levels are confidence in knowledge, not in value. A section in instance/README.md, in the adopter register, with the commands that produce each input on the example instance. Documentation only: a 0.9.x patch under decision-0016 point 2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 instance/README.md gains a section naming each input, the command or MCP tool that yields it, and what knowgov does not supply, in plain English
- [x] #2 tests/test_adopter_docs.py's flag and command checks hold the new section's commands to real options
- [x] #3 The section gains "Planning refinement": the two classes in order (design, then codegen), the table of key level to analysis work, owner and route, and how progress is tracked, in plain English; the task-0252 caveat is one sentence, dropped once task-0252 is on main
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-09 (coordinator): extended on the maintainer's word ("yes, extend task-0253, mint the view and the template") with refinement planning: getting slices to the definition of ready. Run the slices under --task design then --task codegen as of the refinement date; each key below the bar is one analysis item for its owner, typed by its level (absent: elicit, the owner's questionnaire; declared gap: the closer's decision; disputed: a ruling by a reviewer, not the author; invalidated: reconfirm; proposed: four-eyes review; validated below the bar: verify or approve; lapsed by the sprint's end: re-review, capture.py due; a step reading 0 of N: define the knowledge the slice needs; a coverage gap: the architecture owner models the missing link); progress tracked by re-running as of a date, --baseline and step_grid. Until task-0252 merges, the per-slice design reading counts the register map's keys, not design's own.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/README.md gains 'Feeding your prioritisation, and planning refinement' (adopter register). The inputs a team's own method (WSJF, cost of delay, RICE) takes, each with the command on the example instance: time criticality (lapsed findings by gate_cli --as-of, capture.py due --on; reach by the proposal report, the MCP register_impact, the register's tools/impact.py --from), risk (absent, declared-gap and disputed keys; the slice map's required_not_reached), a job-size proxy (per slice new against reused, gaps, owners, handoffs), dependencies (the realisers chain, node approval before link approval as the register's checker enforces, both owners across a cross-owner link); what it does not supply (value, reach, confidence in value, effort; levels are confidence in knowledge). 'Planning refinement': the slices read under --task design then codegen as of the refinement date; a table of key level to work, owner and route (absent questionnaire, declared gap closer, disputed reviewer-not-author, invalidated reconfirm, proposed four-eyes, validated-below-bar verify or approve, lapsed by sprint end capture.py due); a step reading 0 of N and a coverage gap from the slice map; progress by --as-of, -o and --baseline, and step_grid. The task-0252 caveat is one sentence, pointing to gate_cli --task design. Every command ran as written on a fresh example instance; tests/test_adopter_docs.py holds every flag and fenced command. CHANGELOG under Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
