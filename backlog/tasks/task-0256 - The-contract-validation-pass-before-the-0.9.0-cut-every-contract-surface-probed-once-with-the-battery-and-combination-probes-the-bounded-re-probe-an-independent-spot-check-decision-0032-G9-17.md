---
id: TASK-0256
title: >-
  The contract validation pass before the 0.9.0 cut: every contract surface
  probed once with the battery and combination probes, the bounded re-probe, an
  independent spot check (decision-0032, G9-17)
status: In Progress
assignee: []
created_date: '2026-11-09T08:55:00Z'
updated_date: '2026-11-09T15:38:00Z'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**2026-11-09, first pass done.** All three read-only groups probed `main` at `2a8bbeb`, with `KG_CLOCK` pinned and no model calls. Each prober was a fresh session.

| Group | Session | Surfaces | Contract-bearing | Fix-only |
|---|---|---|---|---|
| 1, command lines and configuration | `session_01HTAA1RC6Yp5MDx977euXkS` | 41 of 41 | C1 to C8 | F1 to F20 |
| 2, the servers | `session_01HTAA1RS8eDPksPaVa9ZdWe` | 27 of 27 | F1 to F4, and F5 if fixed by meaning | F6 to F12 |
| 3, shapes and semantics | `session_01HTAA1SgVd34dfq1MYU7WzS` | 37 of 39, plus 2 partial on Neo4j | CB1 to CB6 | F1 to F13 |

There are 16 distinct contract-bearing findings. The groups reported 19, but three were found twice:
- group 1 C1 and group 2 F3;
- group 1 C2 and group 3 CB4;
- group 2 F1 and group 3 CB3.

The coordinator checked these on `main`: group 1's C1, C2, C5 and C6; group 2's F1, F3 and F5; and group 3's CB1, CB2 and CB3.

**Where the findings went:**
- Six keep a documented promise. They are tasked as task-0257 to task-0262 and hold the cut.
- Ten choose contract content. They are put to the maintainer as decision-0033's nine choices.
- The fix-only findings are tasked for 0.9.x as task-0263 to task-0272.

**The settings denominator.** decision-0032 point 1 counted 20 settings, but the two contract files name 75; decision-0033 choice 1 settles which of them are contracts. The probers covered the twenty, plus `KG_STORE`, `KG_RDFLIB_FILE`, `KG_RDFLIB_LOCK_TIMEOUT` and `KG_STORE_READ_ATTEMPTS` (group 1), and the MCP and page settings (group 2).

**Not probed:**
- Neo4j under racing writers, left to SNAP-04;
- the Node linters, which are not installed;
- `action.yml` and the GitLab include, which were read but not run;
- the arms, which are off by rule;
- the runs-server outputs live.

Each prober keeps its scratchpad reproductions for the bounded re-probe. The prober sessions stay available, and the spot check goes to a fresh session.

**2026-11-09, decision-0033 accepted** ("decision-0033 all as advised"). Its nine builds are task-0275 to task-0283, and each holds the cut beside task-0257 to task-0262. SNAP-04's fix is task-0274 (decision-0014 A1, accepted; #415). It is fix-only.

**2026-11-09 afternoon.** decision-0033's builds and the documented-promise fixes are landing: #411, #412, #416, #421, #423 and train #426. task-0276 is closed: AC #4 is proven by #421's green run. Open: task-0275 (#418, rows confirmed), task-0281 (#422), task-0278 and task-0279. Then the bounded re-probe and the spot check. The architecture review's C3 is task-0284, fix-only for 0.9.x; its C1–C8 scoping is in task-0247's notes.

Bounded re-probe and independent spot check at main 9861953 (2026-11-09, coordinator):
- Group 1: 10 of 10 surfaces re-probed, no regression. Contract-bearing, holding the cut: task-0286 (--baseline with a deterministic.json), task-0287 (KG_CLOCK's value domain), task-0288 (the cadence.register_root readers under choice 5). N7, settings read by code with no table row, goes to the maintainer.
- Group 3: 8 of 8 re-probed, 7 fixed, no regression. Its 3(a) is task-0286's gap, plus the D6_gate shape bypass.
- Spot check (point 5): 8 of 8 surfaces, rdflib only.
  - SC-1, subject_check's confinement bypassed through the register map, is fix-only but breaks H7: task-0289, before the cut.
  - GL-1 and GL-2 are task-0267's round-1 finding, independently confirmed; GL-1 fails open on non-ASCII paths. task-0267 is pulled forward before the cut, as is task-0264, whose N4 lets a blank token pass the wide-bind check.
  - D1 (scenario ids) and D3 (gate_verdict keys pattern) go to the maintainer. D2 (KG_ANNOTATE values) is task-0267 AC #2.
  - The rest are fix-only: task-0290 (hooks N12, N13), task-0291 (run folders read defensively, run_status's next), and notes on task-0263, 0265, 0266 and 0269.
- Group 2's re-probe is pending.
<!-- SECTION:NOTES:END -->
