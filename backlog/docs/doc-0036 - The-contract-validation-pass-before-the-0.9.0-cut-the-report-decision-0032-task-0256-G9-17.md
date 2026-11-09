---
id: doc-0036
title: >-
  The contract validation pass before the 0.9.0 cut: the report (decision-0032,
  task-0256, G9-17)
type: other
created_date: '2026-11-09T21:24:00Z'
updated_date: '2026-11-09T21:24:00Z'
---
# The contract validation pass before the 0.9.0 cut: the report (decision-0032, task-0256, G9-17)

**Status:** filed 2026-11-09 by the coordinator. The probers' and the spot checker's reports are quoted, not re-run; each is named by its session.

## Verdict

Every contract-bearing finding but one is fixed on `main` at `f194aac`, and its surfaces were re-probed:
- by the round-1 probers in the bounded re-probe at `9861953`;
- again after the second round of fixes (§5).

The independent spot check found three choices for the maintainer, all accepted as decision-0034 and built. Its last re-check found N3 (NFC and NFD keys), accepted as decision-0034 A2 and building as task-0301: G9-17 is met when task-0301 is merged and re-checked, which this report records in an appendix. It also found one confinement bypass, task-0289, which is fixed. No fix regressed a surface. Fix-only findings are tasked for 0.9.x (§6).

## 1. The surfaces and their denominator

The surfaces are those of decision-0032 point 1:
- the 24 schemas;
- the CLIs, with their flags and exit codes;
- the MCP reader's 17 tools and 2 prompts, on both transports and both protocol eras;
- the runs server's 3 tools;
- the `KG_*` settings;
- the page's 4 routes;
- `instance/ci`;
- the input formats;
- the store port's reads, on both adapters;
- the image's name and tags.

Round 1, at `main` `2a8bbeb`, ran three read-only groups. None of them built the code it probed.

| Group | Session | Surfaces | Probed |
|---|---|--:|--:|
| 1, command lines and configuration | `session_01HTAA1RC6Yp5MDx977euXkS` | 41 | 41 |
| 2, the servers | `session_01HTAA1RS8eDPksPaVa9ZdWe` | 27 | 27 |
| 3, shapes and semantics | `session_01HTAA1SgVd34dfq1MYU7WzS` | 39 | 39 |
| **all** | | **107** | **107** |

Each surface got the battery (point 2): wrong type, missing, empty, boundary, non-finite, oversized, Unicode and path forms. Each also got the combination probes that apply to it:
- task class by tool;
- subject by tool, across CargoQuote, J-F, minimal and the example instance with its own register;
- coverage rule by reader;
- each store alone and racing.

Neo4j 5.26 was run by group 2, and by the SNAP-04 investigation.

## 2. Round 1: findings and outcomes

There were 16 distinct contract-bearing findings (19 reported, three of them found twice) and 40 fix-only ones.
- **Six keep a promise the documents already make:** task-0257 to task-0262.
- **Ten chose contract content.** They became decision-0033's nine choices, accepted 2026-11-09 ("all as advised"), built as task-0275 to task-0283.
- **SNAP-04,** a partial generation on Neo4j, became decision-0014 Amendment A1, accepted ("accept A1"), and task-0274.
- **The fix-only findings** became task-0263 to task-0272, for 0.9.x.

Every contract-bearing build merged on a whole green matrix, `stack` included where it runs.

## 3. The bounded re-probe (decision-0032 point 4), at `main` `9861953`

Each group re-probed only the surfaces the round-1 fixes touched.

| Group | Surfaces re-probed | Fixed | Not fixed | Regression |
|---|--:|--:|--:|--:|
| 1 | 10 | 9 | 1 (task-0258's deterministic.json form) | 0 |
| 2 | 7 | 7 | 0 | 0 |
| 3 | 8 | 7 | 1 (the same form, plus the `D6_gate` shape bypass) | 0 |

**New contract-bearing findings on the touched surfaces:**
- task-0286: `--baseline` with a deterministic.json; it completes task-0258;
- task-0287: `KG_CLOCK`'s value domain, under choice 2;
- task-0288: the `cadence.register_root` readers, under choice 5;
- task-0292: `held_keys`' gate on a store holding no key, under choice 9(a); it completes task-0283;
- N7, the settings table's reach, put to the maintainer and accepted as decision-0034 choice 1 (task-0294).

## 4. The independent spot check (decision-0032 point 5)

**The reviewer:** `session_01HTAA1R97hqkerDqYvPVLHm`, a fresh session that ran no part of the pass and did not read the probers' reports. It probed `main` at `9861953`.

**The sample:** 8 surfaces drawn at random from 60 (seed 20261109):
- `gate_verdict`;
- the `proposal_impact` CLI;
- `run_status`;
- `document_links`;
- the GitLab include;
- `check_subject`;
- `scenario_result`;
- `subject_check`.

All 8 were probed, rdflib only.

**Findings:**
- **Choices for the maintainer,** accepted as decision-0034 ("N7, D1, D3 as advised"):
  - D1, scenario ids: task-0295;
  - D3, the key rule: task-0296.
- **D2** (`KG_ANNOTATE` values) was already round 1's task-0267 AC #2.
- **SC-1:** `subject_check`'s confinement bypassed through the register map. Fix-only, but it broke H7's documented promise: task-0289, before the cut.
- **GL-1:** a non-ASCII path fails open in the CI gate. It is round 1's task-0267, independently confirmed and pulled forward before the cut.
- **Fix-only:** PI-1 and PI-2 (task-0263), CS-1, CS-2 and CS-4 (task-0265; CS-4 moved to task-0296), and RS-1, SR-1 and SR-2 (task-0291).

Group 1's N4, a blank token on a wide bind, pulled task-0264 forward before the cut, for the same reason as SC-1.

## 5. The re-check of the second round's fixes

Each fix was re-checked by the session that found it, at the `main` that carries it.

| Fix | PR | Re-checked by | At | Outcome |
|---|---|---|---|---|
| task-0287, `KG_CLOCK` (N1, N8, N9) | #432, #436 | group 1 | `0682e16` | fixed, no regression |
| task-0288, named-register readers (N10, N11) | #433 | group 1 | `0682e16` | fixed, no regression; `-h` prints on 15 entry points |
| task-0264, settings at start (N3 to N5, F7 to F9, F13) | #434 | groups 1 and 2 | `0682e16` | fixed, no regression |
| task-0289, SC-1 | #431 | spot check | `0682e16` | fixed, no regression; the existence oracle closed |
| task-0286, record baselines | #438 | group 3 | `95af205` | fixed on the file path; the `record` path's checks are fix-only (§6) |
| task-0292, `held_keys`' gate | #438 | group 2 | `95af205` | fixed, 46 of 46 equal |
| task-0267, CI paths kept whole (GL-1, GL-2, F9, F10, F17, F18, N2, N6) | #435 | group 1, spot check | `c94dfa5` | fixed, no regression; hostile names reach the gate as themselves, no injection |
| task-0294, the settings table's reach (N7) | #439 | group 1 | `c94dfa5` | fixed; the reach test fails on a new unlisted name; the scan's own reach is fix-only (§6) |
| task-0295, scenario ids (D1) | #441, train #442 | spot check | `946c72e` | fixed, no regression; every reader refuses before it writes |
| task-0296, one key rule (D3) | #440, train #442 | spot check | `946c72e` | fixed as specified; K1 found (below) |
| task-0297, every control and format character, nothing above U+FFFF (K1, K2; decision-0034 A1) | #444 | spot check | `f194aac` | fixed, no regression; exhaustive over all 1,114,112 code points, Python and Node v22 (ICU 17.0) with and without `u`, 0 mismatches |
| task-0301, keys in NFC (N3; decision-0034 A2) | building | spot check | | to be appended |

**K1** (the re-check of task-0296): other control and format characters passed the key rule, and the two engines' `\s` differed (K2). Put to the maintainer and accepted as decision-0034 Amendment A1 ("K1 (a) as advised"; "astral (a) as advised"), built as task-0297.

## 6. Fix-only findings, tasked for 0.9.x

**Round 1:** task-0263 to task-0272, with the re-probe's and the spot check's notes appended to them.

**The re-probe and the spot check:**
- task-0290: the hooks' `--config-env` aliases, and an empty Bash event;
- task-0291: run folders read defensively, and `run_status`'s `next`;
- task-0293: `schema_check`'s ASCII `\d`, and `add_artefact`'s backtick.

**The re-check:**
- task-0298: settings-parser follow-ups:
  - group 1's F-a (non-ASCII digits), F-b (padding), F-c (token length and padding) and F-d (the Neo4j URI's shape);
  - group 2's N5 (`KG_PUBLIC_PORT`) and N6 (`KG_PAGE_MAX_RUNS`), both read per request;
  - group 1's B2-4, the settings scan's reach (`KG_ORACLE_TIMEOUT`, `KG_DEMO_URL`).
- task-0299: `--baseline record` runs task-0286's checks, and an empty `gate_keys` is refused (group 3).
- task-0300: a changed file whose name starts with `-` (the spot check's R1, group 1's B2-1), non-UTF-8 names in the report (R2), a linter that fails silently (B2-2).
- task-0263's notes: PI-1 re-confirmed (B2-3).
- task-0265's notes: the spot check's N1 and N2 (`subject_check`'s messages) and T1 (a `[scenario]` table read as no scenarios).

None of them changes a contract.

## 7. Not probed, by every session's own account

- Neo4j for the spot check and the re-checks: they ran rdflib only. Group 2 and SNAP-04 ran Neo4j.
- GitLab on a real runner: task-0108, at the pilot.
- The arms: off by rule.
- A case-insensitive filesystem: Linux only.
