---
id: TASK-0256
title: >-
  The contract validation pass before the 0.9.0 cut: every contract surface
  probed once with the battery and combination probes, the bounded re-probe, an
  independent spot check (decision-0032, G9-17)
status: To Do
assignee: []
created_date: '2026-11-09T08:55:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
priority: high
ordinal: 250000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0032 (accepted 2026-11-09, the maintainer: "middle option, and yes, only contract-bearing findings hold the cut"). Surfaces (decision-0032 point 1): the 24 schemas, the CLIs and their flags and exit codes, the MCP reader's 17 tools and 2 prompts on both transports and eras, the runs server's 3 tools, the 20 KG_* settings, the page's 4 routes, instance/ci, the input formats, the store port's reads on both adapters, the image's name and tags. Battery (point 2): wrong type, missing, empty, boundary, non-finite, oversized, Unicode and path forms; combination probes over task classes, subjects (CargoQuote, J-F, minimal, an example instance with its own register), coverage rules and stores alone and racing. Each finding classified contract-bearing (holds the cut) or fix-only (0.9.x). Probers are sessions that did not build the code they probe. The SNAP-04 investigation is part of the store surface.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A surface list with its denominator is written, and every surface is ticked as probed with the battery and the combination probes that apply to it
- [ ] #2 Every finding is reported with a reproduction and classified contract-bearing or fix-only; each contract-bearing finding has a task, is fixed, and its surfaces are re-probed with the same battery
- [ ] #3 An independent spot check, by a reviewer who ran no part of the pass, probes a random sample of surfaces and its result is recorded
- [ ] #4 The pass's report is filed as a backlog doc with the list, the findings, the re-probe and the spot check; fix-only findings are tasked for 0.9.x
<!-- AC:END -->
