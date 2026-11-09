---
id: doc-0034
title: >-
  Squad slicing, sprint planning, cross-team prioritisation and dependency
  mapping at knowgov 1.0: what works, scored; opportunity canvas, fit/gap, SWOT,
  advice
type: other
created_date: '2026-11-09T07:34:00Z'
updated_date: '2026-11-09T07:34:00Z'
---
*A study: nothing built, nothing minted by the study itself. It was drafted by the read-only study session `session_01HTAA1TrEnivaEeAvAcXMeS`, read on `main` `6d27961` with the register at v0.2.13 (`7980708`), and filed by the coordinating session on 2026-11-09. One correction is made at filing: decision-0031 was accepted on 2026-11-09 (#398), after the study read `main`.*

**Trigger.** The maintainer, 2026-11-09: "investigate how the 1.0 release of knowgov can help a squad in slicing their product backlog items and plan their sprints. Also explain if/how it can support cross-team prioritisation and dependency mapping. Score your findings and identify fit/gap, opportunity, swot."

**Builds on.** doc-0022, doc-0017, doc-0020, doc-0024 and doc-0025; task-0101, task-0152, task-0191 and task-0192. doc-0022's verdict, sense if knowgov reads and gates and nonsense if it holds, ranks or estimates, is not repeated.

**"1.0".** decision-0016 point 4 cuts 1.0.0 on the 0.9 contracts unchanged. So 1.0 is `main` plus the fixes in flight (G9-16, task-0241, and now task-0252); anything else is post-1.0, a minor or 0.10.0. The handover's S11 boundary (no tracker write-back, no estimate, no prioritised plan) is taken from the brief. doc-0028 §10's K11 (slices as fine as the register's links) and U1 (one subject's scenario per store) bear on all four questions.

**Method.**
- **Environment.** A venv outside the checkout with rdflib 7.6.0, pyshacl 0.40.2, pumllint 0.35.0 and pyyaml 6.0.3, on CPython 3.13 rather than the pinned 3.12.
- **Settings.** `KG_STORE=rdflib`, `KG_CLOCK=pinned`, `KG_SUBJECT=subjects/cargo_quote`.
- **Stores.** `harness/run.py --deterministic` loaded S1–S7, matching the record's verdicts: S1 and S6 PROCEED, S3 QUALIFIED, S2, S4, S5 and S7 BLOCKED.
- **Tools run.** `proposal_impact` (the fixture, and `--scope`), `gate_cli --no-load`, `capture.py questionnaire|due`, `step_grid`, `upward.py code`, and the MCP server over stdio (`register_impact`, `key_nodes`, `document_links`). `tools/example_instance.py` was built into scratch.
- **Data.** Synthetic, public content only.

## Q1. Slicing product backlog items

**What works.**
- **The slice map.** `proposal_impact <overlay>`, the MCP `proposal_impact`, or branch mode (`--register-branch DIR --base REF`, task-0132).
  - `slices.map` gives one slice per approved journey step of each product touched, or per delivering process where no journey concerns it, by the vendored `THREAD` walk and rule A1 (ieam-register decision 0018).
  - Every overlay element sits in one slice or a named remainder (`shared`, `required_not_reached` with realisers, `frame`, `exceptions`, `outside`), with the denominator.
- **The scope.** `--scope JRN-|PRD-` gives the same slices on the approved register with no overlay (task-0191).
- **Reuse against new.** `nodes` and `links` new, reused `as_is` or `changed`; `reach` before and after; `rests_on`; placement by `check_nodes` and `check_glossary`.
- **Coverage gaps.** C1–C3 before and after, with denominators; C4 lands with task-0241. Candidates D1–D4 are `authored` or `inferred`, never above `proposed`, and D4 is a pool that never chooses.
- **Keys per slice.** `keys.landed` of `keys.of`, from `register_impact.landed_rows`. With a store, `with_levels` runs one `gate_cli.evaluate` per slice under `--task` and `--as-of`, giving `gate.verdict` and cells (levels, worst, unknown, gaps, lapsed, `behind_withdrawn`, handoffs).
- **The intake sequence.** The MCP server's instructions name it: `proposal_impact`, then the gate per slice, then the tracker writes. doc-0022 K5 is in effect done.

**Worked example 1: the fixture, store S2, `--as-of 2026-10-30`, codegen.**
```
C1: 7/8 -> 8/11 covered; uncovered ['JRN-0014', 'JRN-0015']
C2: 5/5 -> 5/6 covered; uncovered ['CAP-0009']
candidate D4 inferred: JRN-0014: pool ['PROC-0002', 'PROC-0003', 'PROC-0004'], none chosen
product PRD-0006 (new): slices by step ['JRN-0013', 'JRN-0014', 'JRN-0015']; required not reached ['CAP-0002', 'CAP-0003', 'CAP-0009']
slice JRN-0013 (new step): process PROC-0002; capability CAP-0004; application APP-0002; information ENT-0002,ENT-0003
  keys 22 of 36; levels 1 absent, 1 declared_gap, 1 validated, 19 approved; worst absent; unknown 1; gaps 1; owner handoffs 4
slice JRN-0014 (new step): process -; capability -; application -; information -   keys 0 of 36; levels none read
slices: 4 in slices, 8 in the remainder, of 12 overlay element(s)
```

**Worked example 2: the approved register, `--scope PRD-0002`.**

| Store and date | `JRN-0002` | `JRN-0003` |
|---|---|---|
| S1, 2026-10-30 | PROCEED | PROCEED |
| S1, 2027-02-07 | QUALIFIED: lapsed `response\|price_presence`, `quote_id_presence`, `statuses` | QUALIFIED, the same |
| S2 | BLOCKED on `QuoteAPI\|on_screening_outage` (declared_gap) and `response\|hold_presence` (absent) | the same |

In both scenarios the remainder is `CAP-0003`, required and not reached. The two slices share 12 of their 22 keys each, 32 in union. `step_grid` lists the 4 keys on no step: `CAP-0003`'s `S-*` screening bands.

**Limits.**
- **(a) Keys are the map's, not the class's** (`with_levels`: `spec = dict(TASKS[task], keys=<slice rows>)`).
  - CargoQuote's map holds the 36 codegen keys only, so under `--task design` S2's slices block on `response|hold_presence`, which design does not require.
  - They miss `REQ-06|text`, which blocks the subject's design gate, and 21 of design's 36 keys land on no slice.
  - The maintainer placed the fix in 0.9.0 (Answered below; task-0252).
- **(b) Shared keys.** Slices share keys through shared nodes, so one gap blocks both. Key overlap is not reported: `shared` groups overlay elements, not keys.
- **(c) New steps.** A new step with no thread reads `keys 0 of 36`, with no verdict. That is unknown, not ready.
- **(d) K11.** Steps supported only by one end-to-end process share a thread.
- **(e) C4** is missing until task-0241.
- **(f) Out of scope.** No write-back, estimate, rank or planning label (decision-0008; doc-0014 decision B). K3 (task-0153) and K4 (task-0154) stay parked.
- **(g) Branch mode** reads additions only (K14).

## Q2. Sprint planning

**What works.**
- **Definition of ready.** `gate_cli.py --task <class> --as-of <sprint end> [--fail-on] [--baseline]`: exit 0, 1 or 2, PROCEED, QUALIFIED or BLOCKED, with JSON under `gate-report.schema.json` v3 (`task_profile`, `register`, `knowgov`).
  - The same per slice through `proposal_impact --scope … --task … --as-of …`, or the MCP `gate_verdict keys=…`.
  - Wired in by `instance/ci/knowgov-gate.sh`, the GitHub and GitLab wrappers, and the Claude Code hook at plan, spec commit and push (task-0102).
- **Routing.** Each key finding carries `owner`, `route` (the owner's questionnaire), and for a declared gap `closer` (task-0102, task-0110). `capture.py questionnaire --scenario S --task T --out DIR` writes one file per unit.
- **Cadence.** `valid_until` is the review date plus the key's months (register `lifecycle.toml`). A lapse reads validated and is a `lapsed` finding (decision-0005). `capture.py due --on DATE`.
- **Preconditions.** `tools/preload_check.py` lints the documents. The gate lists flawed or unchecked documents behind its keys at info (task-0064, task-0085).
- **Re-entry.** `trace check`, `--register-previous` (task-0122), and the lapse.
- **Snapshot.** `step_grid.py` (task-0192).

**Worked example, store S1.** On `--as-of 2027-02-06`: PROCEED, all 36 required keys verified or approved. On `--as-of 2027-02-07`: QUALIFIED, with 3 keys lapsed, each naming owner ORG-0002. A sprint ending on or after 2027-02-07 plans with those as stated assumptions, or schedules the review first. On S2: `blocker QuoteAPI|on_screening_outage is declared gap [owner ORG-0002; closed by ORG-0004]`, and the questionnaire reads "ORG-0002: 3 of the 7 keys you own need an answer".

**Limits.**
- No due date on an open gap: due dates exist for review cadences and elicited links only.
- Pre-load findings are info, never a blocker, and are not filtered per slice.
- Q1's limit (a), until task-0252.
- No capacity, velocity or effort, by decision.
- One scenario per store (U1, U2).

## Q3. Cross-team prioritisation

**What works.**
- **Owners.** One `owner` per map row (task-0043); every register node and link has an `ORG-` owner. `register_impact` and the slices give `owning_unit` per reached node. Slice `handoffs` are the thread edges whose ends have different owners.
- **Cross-domain approvals.** The register's `[approval] four_eyes = true` and `cross_domain_both_owners = true`. `proposal_impact.approvals` lists nodes and links per unit, and a link across two units appears under both.
- **Reach.** `register_impact node=… walk=dependants|realisers [children]` gives the reached nodes with owners and the landed keys with levels (task-0111, task-0118). `--register-previous` stales keys on a withdrawn node.
- **Journey readiness.** Slices under `--scope JRN-…`, or `step_grid`.

**Worked example.** `register_impact node=APP-0004` (ScreeningService, ORG-0002) reaches `CAP-0003` (ORG-0002), and `PROC-0003`, `PROC-0001`, `PRD-0002` and `JRN-0001` (all ORG-0001). It lands 16 keys: 14 owned by ORG-0001, 2 by ORG-0002. On S2 they read 15 approved and 1 declared_gap. A ScreeningService change is ORG-0002's work but mostly ORG-0001's knowledge.

**Inputs to WSJF, cost of delay or RICE.**

| Input | knowgov | Source |
|---|---|---|
| Value, user reach, confidence in value, effort | nothing | none |
| Time criticality | lapses before a date; existing products and journeys reached | `--as-of`; `reach`; `register_impact` |
| Risk reduction and opportunity enablement | absent, declared_gap and disputed keys; enablers (`required_not_reached`) | gate; slices |
| Job size | a proxy only: new against reused, gaps, owners, handoffs | `proposal_impact` |
| Dependencies | the realisers chain; node before link approval; both owners | register; `approvals` |

Key levels are confidence in the knowledge, not in the value.

**Limits.**
- No portfolio roll-up. Squads share one register, but keys, levels and owners are read per subject (U1, U2), so comparing squads is manual stitching.
- No scoring engine, by decision.
- Owners are units, not teams with capacity.

## Q4. Dependency mapping

**What works.**
- **The register's typed links.** `concerns`, `crud`, `delivers`, `is_supported_by`, `manages`, `maps_to`, `owns`, `realizes`, `requires` and `supports`, each with a kind, cardinality per state, owner, evidence and `review_due`.
  - The walks (`dependants`, `realisers`, `THREAD`) follow approved links only; a withdrawn edge is listed `live: false` and not followed.
  - `JRN-0003 is_supported_by PROC-0005` is proposed, and shows in the slice's `withdrawn` with its 4 keys.
- **Code.** `code_map.toml` (code to `APP-`, task-0050), `trace register|check` (task-0051), header citations (task-0124), and `code_path`.
- **Documents.** `document_links` and `document_statements` (task-0143).
- **Derived outputs.** `derived_outputs` (task-0144).
- **The chain.** Down and up are composed from named hops, never one walk both ways (doc-0020).

**Worked example.**
- `key_nodes QuoteAPI|on_screening_outage` gives `APP-0002`, `APP-0004`, `PROC-0003`, `PROC-0001` and `JRN-0003`, owner ORG-0002.
- `register_impact CAP-0004 walk=realisers` gives `PROC-0002` (ORG-0001) and `APP-0002` (ORG-0002), and 19 keys: 12 owned by ORG-0001, 7 by ORG-0002.
- `document_links contract/decision_table.md` gives REL-01001..01003, REL-04003, REL-07001, REL-07003 and REL-08003.
- `upward.py code reference_impl.py` gives `APP-0001`, citations `[]`, and the ledger `unchecked`. Module grain needs citations.

**What a missing link means.** No evidence of no dependency. The coverage rules (C1–C4, A1) catch some missing links: a step with no supporting process, an unrealised capability, a required capability no step reaches. Nothing else flags one. The upward tools say `unchecked` rather than empty, and D1–D4 propose candidates, never links.

**Against a tracker's dependency links.**

| | Tracker (blocks / blocked by) | knowgov |
|---|---|---|
| Between | work items | durable register elements, keys, code and documents |
| Who says so | anyone, unreviewed | owner-approved, four eyes, both owners across domains, evidence cited |
| Lifetime | the item's | versioned; a withdrawal stales keys (task-0122) |
| Order | yes | no, beyond node-before-link approval and the realisers chain |
| Discovered | no | no, declared only |
| Coverage claim | none | against C1–C4 and A1, with denominators |

**Limits.**
- No runtime discovery.
- No item-to-item dependency.
- `code_map` grain is the application unless `[citations]` are required.
- The connector is proven on synthetic exports only (K16).
- A register change is read only with `--register-previous` (K17).

## Scoring

Support at 1.0 runs 0–5, capped at 4 because there is no foreign corpus yet (task-0062, decision-0016 point 4). Value is high, medium or low. Effort is after 1.0, a candidate only.

| # | Capability | Support | Evidence | Value | Effort |
|---|---|---|---|---|---|
| 1a | Slice map by journey step | 4 | task-0152, `test_proposal_impact.py` | high | S: per-key shared |
| 1b | Reuse against new, reach, rests-on | 4 | task-0130, task-0131 | high | none |
| 1c | Coverage gaps | 3 | C1–C3; C4 is task-0241 | high | S: task-0241 |
| 1d | Keys per task class per slice | 2 | codegen only; design misreads | high | S: task-0252, in 0.9.0 |
| 1e | Gate readiness per slice | 4 (codegen) | task-0191 | high | S: unknown verdict for 0-key slices |
| 1f | Link candidates D1–D4 | 3 | built; precision unmeasured | medium | M: measure at the pilot |
| 1g | Backlog coverage, write-back | 0 | K3 parked (task-0153); write-back out | medium | M: K3 |
| 1h | Estimates, rank | 0 | out by decision | none | tracker |
| 2a | DoR gate and hook | 4 | task-0007, task-0102 | high | none |
| 2b | `--as-of` sprint end, lapses | 4 | decision-0005, task-0068 | high | none |
| 2c | Gap routed to owner and closer | 4 | task-0102, task-0110 | high | none |
| 2d | Due dates | 2 reviews / 0 gaps | `capture.py due`; no gap SLA | medium | S, or tracker |
| 2e | Pre-load findings as preconditions | 3 | task-0064, task-0085 | medium | S: per-slice filter |
| 2f | Re-entry: trace, register change, lapse | 4 | task-0051, task-0122 | high | none |
| 2g | Scenario by step grid | 4 | task-0192 | medium | none |
| 2h | Capacity, velocity, effort | 0 | out | none | tracker |
| 3a | Owners per key and node, handoffs | 4 | task-0043, task-0047, task-0191 | high | none |
| 3b | Cross-domain approvals | 4 | register lifecycle; `approvals` | high | none |
| 3c | Reach of a change | 4 | task-0111, task-0118 | high | none |
| 3d | Journey readiness across steps | 4 | task-0191, task-0192 | high | none |
| 3e | Across squads' subjects | 2 | per subject; U1, U2 | medium | M/L: task-0164 |
| 3f | Prioritisation inputs | 2 | data across tools | medium | S: task-0253, docs |
| 4a | Typed approved links and walks | 4 | register v0.2.13, task-0044, decision 0018 | high | none |
| 4b | Code to application, trace | 3 | task-0050, task-0051, task-0124 | medium | S: require `[citations]` |
| 4c | Document and derived links | 4 | task-0143, task-0144 | medium | none |
| 4d | Missing-link semantics | 3 | coverage rules; `unchecked` legs | medium | none: a stance |
| 4e | Runtime discovery | 0 | out (doc-0011) | medium | L; not knowgov's |
| 4f | Item-to-item dependencies | 0 | out | high, in a tracker | tracker |

**Weighted.** Value weights are high 3, medium 2, low 1, with out-by-decision rows excluded. The weights are an aid, not a measure.
- Q1: 3.3/4, with 1d the one in-scope gap, now task-0252.
- Q2: 3.6/4.
- Q3: 3.5/4: 4 within one subject, 2 across squads.
- Q4: 3.6/4 for declared dependencies, and 0 for runtime discovery.

## Fit/gap

| Use case | Requirement | Fit/gap |
|---|---|---|
| Slicing | R1 vertical slices from approved facts | Fit |
| | R2 every element placed, with a denominator | Fit |
| | R3 new against reused | Fit |
| | R4 gaps as items | Fit, once task-0241 lands C4 |
| | R5 readiness per slice for the task class in hand | Gap for any class but codegen; task-0252 in 0.9.0 |
| | R6 shared knowledge visible | Partial (limit b) |
| | R7 no write-back, estimate or rank | Fit by design |
| Sprint | R8 a binary DoR in CI and at the agent | Fit |
| | R9 readiness at the sprint's end date | Fit |
| | R10 each blocker routed to an owner | Fit |
| | R11 a due date per blocker | Gap: the tracker's |
| | R12 document quality as a precondition | Partial: info only |
| | R13 work sent back on change | Fit |
| | R14 capacity and velocity | Out |
| Cross-team | R15 owners and handoffs | Fit |
| | R16 cross-domain approval rule | Fit |
| | R17 reach of a change | Fit |
| | R18 portfolio readiness across squads | Gap (3e) |
| | R19 a prioritisation score | Out by decision |
| | R20 inputs to the team's method | Partial; task-0253 documents them |
| Dependencies | R21 typed, owned, approved links | Fit |
| | R22 code and document joins | Fit, at application grain |
| | R23 honest absence | Fit |
| | R24 runtime discovery | Out |
| | R25 work-item order | Out: the tracker's |

## Opportunity canvas

| Block | Content |
|---|---|
| Users | Product owners and squads refining and planning; architects at intake; capability and process owners asked to approve or answer; delivery leads across squads; an assistant over MCP beside the tracker's connector |
| Problem | Slices cut on sticky notes; readiness guessed at planning; cross-team approvals started late; dependencies in tickets that expire with the sprint; missing knowledge surfacing in build |
| Today | Story mapping by hand, the EA tool's impact view and tracker links. In knowgov at 1.0: `proposal_impact` (slices, `--scope`, branch mode), the gate and its hook, `--as-of`, `capture.py`, `register_impact`, `step_grid`, and the upward tools |
| Solution at 1.0 | The intake sequence in the server's instructions: the overlay, then slices, then the gate per slice, with owners routed. The tracker writes and orders |
| Value | Readiness per slice as a fact with a route; lapses seen before the sprint; cross-domain approvals named at intake; owner-approved dependencies that outlive the sprint |
| Metrics | Share of slices PROCEED or QUALIFIED at planning; blockers found at refinement against those found in build; items reopened by suspect, stale or lapsed; days from gap to answer, from the tracker's dates |
| Cost after 1.0 | Per-key shared S; 0-key verdict S; K3 M; cross-subject M/L. task-0252 and task-0253 land before or within 0.9.x |
| Risks | Being read as a plan or a priority; a synthetic register of 57 nodes; owners are units, not teams |
| Unfair advantage | Gaps and owners from approved rules with denominators; statement-grain levels per key; deterministic and read-only |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** slices, gate, routes and reach are built, tested, deterministic and schema-pinned on CLI and MCP; the server's instructions name the intake sequence | **W:** class readiness per slice misread until task-0252; key overlap between slices unreported; new steps read "0 of N" with no verdict; one subject per call; proven only on synthetic subjects |
| **External** | **O:** a DoR every squad can wire into CI and its agent; the lighthouse (task-0062) can measure blockers found at refinement; K3 once a tracker is named | **T:** being read as a planning or scoring tool; adopters expecting tracker integration or runtime dependency maps; a coarse register (K11) giving one fat slice |

## Advice

**What to tell a squad today:**
1. Run `proposal_impact` on the feature's overlay, or `--scope` on the journey. The slices are the story map's columns, and the remainder (`required_not_reached` and the gaps) is the discovery items.
2. Per slice, PROCEED or QUALIFIED under `codegen --as-of <sprint end>` is the definition of ready. The hook and `knowgov-gate.sh` enforce it.
3. Send each blocker's `route` to its owner as a tracker item. The tracker holds the due date.
4. Read `approvals` and `handoffs` at refinement, so cross-domain approvals start before the sprint.
5. Until task-0252 lands, use the subject's `gate_cli --task design`, not `--task design` per slice.
6. Keep value, effort, order and ticket dependencies in the tracker.

**Worth closing after 1.0, ranked.** Each is a post-1.0 minor (or 0.10.0):
1. Per-key `shared` across slices, and an explicit `unknown` verdict for a 0-key slice. Additive schema.
2. K3 backlog coverage (task-0153), once the pilot's tracker is named. A new tool and schema.
3. Cross-subject readiness (task-0164, U1). It needs its own decision.

**Leave to the tracker:** estimates, capacity, velocity, ordering, item dependencies, gap due dates and write-back. Leave runtime discovery to observability or process mining (doc-0011).

## Answered (2026-11-09)

The maintainer, on D1, the per-slice gate under a non-codegen task class: "(a), fix it in 0.9.0".
- **task-0252** builds it. A slice reads its class's keys among the rows landing on its thread, and the class's keys on no slice become a named remainder with the denominator. `register_impact` keeps its reach semantics and says so. It is an additive contract change to the `proposal-impact` output, gathered for 0.9.0.
- **task-0253**, the prioritisation-inputs recipe, is docs only and needed no decision (the study's D2). It is a 0.9.x patch.
