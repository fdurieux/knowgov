---
id: doc-0022
title: >-
  Slicing an initiative into a backlog: the register's chain as the story map,
  the gate as the definition of ready. Sense and nonsense, fit/gap, opportunity
  canvas
type: specification
created_date: '2026-11-05T22:32:00Z'
updated_date: '2026-11-05T22:33:00Z'
tags:
  - brief
  - canvas
  - fit-gap
  - register
  - mcp
---
*2026-11-05. Maintainer register. A study: nothing built, no task opened. K1 to K5 are proposals with no ids; the coordinating session mints them on the maintainer's go. Trigger: the maintainer's ask of this date: the sense and nonsense of using knowgov to slice a change (an initiative, an epic) into a prioritised backlog that covers every required artefact (journey, business capability, application and so on), for kanban or sprints; fit/gap; an opportunity canvas. Read on `main` at `581f3b4`, with the register at v0.2.10 (`4149e06`, the vendored `demo/register` and the ieam-register checkout at the same commit). Executed: `harness/proposal_impact.py tools/fixtures/proposal_contract_quote.json --no-store`; ieam-register `tools/check_register.py`; a read-only script over the register's `load_register` that follows each product's journey steps through approved `is_supported_by`, `realizes`, `supports`, `crud` and `manages` links, committed nowhere. Not read: key levels (no store; rdflib is not installed in the session), real register names, a tracker's export. The session's canvas page (https://claude.ai/artifact/7kwwVQG1Lsdy7Qakepsnjv, private) is a view; this doc is the record. Synthetic content only.*

## Verdict

**Sense, as long as knowgov reads and gates; nonsense if it holds, ranks or estimates the backlog.**

- **The intake read exists.** `proposal_impact` (task-0130 to task-0132) reads an initiative as an overlay, as if approved, and reports what slicing starts from:
  - placement;
  - C1, C2 and C3 before and after, with denominators;
  - reach from every reused node;
  - what the new product rests on;
  - the keys of reused nodes, with levels when a store is held;
  - approvals per unit.

  Its gaps are a backlog's first items. The gate is a definition of ready per task class: `design` for discovery, `codegen` for build. `trace`, `--register-previous` and the review lapse send work back when the knowledge under it changes.
- **The register's chain is a story map's backbone.** A journey's steps are the columns. A step's thread (step → process → capability, with the supporting applications and the entities touched) is a vertical slice. A capability the product requires that no step's thread reaches is an enabler, or the sign of a missing step or link.
- **Nothing groups or orders the report.** No named register walk follows a step's thread down to applications and entities:
  - the `dependants` walk from a step reaches its process, capability, product and sibling steps;
  - `realisers` starts from a capability;
  - no walk goes forward along `crud` or `manages`.

  Composing the thread in knowgov would be a second walk semantics, which doc-0017 §6 and `proposal_impact`'s docstring exclude. So the register comes first (K2), then knowgov's grouping (K1).
- **Out, by decision.** knowgov writes no backlog item (decision-0008; doc-0014 decision B: intent and plan stay in the tracker). The register gets no `initiative` or `epic` kind. Value, cost of delay, effort and capacity stay the product owner's and the team's. knowgov informs three of WSJF's five inputs and decides none.
- **Method-neutral.** Kanban or sprint changes where the gate is called (a column policy, or the sprint's ready and done definitions), not what it reads.

## 1. The question, as a prompt

> Given an initiative described by partial artefacts, can knowgov, with the register it reads:
> 1. decompose it into vertical slices that cover every register element and coverage gap it entails;
> 2. say per slice what is new, reused, changed or missing, and how ready the knowledge under it is;
> 3. give the inputs to its order (risk, dependencies, approvals, lapses) without ranking by value or estimating;
> 4. gate the board's transitions under kanban or sprints, without becoming the backlog, the register's author or the tracker?

## 2. What exists, verified

**The intake read on doc-0017's worked example.** The overlay is 6 nodes, 6 links and 4 reused nodes: `PRD-0006` *Contract freight quote*, new capability `CAP-0009`, journey `JRN-0012` with steps `JRN-0013` to `JRN-0015`.

| Output | Value |
|---|---|
| C1 | 7/8 → 8/11; uncovered `JRN-0014`, `JRN-0015` |
| C2 | 5/5 → 5/6; uncovered `CAP-0009` |
| C3 | 5/5 → 5/5 |
| Placement | one warning (`JRN-0012` has no journey family); six infos, "in no tool yet" (no `[source]`) |
| Candidates | D1 for the three `requires` links and `JRN-0013 is_supported_by PROC-0002`; D3 `JRN-0013` "same as JRN-0002"; D4 pools for `JRN-0014`/`JRN-0015`, `PROC-0002/0003/0004`, none chosen |
| Reach | CAP-0002, CAP-0003 and CAP-0004 each gain `JRN-0012`, `PRD-0006`; PROC-0002 gains `JRN-0012`, `JRN-0013`, `PRD-0006` |
| Rests on | `PRD-0006` ← CAP-0002 (PROC-0004, APP-0003), CAP-0003 (PROC-0003, APP-0004), CAP-0004 (PROC-0002, APP-0002), CAP-0009 nothing (gap) |
| Keys of reused nodes | CAP-0002 13, CAP-0003 16, CAP-0004 11, PROC-0002 11, overlapping, of the subject's 36; levels not read (`--no-store`) |
| Unmapped | all six new nodes, by construction |
| Approvals | ORG-0001: five nodes, six links. ORG-0002: `CAP-0009` and the four `requires` links (cross-domain) |

**The slice map, grouped by hand** from that report and the register's approved links (what K1 would compute):

| Layer | Slice `JRN-0013` | Slice `JRN-0014` | Slice `JRN-0015` | Enablers (required, on no step's thread) |
|---|---|---|---|---|
| Step | new | new | new | none |
| Process | reused `PROC-0002` | C1 gap; D4 pool, none chosen | C1 gap | C2 gap: nothing realises `CAP-0009` |
| Capability | reused `CAP-0004` | unknown | unknown | new `CAP-0009`; reused `CAP-0002`, `CAP-0003` |
| Application | reused `APP-0002` QuoteAPI | unknown | unknown | `APP-0003`, `APP-0004`; none for `CAP-0009` |
| Entity | reused `ENT-0002`, `ENT-0003` | unknown | unknown | `ENT-0004` (pricing) |
| Knowledge | PROC-0002 11 keys, CAP-0004 11 | unmapped | unmapped | CAP-0002 13, CAP-0003 16; `CAP-0009` unmapped |
| Owners | ORG-0001 | ORG-0001 and the new process's owner | as `JRN-0014` | ORG-0002; cross-domain `requires` |

Cross-cutting, not slices:
- the register pull request for 6 nodes and 6 links, under four eyes;
- `JRN-0012`'s journey family;
- modelling the six elements in the system of record.

The study reads `JRN-0013` as the walking skeleton (almost all reuse), and `JRN-0014`, `JRN-0015` and `CAP-0009` as discovery first. That reading is the study's, not an output (§9, item 4).

**The same alignment on the approved register, with no proposal.** Each finding is a question for an owner, not an error.

| Product | Requires | Its journey's steps reach | Finding |
|---|---|---|---|
| `PRD-0002` instant quote | CAP-0002, CAP-0003, CAP-0004 | CAP-0004 (JRN-0002 → PROC-0002), CAP-0002 (JRN-0003 → PROC-0004) | `CAP-0003` *Screen a shipper* is on no step's thread. Its realiser PROC-0003 is an activity of PROC-0001 that no step is supported by, though JRN-0003 shows the refusal screening produces |
| `PRD-0004` seam frame | CAP-0007 | CAP-0007, CAP-0008 | `CAP-0008` reached, not required |
| `PRD-0005` daily run outputs | CAP-0007, CAP-0008 | no journey concerns it | slices come from the process axis |

The register check on the same commit: 57 nodes, 65 links, 0 errors, 7 warnings; C1 7/8 (1 excepted, EXC-0001), C2 5/5, C3 5/5. No coverage rule asks for the alignment above.

**What the walks cover** (`tools/impact.py`):

| Walk | From a step | What it lacks for a slice |
|---|---|---|
| `FORWARD` (`dependants`) | `is_supported_by` to the process, then `delivers`, `realizes`, and `is_supported_by` inverse to sibling steps | applications and entities: `crud` and `manages` are walked inverse from information only |
| `REALISERS` (decision 0012) | nothing: it starts at a capability, then `realizes` inverse and `supports` inverse | entities |

A slice therefore needs a third named walk.

## 3. Fit/gap

| What slicing needs | knowgov today | Fit/gap |
|---|---|---|
| Inventory of what the initiative adds, reuses or changes, across the seven taxonomies | `proposal_impact` overlay (nodes, links, reused `as_is`/`changed`); `register_nodes` for the ids to start from | Fit |
| Placement: kind, parent, owner, glossary | `check_nodes`, `check_glossary`; no `[source]` is "in no tool yet" | Fit |
| Artefacts the rules demand and the initiative lacks | C1, C2, C3 before and after, with denominators | Fit |
| Links from new elements to existing ones | D1 to D4; D4 a pool never chosen; a model's candidates parked (doc-0017 candidate 4) | Partial |
| What the change touches outside the initiative | reach before and after per reused node, `changed` flagged | Fit |
| What the new product rests on | `requires` targets plus `realisers` | Fit |
| Readiness of each piece's knowledge | reused nodes: levels per task class and `as_of` with a store; new nodes unmapped by construction | Partial |
| Grouping into vertical slices | nothing groups; no named walk follows a step's thread to applications and entities | **Gap**: K2a, then K1 |
| Enablers: required capabilities on no step's thread | no rule; measured above (`PRD-0002` → `CAP-0003`) | **Gap**: K2b, then K1 |
| Order between items | realisers chain and approval routes exist; no order emitted; lifecycle puts node approval before link approval | Partial: K1 |
| Who must approve or answer | approvals per unit; key `owner`, `route`, `closer` (task-0102, task-0110) | Fit |
| Documents per slice (BPMN, API contract, Gherkin, user story) | C3 asks for a diagram of record; `instance/kinds.toml` 20 kinds with the pre-load lint; no map from node kind to the documents a slice owes | Gap: K4 |
| The backlog covers the initiative | nothing reads a tracker; items would cite register ids | Gap: K3 |
| Definition of ready | `gate_cli` exit 0/1/2, PROCEED/QUALIFIED/BLOCKED per task class; the hook at plan, spec commit, push (task-0102) | Fit |
| Definition of done, re-entry | `trace register`/`check` (suspect, drift, missing, unmapped); `--register-previous` (task-0122); review lapse (decision-0005) | Fit |
| Time criticality inside a sprint | the gate `--as-of` the sprint's last day lists what lapses before it ends | Fit |
| User-story quality (INVEST, acceptance criteria) | the `user-stories` kind has no gate-capable tool | Out (Legible's row) |
| Value, cost of delay, effort, capacity, WSJF | none | Out, by design |
| Writing epics and stories | none; decision-0008, doc-0014 decision B | Out, by decision |

## 4. Sense and nonsense

**Sense.**
- The register as the story map's backbone: journey, stage and step are the columns; a step's thread is its slice.
- `proposal_impact` before slicing, with its gaps as the first items. A C1 gap is discovery for a supporting process. A C2 gap is discovery for a realising process and its application.
- The gate as the definition of ready, by task class.
- `trace`, the lapse and `--register-previous` as the signal that sends a card back.
- The owners and routes read before a slice is committed, so approvals start early.

**Nonsense.**
- knowgov holding the backlog, or a register taxonomy for initiatives or epics. Work items are transient, register nodes durable: two records of the same work, against "one record per thing".
- knowgov ranking by value or estimating: it holds no value, cost or capacity.
- "All required artefacts" as a claim. Completeness holds against C1 to C3, the metamodel's kinds and the declared keys only, and is reported with its denominator.
- A D4 pool choosing a step's process: a candidate never closes a gap.
- Slicing by layer (all capabilities, then all applications). The register makes it easy, and it is the anti-pattern; the thread is vertical.
- Planning labels ("walking skeleton", "discovery first") in a report. They are judgements, not register facts.

## 5. Priority: who supplies which input (WSJF)

| Input | Owned by | What knowgov adds |
|---|---|---|
| Business value | product owner | nothing |
| Time criticality | product owner | lapses before the sprint's end (`--as-of`); existing products and journeys the change reaches |
| Risk reduction, opportunity enablement | team, informed | keys at `absent`, `declared_gap`, `disputed` as spikes; enablers that unblock several slices |
| Job size | team | a proxy only: new against reused elements, gaps, owning units per slice; never an estimate |
| Dependencies | team | the realisers chain; node before link approval; a cross-domain link waits for both owners |

## 6. Kanban or sprint: where knowgov is called

| Transition | Kanban (column policy) | Sprint (event) | knowgov |
|---|---|---|---|
| Intake → sliced | entry to "Sliced" | refinement | `proposal_impact`, then K1 |
| Discovery → design-ready | a WIP-limited discovery lane | refinement | gate under `design`; questionnaires per owner for the blocking keys |
| Ready for build | the "Ready" column's policy | definition of ready at planning | gate under `codegen`, `--as-of` the sprint's end |
| In build | pull | the sprint | the Claude Code hook at spec commit and push |
| Done | done policy | definition of done at review | `trace register` and `check`; pre-load lint of the documents; the register pull request approved |
| Reopened | back to Ready or Discovery | next sprint's backlog | a suspect, stale or lapsed finding |

## 7. Opportunity canvas

| Block | Content |
|---|---|
| Users and customers | Product owners and delivery leads cutting an initiative into epics, features and stories. Architects at intake. Capability and process owners asked to approve reuse or answer a questionnaire. Teams pulling work or committing to a sprint. An assistant drafting the backlog over MCP |
| Problem | Slicing happens in workshops, on slides and sticky notes. The architecture under each slice is checked at approval, if at all, after the backlog is committed. Missing artefacts surface late: a step no process supports, a required capability nothing realises, a process with no diagram of record. Readiness is guessed. Cross-domain work stalls on approvals nobody routed |
| Today | Story mapping on the journey by hand. The EA tool's impact analysis (ARIS, LeanIX, Ardoq) shows the model, not the quality of what is known. In knowgov: `proposal_impact` (CLI, MCP, branch mode), `register_nodes`, `register_impact`, the gate and its hook, `trace` |
| Solution | The initiative as an overlay, read by `proposal_impact` as today. K2's named walk and alignment rule in the register. K1's slice map in the report: slices, enablers and cross-cutting items, each cell new, reused, changed or gap, with owners and key levels. The gate at the board's transitions. The tracker writes the items, through its own connector, each citing register ids |
| Value | Gaps found at slicing, not at approval. Completeness stated against C1 to C3 and the declared keys. A walking skeleton chosen on evidence: the slice that reuses the most verified knowledge. Discovery separated from build by the gate, not by opinion. Owners of existing products warned before their product changes |
| Metrics | Share of overlay elements and gaps cited by at least one item (K3). Gaps found at slicing against those found at approval or in build. Share of slices PROCEED or QUALIFIED under `codegen` at planning or at "Ready". Items reopened by a suspect, stale or lapsed finding. Days from intake to an approved register pull request (doc-0017) |
| Channels | MCP in Claude Desktop and Claude Code, beside the tracker's connector. The CLI and `instance/ci/proposal-impact.sh` on a register pull request. The hook (task-0102). The lighthouse pilot's architects (task-0062) |
| Cost | K2: one register decision with two parts and their tests, then a re-vendor here; small. K1: a report section in `proposal_impact` and its schema, additive, so a minor version while 0.x (decision-0003) with a line under `## Unreleased`; small to medium. K3: medium, at the pilot |
| Risks | Drift into a work-management tool: knowgov never stores or writes an item. The map read as a plan: it is a decomposition, and the order of value is the product owner's. Products with no journey (`PRD-0005`): the process axis. SAFe's "Capability" work item against the register's `CAP-`: the glossary binds register names only. 57 synthetic nodes: candidate precision unmeasured on real names. New nodes have no keys until a subject declares them |
| Unfair advantage | The gaps come from the register's approved rules, with denominators, not from the room's memory. Every reused element arrives with statement-grain epistemic levels and an owner to route to. Deterministic and read-only: the same overlay gives the same map, and nothing becomes record without a register pull request |

## 8. Candidates

| # | Candidate | Disposition |
|---|---|---|
| K2 | **Proposal to ieam-register**, one decision with two parts. (a) A third named walk, `thread`: from a step or touchpoint, `is_supported_by` forward. From a process: `realizes` forward, `supports` inverse, `crud` forward. From an application: `manages` forward. `parent` adds starts as decision 0014, so an end-to-end process brings its activities. (b) An alignment rule at warning level: a capability that an approved product `requires` and that no approved step of a journey `concerns`-ing the product reaches through (a), unless an unexpired exception covers it; a product no journey concerns is reported as such, not failed. Evidence: §2 (`PRD-0002` → `CAP-0003`; `PRD-0004`; `PRD-0005`) | **Register proposal**, small. The register decides; nothing is opened there from here |
| K1 | **Slice map in `proposal_impact`'s report**: one slice per new or changed step, by K2's walk; enablers by K2's rule; cross-cutting items (the register pull request, placement findings, "in no tool yet"). Every cell carries status (new, reused, changed, gap), owners and key levels under one task class and `as_of`. Facts only, no planning labels. Every overlay element appears exactly once, with the denominator shown. On the doc-0017 fixture: the three slices and the enabler group of §2 | **Build** on the maintainer's go, after K2 is vendored. Small to medium. Behind task-0141 and the lighthouse prerequisites unless the pilot asks |
| K3 | **Backlog coverage check**: a neutral, schema-pinned file of work items with the register ids and keys each cites, converted on the client's side from the tracker. Reports overlay elements and gaps no item cites, and items citing ids that do not exist. The pattern of doc-0011's process-mining file: knowgov names no vendor | **Park** until the pilot names its tracker (task-0062) |
| K4 | **Documents per node kind** as instance policy: a step owes acceptance scenarios, a module an API contract, a realising process its diagram of record (C3 already asks for it). The definition of done per slice, read with the pre-load check | **Park**; study at the pilot |
| K5 | **The intake-to-backlog sequence in the MCP server's instructions**: `proposal_impact`, the slice map, the gate per slice; the tracker's connector writes | **Document**, after K1 |
| × | knowgov writing items; an `initiative` or `epic` taxonomy in the register; a value or effort score; a model choosing D4's process; knowgov composing the thread from raw links | **Reject** |

## 9. For the maintainer

1. **Send K2 to ieam-register?** Recommended: yes, as one proposed decision with both parts. It is the precondition for K1 without a second walk semantics, and its evidence is in §2.
2. **K1's priority.** Recommended: after K2 is vendored, below task-0141 and the lighthouse prerequisites. It is the intake demonstration for the pilot's architects, not a blocker.
3. **The slice axis.** Recommended: the journey step by default, the end-to-end process for a product no journey concerns.
4. **Facts only in K1's report.** Recommended: yes. "Walking skeleton" and "discovery first" stay the reader's judgement, as §2's reading is this study's.
5. **K3 and K4.** Recommended: park both to the pilot, where a real tracker and real document kinds exist.
