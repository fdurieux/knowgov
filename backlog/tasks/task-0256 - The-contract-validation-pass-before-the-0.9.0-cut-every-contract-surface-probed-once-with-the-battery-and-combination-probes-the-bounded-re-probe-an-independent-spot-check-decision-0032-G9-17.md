---
id: TASK-0256
title: >-
  The contract validation pass before the 0.9.0 cut: every contract surface
  probed once with the battery and combination probes, the bounded re-probe, an
  independent spot check (decision-0032, G9-17)
status: Done
assignee: []
created_date: '2026-11-09T08:55:00Z'
updated_date: '2026-11-09T22:55:00Z'
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
- [x] #1 A surface list with its denominator is written, and every surface is ticked as probed with the battery and the combination probes that apply to it
- [x] #2 Every finding is reported with a reproduction and classified contract-bearing or fix-only; each contract-bearing finding has a task, is fixed, and its surfaces are re-probed with the same battery
- [x] #3 An independent spot check, by a reviewer who ran no part of the pass, probes a random sample of surfaces and its result is recorded
- [x] #4 The pass's report is filed as a backlog doc with the list, the findings, the re-probe and the spot check; fix-only findings are tasked for 0.9.x
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

Group 2's re-probe (point 4) at 9861953: 7 of 7 surfaces re-probed, 7 fixed, no regression, Neo4j 5.26 included (SNAP-11 and a 90 s race clean). N1, held_keys' gate null on an empty store, contradicts choice 9(a) as accepted: task-0292, contract-bearing, completing task-0283. N2 goes to task-0263, N3 and N4 to task-0293, and F10 is confirmed on task-0265. Every re-probe and the spot check are in.

decision-0034 accepted on the maintainer's word, "N7, D1, D3 as advised": choice 1 (the settings table's reach) is task-0294, choice 2 (scenario ids) task-0295, choice 3 (the gate_verdict key pattern) task-0296. Each holds the cut.

Re-check of the second-round fixes, complete (decision-0032 point 4):
- every fix holds with no regression: task-0264, 0267, 0286, 0287, 0288, 0289, 0292, 0294, 0295 and 0296 (groups 1, 2 and 3, and the spot check, at 0682e16, 95af205, c94dfa5 and 946c72e).
- One new contract-bearing finding, K1 (other control and format characters pass the key rule): decision-0034 Amendment A1, accepted as 'K1 (a) as advised', built as task-0297, which holds the cut.
- Fix-only findings are tasked as task-0298 (settings parser and scan reach), task-0299 (the `--baseline record` path) and task-0300 (CI paths with a leading dash, non-UTF-8 names, silent linters), with notes on task-0263 and task-0265.
- The pass report, doc-0036, is filed after task-0297's re-check.

The spot check's re-check of task-0297 at f194aac: fixed, exhaustive over every code point in Python and in Node v22 (ICU 17.0), with and without u, 0 mismatches, no regression. It found N3 (the NFC and NFD spellings of a name are different keys), put to the maintainer. After 'In Belgium we have many French names with accents', the advice was re-evaluated to (a). Accepted as decision-0034 Amendment A2 ('N3 (a) as advised'), built as task-0301, which holds the cut. N4 (unassigned code points and noncharacters accepted) is a note; tests/test_key_rule.py regenerates against the running interpreter.

Re-check of task-0301 (#446, ac64d59) by the spot check: N3 fixed, no regression; the record holds. Four fix-only findings, B1 to B4, are task-0309; B1 fails open, so it is pulled ahead of the cut with task-0308 (task-0302's re-check R1 to R3). No contract-bearing finding is open, so G9-17 is met (decision-0032 point 3).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The contract validation pass is done (decision-0032). Round 1 by three fresh groups found 16 contract-bearing findings over 105 surfaces; six documented-promise fixes (task-0257 to task-0262), decision-0033's nine choices (task-0275 to task-0283) and the follow-ups from the re-probe, the spot check and the re-checks (task-0286 to task-0289, task-0292, task-0294 to task-0297, task-0301) are built, merged on whole green and re-checked by the session that found each, without regression. Fix-only findings are tasked: task-0263 to task-0272 and task-0290 to task-0300 for 0.9.x, and task-0308 and task-0309 pulled ahead of the cut. Report: doc-0036; G9-17 met in doc-0028. Not probed, by each session's account: doc-0036 §7.
<!-- SECTION:FINAL_SUMMARY:END -->
