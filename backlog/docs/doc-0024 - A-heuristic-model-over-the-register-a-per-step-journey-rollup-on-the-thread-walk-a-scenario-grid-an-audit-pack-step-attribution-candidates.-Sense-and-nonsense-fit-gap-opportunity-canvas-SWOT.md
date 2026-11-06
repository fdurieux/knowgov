---
id: doc-0024
title: >-
  A heuristic model over the register: a per-step journey rollup on the thread
  walk, a scenario grid, an audit pack, step-attribution candidates. Sense and
  nonsense, fit/gap, opportunity canvas, SWOT
type: specification
created_date: '2026-11-05T23:02:00Z'
updated_date: '2026-11-06T17:19:00Z'
tags:
  - brief
  - canvas
  - fit-gap
  - swot
  - register
  - mcp
  - impact
---
*2026-11-05, recorded 2026-11-06. Maintainer register. A study: nothing built, no task opened. J1 to J6 are proposals with no ids.*

*Trigger: the maintainer's question: does a heuristic model in knowgov make sense? It would apply to a subject's register to test scenarios and analyse an end-to-end journey down to its applications, with relevant use cases, sense and nonsense, an opportunity canvas and fit/gap.*

*Read on knowgov `main` at `8f20af0`. The register is v0.2.11 (decision 0018 approved, vendored by task-0155); task-0152 and task-0144 are done. Executed:*
- *a read-only script over the register's `load_register`, `impact.walk(…, THREAD)`, `walk_children` and `descendants`, committed nowhere, joining per reached node the keys of `subjects/cargo_quote/register_map.toml` and `subjects/jef_data_load/register_map.toml`;*
- *`harness/proposal_impact.py --no-store` on an overlay that adds nothing;*
- *ieam-register `tools/check_register.py`.*

*A first pass on v0.2.10 with a hand-composed walk gave §2's four findings; decision 0018's record re-measured them. Not read: key levels (no store), real register names. Synthetic content only.*

## Verdict

**Sense, if the "heuristic model" is a declared, deterministic aggregation over the register's walks and the gate's key levels; nonsense if it is a quantitative simulation or a single score.**

- **The precedent is pumllint's `SCORING.md`.** It is "a reporter-layer aggregation over rule findings" and "introduces no new analysis machinery": rules stay the single source of truth, weights are declared, and the output is a gap report. The same shape fits here. The register's walks and coverage rules and the gate's levels are the rules. The aggregation is per journey step.
- **The trace is ieam-register decision 0018** (doc-0022 K2a; ieam-register#29, v0.2.11, vendored by task-0155).
  - `THREAD` goes from step to process, then from the process to the capability it realises, the applications that support it and the entities it reads or writes (`crud` forward), and from an application to what it manages.
  - A journey threads its steps with `--children`.
  - Rule A1 warns when a product and its journeys disagree on capabilities.

  knowgov composes no trace of its own: that would be a second walk semantics (doc-0017 §6, doc-0022 §8). 0018's record carries this study's four CargoQuote findings.
- **The slice map exists.** task-0152 (doc-0022 K1) gives, per approved step of a product in scope:
  - the thread by layer, each node with its kind, owner and status;
  - the withdrawn edges and the owners;
  - A1's required capabilities not reached.

  It scopes by a proposal's footprint only, and keys with levels come per reused node, not per slice.
- **What is new is the layer on the thread:**
  - the same slices on the approved register, with each slice's keys and levels (J1);
  - a grid of steps against knowledge scenarios (J3);
  - an audit pack per journey (J4);
  - step-attribution candidates (J5).
- **Out.**
  - Dynamic or quantitative simulation (volumes, latency, cost, failure probabilities). The register holds no attributes by contract, and doc-0015 §1 leaves simulation to the process tools.
  - A single risk score: it hides `unknown`, and the register's coverage is "never used as a percentage to pass".
  - Weighted structure scores (degree, concentration) stay parked: 57 nodes cannot calibrate a weight.

"Scenario" has three readings, all served:
- **structural:** an overlay (`proposal_impact`) or a node retired (`register_impact`);
- **epistemic:** a subject's scenarios through `knowgov-runs` (task-0133) or `run.py --deterministic`;
- **temporal:** `--as-of` (decision-0005).

## 1. The question, as a prompt

> Given a journey in the register and a subject's knowledge, can knowgov say per step:
> 1. what supports it down to applications and entities;
> 2. how ready the knowledge under it is, under a task class, a scenario and a date;
> 3. who must answer or approve;
>
> and rank what a structural change touches, without simulating, scoring risk or holding attributes the tools own?

## 2. What exists, measured

**The journey threaded per step** on register v0.2.11: `impact.walk(reg, <step>, THREAD)` from the register's own `impact.py`. Keys are those of the subject's `register_map.toml` that name any reached node: CargoQuote has 36, J-F 163.

| Step | Grain | Reached | Withdrawn | Keys | Owners |
|---|---|---|---|---|---|
| JRN-0002 Submit a quote request | activity | PROC-0002, CAP-0004, APP-0002, ENT-0002, ENT-0003 | none | 22 | ORG-0001, ORG-0002 |
| JRN-0003 Receive the quote, hold or refusal | activity | PROC-0004, CAP-0002, APP-0003, ENT-0003, ENT-0004 | PROC-0005 (`proposed`) | 18 | ORG-0001, ORG-0002 |
| JRN-0004 Quote API (touchpoint) | none | nothing (EXC-0001, to 2027-01-31) | none | 0 | ORG-0001 |
| JRN-0006 Sync the store | subprocess | PROC-0007, CAP-0007, APP-0006, APP-0008, ENT-0008, ENT-0009 | none | 65 | ORG-0003 |
| JRN-0007 Check the store's health | subprocess | PROC-0008, CAP-0008, APP-0007, ENT-0008 | none | 66 | ORG-0003 |
| JRN-0009, JRN-0010, JRN-0011 | end_to_end_process | PROC-0006, APP-0005, ENT-0007, ENT-0010 | the `crud` edge to ENT-0010 (deprecated) | 100, the same for each | ORG-0003 |

- **With `--children`:** JRN-0001 reaches 9 nodes and JRN-0005 13.
- **The checker on v0.2.11:** 0 errors, 10 warnings.
  - C1 7/8 (1 excepted), C2 5/5, C3 5/5.
  - A1: 0 of 3 products aligned. One has no journey, one has a required capability not reached, one has a reached capability not required.
- **The three coarse steps carry the most keys:** 100 of 163, the same 100 for each. A change to a finer J-F step touches 65 or 66.

**Four findings.** Each is a question for an owner, not an error.

1. **Screening is on no step's thread.**
   - PROC-0003 *Screen the shipper* carries 14 keys, among them S2's REQ-06 outage key. Its application is APP-0004 ScreeningService.
   - The dependants walk from APP-0004 reaches JRN-0001 only through the product: APP-0004 → PROC-0003 → CAP-0003 → PRD-0002 → JRN-0001.
   - So "which step does a screening outage hit" has no authored answer. A1 reports the same gap from the product side: PRD-0002 requires CAP-0003, and no step reaches it.
2. **Four keys rest on a link the walk does not follow.** JRN-0003 → PROC-0005 *Notify the shipper* is `proposed`.
3. **Three steps are supported only at end-to-end grain.**
   - JRN-0009, JRN-0010 and JRN-0011 rest on PROC-0006 alone, so they share one thread and cannot be told apart.
   - `THREAD` does not descend a supporting process's activities: `parent` adds starts only at the start (decision 0014). 0018's record says so: "the walk is as fine as the links".
   - The kind of the supporting process (`end_to_end_process`) is the fact a report shows beside the step.
4. **Four processes are on no step's thread:** PROC-0001, PROC-0003, PROC-0009, PROC-0010.
   - PROC-0001 is the end-to-end process above PROC-0002 to PROC-0005.
   - PROC-0009 is an activity under PROC-0007.
   - PROC-0010 *Seam frame export* is approved and serves the process axis (doc-0022 §9 item 3).

**The slice map on the approved register is not reachable today.** `proposal_impact` refuses an overlay that adds nothing ("the proposal adds no node and no link"), with or without a reused node marked `as_is`. task-0152's AC4 test reads the approved register through a two-entity probe overlay (`test_on_the_approved_register_…`).

**The hops already built** (doc-0020, on the read-only server):
- `register_nodes` gives the listing and each node's lineage (task-0142).
- `key_nodes`, `code_path` and `document_links` are the upward joins (task-0143).
- task-0144 gives every key the held scenario holds, with its level, and every derived output on a key.
- `register_impact` gives key levels per node under a task class and an `as_of` (task-0120).
- `proposal_impact` is the overlay with its slice map (task-0130 to task-0132, task-0152).
- `knowgov-runs` runs a scenario (task-0133).

## 3. Use cases

| # | Question | Built on | New |
|---|---|---|---|
| U1 | Can this journey be built or changed, step by step? | `THREAD`, task-0152's slices, `register_impact` levels | J1 |
| U2 | Which steps' keys lapse before a release or audit date? | `--as-of`, cadence | J1 with `as_of` |
| U3 | Which steps does each knowledge defect reach (S1 to S7)? | deterministic runs, `key_nodes` | J3 |
| U4 | An application goes down or retires: which steps lose live support, which keys, which owners? | `register_impact` dependants (journey grain) | J1 read from the application, step grain; doc-0025's study, application lifecycle |
| U5 | Initiative intake, reuse judged on its evidence | `proposal_impact` with its slice map | nothing: task-0152 |
| U6 | Journey continuity: steps with nothing live behind them, end-to-end support only, keys behind a proposed link | C1, A1, slice cells | cells of J1 |
| U7 | Suggest the missing step link (finding 1) | D3/D4 (task-0131), A1's finding | J5 |
| U8 | Who signs off a change to this journey: owner handoffs along the thread | slice owners, `route`, `closer` | a count in J1 |
| U9 | An audit pack for one journey: each link's approval, evidence, `review_due`; expiring exceptions (EXC-0001, 2027-01-31) | the register's files | J4 |
| U10 | Concentration: applications many steps depend on | the walks | J6, parked; doc-0025 |

## 4. Fit/gap

| Needed | Today | Fit/gap |
|---|---|---|
| Journey → steps | `children`, decision 0014 | Fit |
| Step → process → applications, capability, entities | `THREAD`, decision 0018, vendored (task-0155) | Fit |
| Required capability on no step's thread | A1 `check_alignment`; `required_not_reached` in task-0152's slices | Fit |
| Grain of a step's support | the process cell's `kind` in a slice | Fit |
| Key levels per node, task class, `as_of` | `register_impact` (task-0120); `keys.by_node` in `proposal_impact` | Fit |
| Every key the held scenario holds, with its level | task-0144 | Fit |
| Slices on the approved register, a named journey or product in scope | an overlay that adds nothing is refused (measured) | **Gap: J1** |
| Keys and levels per slice | per reused node only | **Gap: J1** |
| Step × scenario grid | one run at a time; `start_run` wipes the shared store (decision-0008) | **Gap: J3**, over run folders |
| Audit pack per journey | everything is in the files; nothing assembles it | Gap: J4 |
| Step-attribution candidates on the approved register | D3/D4 on an overlay; a model's candidates parked (doc-0017 candidate 4) | Gap: J5 |
| Weights as a governed artefact | pumllint `SCORING.md` the template; none here | Parked: J6 |
| Criticality, volumes, SLAs | the register never holds tool attributes | Out. Open: read from `exports/<system>/<date>/` at query time, never copied |
| Dynamic simulation, a single risk score | none | Out (doc-0015 §1) |

## 5. Opportunity canvas

| Block | Content |
|---|---|
| Users | Journey and product owners (ORG-0001); application owners (ORG-0002); compliance (OD-1, ORG-0004); auditors; the lighthouse pilot's architects (task-0062); an assistant asked "can we change this step" |
| Problem | A journey is drawn in the modelling tool and its applications are listed in the portfolio tool. Nothing says per step whether the knowledge behind it is verified, current or contested, or which step a defect or an outage reaches. The slice map answers per step for a proposal only, and its keys come per reused node |
| Solution | task-0152's slices, scoped by a named journey or product on the approved register. Each slice gets the keys landing on its thread, with levels under a task class and an `as_of`: worst level, gaps, lapses, keys behind withdrawn edges, owner handoffs. J3 sweeps the subject's scenarios. J4 assembles an audit pack. Every cell carries its denominator and `unknown`; every inferred element is labelled `inferred`. No score. Nothing stored |
| Value | A step-grain readiness view no EA tool gives. Hidden gaps found (finding 1). A release or audit date's lapses known in advance. Owners routed before a change starts |
| Metrics | Calls from journey to per-step readiness (target 1). Step-grain gaps found per journey. Candidate precision (accepted over proposed) at the pilot. Pilot architects' use |
| Channels | MCP (the reader, `proposal_impact`'s tool), the page's impact view, the CLI in an instance's CI |
| Cost | J1 small to medium: a scope and a keys field in one evaluator, schema additive. J3 small. J4 small. J5 medium |
| Risks | A rollup read as a score. A heuristic promoted to fact. Pressure to copy tool attributes into the register. Drift into an EA tool. Coarse links read as fine: three steps share one thread (finding 3) |
| Unfair advantage | Statement-grain epistemic levels attached to each step. Deterministic and read-only: the same register, subject and date give the same answer |

## 6. SWOT

**J1, the build this doc recommends.**

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S.** Every input exists (`THREAD`, A1, task-0152's slices, `landed_rows`/`with_levels`, task-0144); no walk of its own; the step grain separates (22/18 of 36, 65/66 of 163); deterministic, read-only | **W.** As fine as the links (JRN-0009 to JRN-0011: one thread, the same 100 keys); keys from a subject's map, not the register; levels unread here; a contract change to `proposal_impact`; 57 synthetic nodes |
| **External** | **O.** One call per journey for U1, U2, U6, U8; the pilot's intake demonstration extended to what exists; finding 1 shown per step with its 14 keys; J3 and J4 read J1's cells | **T.** A rollup read as a score; decision-0016's freeze (proposed); overlap with doc-0025 on U4, U10 |

The evidence for each cell:

**Strengths.**
- Every input exists:
  - `THREAD` and A1 (decision 0018, vendored by task-0155);
  - task-0152's slices: the thread by layer, each cell with kind, owner and status, plus withdrawn edges and owners;
  - `register_impact`'s `landed_rows` and `with_levels`, which `keys.by_node` already reads;
  - task-0144's held-scenario reads.

  J1 adds no walk and no walk rows.
- The step grain separates what the journey grain merges. CargoQuote's two steps land on 22 and 18 of 36 keys; J-F's two finer steps on 65 and 66 of 163 (§2).
- It is deterministic and read-only. The same register, subject and `as_of` give the same answer, as `proposal_impact` already holds for CLI and MCP (task-0152).

**Weaknesses.**
- **The thread is as fine as the links.** JRN-0009 to JRN-0011 share one thread and the same 100 keys (finding 3). J1 reports this; it cannot resolve it.
- **Keys per step come from a subject's `register_map.toml`, not from the register.** CargoQuote's map is `authored` (approved 2026-10-31) and J-F's `derived` (approved 2026-11-02). A step's keys are only as complete as its map rows.
- **Levels were not read here** (no store). The cells' values on a held scenario are unmeasured.
- **It changes a contract.** `proposal_impact` refuses an overlay that adds nothing (measured), so J1 changes its input (a scope with no overlay) and its report (keys per slice).
- **57 synthetic nodes; real names not read.**

**Opportunities.**
- **One call per journey answers U1, U2, U6 and U8**, which today take a walk per step plus `register_impact` per node.
- **The pilot:** doc-0017 and doc-0022 make intake the architects' first demonstration (task-0062). J1 extends the same answer to what already exists.
- **Finding 1 shows per step with its weight.** Screening sits on no step's thread, while PROC-0003 carries 14 keys, S2's outage key among them.
- **J3 and J4 read J1's cells**, so neither needs a read of its own.

**Threats.**
- **A rollup read as a score.** A per-step "worst level" invites a readiness percentage, against the register's "coverage is never a percentage to pass". Mitigation: cells carry denominators and `unknown`, no aggregate across steps.
- **The contract freeze.** decision-0016 (proposed) makes 0.9.0 a freeze with 0.9.x fixes only. If it is accepted, J1's contract change lands before 0.9.0 or waits for the next minor after it.
- **Overlap with doc-0025** (applications to refactor, sunset or replace, reserved) on U4 and U10: two studies reading the same walks from the application side.

**The parked and rejected candidates, where they bear on the advice.**

| Candidate | Weakness | Threat | Bearing |
|---|---|---|---|
| J3 grid | Needs one run folder per scenario | `knowgov-runs`' `start_run` wipes the store every viewer shares (decision-0008) | Route over run folders, after J1 |
| J4 audit pack | No auditor's ask recorded | Assembly without a reader | Park |
| J5 step-attribution candidates | Precision unmeasured; 57 synthetic names | A candidate read as a link; a candidate never closes a gap | Park until a real register |
| J6 weights | 57 nodes cannot calibrate a weight | A score hides `unknown` | Park |
| Simulation, a single risk score | The register holds no attributes by contract | A second record; an EA tool's job (doc-0015 §1) | Reject |

## 7. Sense and nonsense

**Sense.**
- The aggregation on the pumllint pattern: rules decide, the summary only aggregates, and a gap report says what blocks.
- The step as the unit, on the register's own walk and task-0152's slices.
- All three scenario readings.
- Inferred candidates for missing links, routed to an owner as a register pull request.

**Nonsense.**
- Simulation on attributes the register refuses to hold.
- A journey risk percentage.
- A model scoring impact.
- One undirected walk: doc-0011 measured that every start reaches the same 15 nodes.
- knowgov composing the thread from raw links.
- Weights calibrated on 57 synthetic nodes.

## 8. Candidates

| # | Candidate | Relation to what exists | Disposition |
|---|---|---|---|
| — | The journey trace | **is decision 0018's `THREAD`**; findings 1 to 4 are in its record | No knowgov item |
| J1 | Slices on the approved register, each with its keys and levels | task-0152's slices with two additions. (a) A scope by a named journey or product with no overlay. (b) Per slice, the `register_map.toml` keys landing on its thread, with levels per task class and `as_of`, as `keys.by_node` reads them (`register_impact` `landed_rows`, `with_levels`). Cells: worst level, gaps, lapses, keys behind withdrawn edges, owner handoffs. Facts only, denominators shown | **Build** on the maintainer's go, as a follow-up of task-0152 (§9 item 1) |
| J2 | Support grain per step (finding 3) | the process cell's `kind` in a slice; 0018 records the limit | **No item** |
| J3 | A step × scenario grid from `run.py --deterministic` run folders, keys to steps through `key_nodes` and `THREAD` | `knowgov-runs` exists, but `start_run` wipes the shared store | **New**, small, after J1. CLI over run folders |
| J4 | An audit pack per journey: the thread with each link's approval, evidence, `review_due`, the exceptions and their expiry | new | **Park** to the pilot, on an auditor's ask |
| J5 | Step-attribution candidates on the approved register: A1's gap, the BPMN order, D3/D4's pool; `inferred`, never above `proposed`, precision measured | D3/D4 (task-0131); doc-0017 candidate 4 | **Park** until precision can be measured on a real register |
| J6 | Weighted structure scores (concentration, ranking a what-if's reach), weights in a versioned file under a decision | pumllint `SCORING.md` the template; doc-0025 for applications | **Park** to the pilot |
| × | Dynamic simulation; a single risk score; tool attributes in node files; a model's impact score; knowgov's own trace | doc-0015 §1; the register's contracts; doc-0022 §8 | **Reject** |

## 9. For the maintainer

1. **J1's home.** Recommended: task-0152's evaluator, with a scope by journey or product and keys per slice. One evaluator, one schema, one shape of answer for an initiative and for what exists. A separate read would compute the same slices twice. Timing (§6 threats): if decision-0016 is accepted, J1 lands before 0.9.0's freeze or in the next minor after it.
2. **The scenario grid (J3).** Recommended: a CLI over deterministic run folders, after J1, not through `knowgov-runs`, so a sweep never wipes what every viewer of the page sees.
3. **J4 and J5.** Recommended: park both to the pilot.
4. **Scores and simulation.** Recommended: J6 parked; simulation and a single risk score rejected, as doc-0015 §1 already holds.
5. **The coarse J-F steps.** Not knowgov's call: whether JRN-0009 to JRN-0011 get finer processes is a register content change for ORG-0003. 0018 leaves it open.
