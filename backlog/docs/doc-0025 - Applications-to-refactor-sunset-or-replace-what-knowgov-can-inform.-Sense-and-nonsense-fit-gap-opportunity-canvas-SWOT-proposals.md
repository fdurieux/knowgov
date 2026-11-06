---
id: doc-0025
title: >-
  Applications to refactor, sunset or replace: what knowgov can inform. Sense
  and nonsense, fit/gap, opportunity canvas, SWOT, proposals
type: specification
created_date: '2026-11-05T23:02:00Z'
updated_date: '2026-11-06T17:07:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - sense-nonsense
  - register
  - applications
---
*2026-11-05, re-measured 2026-11-06. Maintainer register. A study: nothing is built, and no task is created before the maintainer's go. Trigger: the maintainer's question of 2026-11-05, how knowgov serves the decision whether an application is refactored, sunset, or replaced by another application that fulfils the same business capability, given that applications have a lifecycle and a software quality score (unmeasured, or measured by e.g. SonarQube). Evidence used: knowgov `main` at `8f20af0` (after #319); the register at v0.2.11 (`7f1680c`, decision 0018 approved, 57 nodes, 65 links), as vendored in `demo/register` (task-0155); the committed J-F record `subjects/jef_data_load/record/*/deterministic.json` and its approved `register_map.toml` (163 rows). Measured with the register's own `tools/impact.py` functions (`walk`, `walk_children`, `reached`, the rows `FORWARD`, `REALISERS`, `THREAD`) and a join of the record's `gate_keys` to the map rows; no store, no model call. The same figures held on v0.2.10 (`4149e06`) the day before.*

## Verdict

**Sense, on one condition: knowgov adds the one axis an application portfolio tool lacks, how well what the application does is known, and the register records the decision. Nonsense if knowgov becomes the portfolio tool.** The TIME call (tolerate, invest, migrate, eliminate) weighs business value and technical fitness; the cost that surfaces mid-migration is the behaviour nobody documented. knowgov already reads that per statement and per node (`register_impact` under the `codegen` task class). Holding lifecycle phases, SonarQube scores, cost or volumes, or computing a sunset score, would duplicate LeanIX, Ardoq or ARIS IT Architect and break two contracts: a node file never copies a tool's attribute, and observed state is out (doc-0010, doc-0015 §1).

Two corrections to the question's premise, from the metamodel:
- **Capabilities are realised by processes; applications support processes.** `realizes` is process to capability, `supports` application to process; no link joins an application to a capability. The `realisers` walk (register decision 0012) composes the two.
- **The register's `state` is its approval lifecycle, not the application lifecycle.** `draft → proposed → approved → deprecated → retired` (`lifecycle.toml`) says whether the element is an approved part of the architecture. The operational lifecycle (plan, phase-in, active, phase-out, end of life, with dates) belongs to the system of record. They meet at one point: a decision to sunset is `approved → deprecated`, with a decision record, four eyes and both owners.

An unmeasured quality score is `unknown`, never low: the three-valued answer applies to it as to any key.

## 1. Measured on the public register

**What each application serves, and who else realises it.** The dependants walk from each approved application node, filtered to capabilities; then the `realisers` walk from each of those capabilities; a peer is another application node reached. Peers are split by root application (`parent` climbed within the applications taxonomy).

| Node | Kind | Capabilities reached | Peers, same root | Peers, other root |
|---|---|---|---|---|
| APP-0001 CargoQuote reference implementation | application | none; with `--children` CAP-0002, CAP-0003, CAP-0004 | | |
| APP-0002 QuoteAPI | module | CAP-0004 | none | none |
| APP-0003 TariffEngine | module | CAP-0002 | none | none |
| APP-0004 ScreeningService | module | CAP-0003 | none | none |
| APP-0005 jef-data | application | none; with `--children` CAP-0007, CAP-0008 | | |
| APP-0006 sync | module | CAP-0007 | APP-0008 | none |
| APP-0007 health | module | CAP-0008 | none | none |
| APP-0008 store | module | CAP-0007 | APP-0006 | none |
| APP-0009 collectors | module | none (PROC-0009 realises nothing) | | |

- **No overlap candidate exists on the public register.** The one process supported by two nodes, PROC-0007 *Sync run* (APP-0006, APP-0008), is supported by two modules of one application: complementary, not redundant. A capability map at application-to-capability grain would show two applications on CAP-0007; the register's activity grain and `parent` tell them apart. Each subject has one application, so the rationalisation question has no instance until a register holds two applications on one capability.
- **An application root reaches no capability without `--children`.** Its `supports` links sit on its modules (APP-0001 has none of its own); APP-0005's own links reach PROC-0006 and PROC-0010, which realise nothing. A consumer asking "what does this application serve" states `--children` (decision 0016 point 3).
- **Every realising process has a supporting application.** 5 of 5 approved processes that realise an approved capability (PROC-0002, -0003, -0004, -0007, -0008) are supported by an approved application node. A rule asking for it (§3, P3) would fire nowhere today.

**How well what each application does is known.** The J-F record's `gate_keys` (task class `codegen`) joined to the `register_map.toml` rows that name the application node directly, without a walk; a row naming two application nodes counts for both. Approved / proposed:

| Node | Keys | C | D1 | D2 | D3 | D4 | D5 |
|---|---|---|---|---|---|---|---|
| APP-0005 jef-data | 100 | 100/0 | 100/0 | 96/4 | 96/4 | 100/0 | 99/1 |
| APP-0006 sync | 17 | 17/0 | 17/0 | 15/2 | 17/0 | 17/0 | 14/3 |
| APP-0007 health | 21 | 21/0 | 21/0 | 21/0 | 21/0 | 19/2 | 21/0 |
| APP-0008 store | 35 | 35/0 | 35/0 | 34/1 | 32/3 | 35/0 | 34/1 |
| APP-0009 collectors | 17 | 17/0 | 17/0 | 17/0 | 17/0 | 17/0 | 17/0 |

The recreation experiment is the replacement case in miniature: the application rebuilt from its documents alone. C: gate PROCEED, the rebuild passed the oracle 258 of 258. D3 and D5: gate QUALIFIED, and planted defects reached the code (all three in D3, two of three in D5), concealed by the arm's own oracle. D1: PROCEED with wrong diagrams, nothing reached the code. D4: the changed expectation was invisible to the store and reached the code. **Readiness is readable per application and per state of the documents, and the gate is a necessary signal, not a sufficient one.** One synthetic subject, 163 keys, the maintainer's own program: not a portfolio.

## 2. Sense and nonsense

| Use | Verdict | Why |
|---|---|---|
| Knowledge readiness as a third axis beside business value and technical fitness | **Sense** | Migration cost is dominated by undocumented behaviour; the gate reads it per key with provenance (§1) |
| "Document before you decommission": a migrate or eliminate candidate with keys below verified is routed to its owning unit before the switch-off | **Sense** | The gate's `owner` and `route` (task-0102), the questionnaire per unit (task-0043) |
| The capability's verified keys as a replacement's acceptance list; its unknown keys as the discovery backlog | **Sense** | The keys land on capabilities, processes and entities as well as on the application; they outlive it |
| The TIME call recorded in the register: a decision record, `deprecated` approved by both owners, an expiring exception for the phase-out | **Sense** | Approval is a file-state change; exceptions expire |
| Re-verification after the switch | **Sense**, built | `register_change` (task-0122) stales the keys resting on a deprecated node and marks what was built on them suspect, until verified again against the replacement |
| Lifecycle phases and dates, SonarQube metrics, cost, volumes in a node file | **Nonsense** | Two records; the register's contract |
| The same read at decision time from a dated export of the system of record | Sense, later | The connector's pattern, `exports/<system>/<date>/` with a MANIFEST; read, never copied into a node |
| A computed sunset or risk score | **Nonsense** | It hides `unknown`; coverage is reported with its denominator, never a percentage to pass. The heuristic-model study of 2026-11-05 (doc-0024, reserved; its text not on `main` at `8f20af0`), as its session reported it, kept counts of application concentration and single points of failure, parked weights and scores, and rejected a single risk score |
| A SonarQube score as a verification of knowledge | **Nonsense** | Code quality says nothing about whether behaviour is documented; at most received, flagged evidence on the pattern of task-0053, parked |
| Overlap reported as a finding | **Nonsense** | Two applications on one activity are a candidate; `supports` does not say which part of the activity each covers |
| Portfolio dashboards, roadmaps, TIME quadrants in knowgov | **Nonsense** | doc-0017's threat: the edge is the epistemic layer alone |

## 3. Fit/gap per question

| Question | What exists | Fit/gap |
|---|---|---|
| What does this application serve? | Dependants walk; `register_impact` (task-0111) with `children` (task-0118) | **Fit**, with `--children` for an application root (§1) |
| Who else realises the same capability? | `realisers` walk (decision 0012), per capability | Fit per capability. **Gap, small: P1**, the two named walks composed (application → capabilities by dependants → applications by realisers), peers split by root. Two walks composed, not a row walked both ways (doc-0011's rejection stands) |
| How well is what it does known? | `register_impact` with a held scenario: each landed key's level, stale, lapsed, owner, route | Fit per node; needs a loaded store. **Gap, small: P2**, a roll-up over every application node, counts with denominators, no score |
| Sunset: what the register refuses | Deprecating a node fails every approved link referencing it (`check_register.py`) | **Fit** |
| Sunset: a realising process left with no application | C1 to C3 ask step → process, capability → process, process → diagram | **Gap: P3**, a register proposal: a coverage rule, an approved realising process supported by an approved application, its exception for a process manual by design; the exception's `expires` is the phase-out's deadline. Fires nowhere today (§1) |
| Sunset: what it does to the knowledge | `register_change` (task-0122), `gate_cli --register-previous` | **Fit**. Risk: the dependants walk with descent stales product-level keys when one module is deprecated; measure on the pilot before narrowing |
| Replace: the target read as if approved | `proposal_impact` (task-0130, -0131): additions only; branch mode lists a link changed in place as `not_read` | Partial. **Gap, medium: P4**, a replacement overlay: additions and withdrawals read together (new `supports` links hypothetical, the old application and its links deprecated, hypothetical), coverage and reach before and after, the keys inherited by the target |
| Replace: by slice | `proposal_impact` `slices` (task-0152, doc-0022 K1), by the `THREAD` walk and A1 | Fit for an addition: a replacement's new `supports` links fall into the slices of the journey steps their processes support. P4 reuses the slice map |
| Trace a journey step down to its applications | `thread` walk (register decision 0018, approved, vendored at v0.2.11) | Related, not this question: from an application the `THREAD` rows follow `manages` only; APP-0008 reaches ENT-0008 and ENT-0009, APP-0006 nothing |
| Can the replacement be built from what is documented? | The `codegen` gate; the J-F degradation record | **Fit** as a necessary condition (§1) |
| Lifecycle phase, TIME classification, cost, SonarQube | None | **Out** of node files. **P5, parked**: read at decision time from a dated export, the connector's pattern (task-0063's route, decision-0010's MANIFEST), joined by register id; prerequisites task-0123 (the register id stamped into the tool) and, for SonarQube's project key, task-0125 (an approved application-to-repository link) |
| Code to application | `code_map.toml` (task-0050), `code_path` (task-0143) | **Fit**: a hand-written file's application, cited keys and ledger entry |

## 4. Opportunity canvas

| Block | Content |
|---|---|
| Users and customers | Portfolio and EA leads running a rationalisation; application and capability owners; delivery leads of a migration; an agent drafting a migration plan |
| Problem | TIME calls weigh business value and technical fitness. What nobody knows the application does surfaces mid-migration, as rework or as a defect carried into the replacement (D3, D5). A portfolio tool shows that an application supports a capability, not whether its behaviour is documented, verified and current |
| Solution | A read-only readiness reading per application: what it serves (with `--children`), its peers on the same capabilities split by root, the keys it reaches with their levels, owners and routes, counted with denominators (P1, P2). A replacement what-if that reads additions and withdrawals together (P4). The decision lands in the register as a state change with its record and an expiring exception (P3). Lifecycle dates and quality scores stay in their systems, read from a dated export when needed (P5) |
| Value | Migration risk visible before the call; the discovery backlog sized by unknown keys; owners told by route; re-verification against the replacement enforced by what exists (task-0122) |
| Metrics | Share of each application's keys at verified or better, with denominator; unknown keys per migrate or eliminate candidate before and after capture; post-switch defects traced to keys below verified; days from the TIME call to an approved deprecation pull request |
| Channels | MCP: `register_impact`, `register_nodes` filtered to the applications taxonomy, `code_path`. Beside a portfolio tool's own MCP server (LeanIX's is generally available, doc-0012), an agent joins the two by register id: no integration and no content write-back |
| Cost | P1, P2: small, the register's functions and the gate's report composed. P3: a register decision, a rule, an exception kind. P4: medium. **The dominant cost is coverage:** an application has keys only once its documents are loaded as a subject; today two subjects and nine application nodes. Any other application reads `unmapped`, never `unknown` |
| Risks | Readiness read as quality, or as a verdict on the application. `unmapped` read as `unknown`, then as bad. Drift into a portfolio tool. Staling too broad after a module's deprecation |
| Unfair advantage | Levels per statement with provenance, and a record (J-F, D1 to D5) in which the gate's verdict tracked whether a rebuild carried defects |

## 5. SWOT

- **Strengths.** Every answer comes from the register's own walks and the gate's own report: no new semantics. The keys land on capabilities, processes and entities, so they survive the application they describe. Re-verification after a switch is already built (task-0122). The J-F record shows the gate's verdict tracking whether a rebuild carried defects. *Response:* compose what exists; P1 and P2 add no walk row and no level.
- **Weaknesses.** The public register has two applications and no overlap, so P1 has no instance to show. Readiness exists only where a subject is loaded; every other application is `unmapped`. Staling after a module's deprecation may be broad. One maintainer. *Response:* report `unmapped` plainly; measure P1 and the staling breadth on the pilot's register before building.
- **Opportunities.** Rationalisation is a portfolio lead's recurring question and a visible lighthouse case (m-8, decision-0006): "document before you decommission" is a sentence a buyer repeats. A portfolio tool's own MCP server beside knowgov's lets an agent join both by register id with nothing built. *Response:* offer it at the pilot as a reading over `register_impact`, not as a feature.
- **Threats.** LeanIX, Ardoq and ARIS IT Architect own TIME, lifecycle and fitness; a knowgov score would compete and lose. A readiness count can be read as a verdict on the application or as its quality. Lifecycle and quality data pull towards copying attributes. *Response:* no score, no rank; counts with denominators; lifecycle and quality only as P5, read from a dated export.

## 6. Proposals

Mapped to what exists; none has a task id.

1. **P1, application peers** (small, new): `register_impact` or a CLI composes the dependants walk to capabilities and the `realisers` walk back, peers split by root application, every peer a candidate. Builds on decisions 0012, 0014, 0016.
2. **P2, readiness roll-up** (small, new): `register_impact` over every node of the applications taxonomy under one task class and `as_of`; per node the keys by level and finding, with denominator; no score, no rank.
3. **P3, a coverage rule for realising processes** (register proposal, new): an approved process that realises an approved capability is supported by an approved application, or carries an exception (manual by design, or a phase-out with `expires`). Fires nowhere on v0.2.10.
4. **P4, a replacement overlay in `proposal_impact`** (medium, new): withdrawals read beside additions, each withdrawal as hypothetical as each addition; reuses task-0152's slice map, so the slices a replacement leaves and the slices it joins are listed side by side.
5. **P5, lifecycle and quality read from a dated export** (parked, new): the connector's pattern, joined by register id; after task-0063, task-0123 and, for SonarQube, task-0125; on an adopter's ask at the pilot (task-0062).

## 7. For the maintainer

- **Whether to build P1 and P2 before the lighthouse.** Recommendation: no. The public register has no overlap and two applications; build on the pilot's first rationalisation question, below task-0141 and the lighthouse prerequisites.
- **Whether to propose P3 to ieam-register now.** Recommendation: yes, as a proposed decision only; it is cheap, fires nowhere today, and gives a sunset an expiring deadline in the register's own terms.
- **Whether P4 is tasked now that task-0152 is built.** Recommendation: not before the pilot's first replacement question; it is the only medium proposal and the public register has no replacement to read.
- **Whether lifecycle and quality ever enter knowgov.** Recommendation: only as P5, read from a dated export, never in a node file and never as a score.
