---
id: doc-0017
title: >-
  Impact of a proposed addition: a new product, capability and journey read
  against the register before approval. Opportunity canvas, fit/gap, SWOT
type: specification
created_date: '2026-11-04T20:02:00Z'
updated_date: '2026-11-04T20:03:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - brief
  - mcp
  - register
---
*2026-11-04. Maintainer register. A study: nothing is built, and no task is created before the maintainer's go. Trigger: the maintainer's ask of this date, to determine the impact of creating a new element in the ontologies (a new product that partly reuses existing capabilities and needs a new one, with a customer journey partly based on an existing journey), the known artefacts given to knowgov, perhaps over MCP, and knowgov linking the other elements and naming the gaps. Evidence used: knowgov `main` at `1f14be0` (after #204); the register at v0.2.9 (`4bb0923`, decision 0016), as vendored; a worked example run on two scratch copies of the register and once in memory (§2), committed nowhere. Settled in the session: the outputs are this doc's opportunity canvas, fit/gap and SWOT of the capability; both input routes (a proposal held in the call, a register branch); deterministic link candidates first, a model's second; journey reuse left open (§5). doc-0016 (scenario runs over MCP, on another branch the same day) also proposes a read-only tool; the two are independent.*

## Verdict

**Most of the answer exists already. What is missing is a way to read a proposal as if approved without approving it.** The register's checker and walk already compute the gaps and the reach the question asks for. Written as approved, the worked example's proposal raises C1 on the two new journey steps that nothing supports and C2 on the new capability that nothing realises. The walks from CAP-0002 and PROC-0002 then reach the new product and journey. Written as draft, the only honest state for a proposal, it is invisible: the checker passes, coverage counts nothing, and every walk reports the new links withdrawn (decision 0007). Both functions take the register as a dict, so the tagged register plus the proposal held in memory gives the same result with nothing written. The read-only stance holds (doc-0013 candidate 9, doc-0015 §1).

**Build one evaluator behind a further read-only MCP tool and a CLI** (candidates 1 to 3):
- the proposal is an overlay, held in the call or taken from a register branch's diff against its base;
- the register's own functions read it as if approved, and every overlay element and edge is marked hypothetical;
- deterministic link candidates;
- the keys the reused nodes carry, with their gate levels;
- what each owning unit must approve or answer.

Park a model's candidates until the deterministic ones have been measured on a real register (candidate 4). Send one proposal to the register: list the export ids that no node carries (candidate 5). Journey reuse is the maintainer's call; §5 recommends no new type for now. The knowledge side of a *new* element is empty by construction: no subject has asked about it yet, so it is reported as unmapped, not unknown.

## 1. The question, as a prompt

> Given a proposed initiative described by partial artefacts, can knowgov, with the register it reads, (1) place the new elements in the register's taxonomies, (2) propose the typed links that join them to existing approved nodes, (3) report per element what is reused as is, reused with change, new, missing or unknown, and (4) report what the change touches among existing nodes and the knowledge keys that rest on them, without becoming the author of the register or of the content?
>
> Inputs: the existing journey (register id or diagram of record), the reused capabilities, the new capability at name-and-parent grain, the new journey. Outputs: placement; proposed links, each with type, rationale, basis (`inferred` when matched or proposed by a model, `authored` when the input stated it) and the owners who approve it; fit/gap with denominators (C1, C2, C3, unregistered entities, missing owners; inherited keys `unknown`, `documented_absent`, lapsed or stale; reused nodes withdrawn; accepted gaps as expiring exceptions); the impact on what exists (each reused node's dependants and keys, with level and owner); the route per owning unit. Constraints: the MCP server only reads; the register changes by pull request under four eyes; metamodel changes are proposals to ieam-register; synthetic data only.

## 2. What exists, verified

**The worked example.** Synthetic, on the public CargoQuote register (57 nodes, 65 links). The new product PRD-0006 *Contract freight quote* (product under PRD-0001, owner ORG-0001) `requires` CAP-0002 *Price a shipment*, CAP-0003 *Screen a shipper* and CAP-0004 *Validate a quote request* (reused, owner ORG-0002). It also requires CAP-0009 *Check a shipper's credit* (new, name and parent CAP-0001 only, owner ORG-0002). The new journey JRN-0012 *Get a contract quote* `concerns` PRD-0006. Its step JRN-0013 *Submit a quote request* copies JRN-0002, so it takes JRN-0002's support, `is_supported_by` PROC-0002. Its other two steps are new: JRN-0014 *Negotiate the terms* and JRN-0015 *Accept the contract*. In all: six nodes and six links.

| Read | Checker | C1 | C2 | C3 | Walk from CAP-0002 reaches | Walk from PROC-0002 reaches |
|---|---|---|---|---|---|---|
| Tagged register | 0 errors, 7 warnings | 7/8, 1 excepted | 5/5 | 5/5 | JRN-0001, PRD-0002, PROC-0001 | CAP-0004, JRN-0001, JRN-0002, PRD-0002, PROC-0001 |
| Proposal as `draft` files | 0 errors, 8 warnings | 7/8 | 5/5 | 5/5 | unchanged; the link to PRD-0006 listed withdrawn | unchanged; JRN-0013 and PRD-0006 listed withdrawn |
| Proposal as `approved` files | **3 errors**: C1 JRN-0014, JRN-0015; C2 CAP-0009 | 8/11, 2 uncovered | 5/6, 1 uncovered | 5/5 | + JRN-0012, PRD-0006 | + JRN-0012, JRN-0013, PRD-0006 |
| Tagged register + proposal in memory, read as approved | `check_coverage` only | 8/11 | 5/6 | 5/5 | as above | as above |

The draft run's eighth warning is JRN-0012's missing journey family. The in-memory read calls `register.load_register`, then adds the six nodes and six links to the dict. It calls `check_register.check_coverage` and `impact.walk`/`impact.reached` on the result. No file is written.

**What the new product rests on has no walk.** `FORWARD` follows `requires` only inverse (capability to product), so from PRD-0006 the dependants walk reaches JRN-0012 alone. The upstream answer can be composed: take the product's `requires` targets, then run the `realisers` walk (decision 0012) from each. CAP-0002 → PROC-0004 → APP-0003; CAP-0003 → PROC-0003 → APP-0004; CAP-0004 → PROC-0002 → APP-0002; CAP-0009 → nothing, the C2 gap again.

**Inherited knowledge.** `register_impact.landed_rows` over `subjects/cargo_quote/register_map.toml`: 28 of the 36 keys name a reused node (CAP-0002 10, CAP-0003 13, CAP-0004 8, PROC-0002 8, overlapping). Their owners are ORG-0001 and ORG-0002. With a scenario held, `register_impact` gives each key its gate level under a task class and an `as_of` (task-0120). The levels were not read here, because no store was loaded. The new nodes have no row in any map and no statement: they are unmapped.

**Placement.** `check_nodes`, `check_relationships` and `check_glossary` also take the dict. Two things raise no finding. None of the six nodes carries a `[source]` block, and the checker accepts that. JRN-0013 repeats JRN-0002's name, and the checker compares no names across nodes.

**Route.** PRD-0006 and JRN-0012 to JRN-0015 are ORG-0001's; CAP-0009 is ORG-0002's. The four `requires` links cross from ORG-0001 to ORG-0002. The register's README asks for both owners' approval on a cross-domain link. `approval.by` holds one name, and the checker checks for neither.

**Input routes.**
- The MCP server has five read-only tools and one register per process (`KG_REGISTER`, through `cadence.register_root`).
- `register_impact.source` reads a checkout's git when there is no `SOURCE.md`, so a branch checkout already serves. Its draft elements are then withdrawn, as above.
- `tools/connector.py` lands an export, and the register's `tools/reconcile.py` lists the ids added since the previous export and the stale nodes. It does not list the export ids that no register node carries, which is where a new element modelled in ARIS first appears.

**Journey reuse.** No relationship type joins two journeys, and a step has one `parent`. Reuse shows only through shared processes. Once JRN-0013 `is_supported_by` PROC-0002, the walk from PROC-0002 reaches both JRN-0002 and JRN-0013.

## 3. Fit/gap against the five outputs

| Output | Today | Fit/gap |
|---|---|---|
| 1. Placement: kind, parent, owner, glossary | `check_nodes`, `check_glossary` on a dict | Fit: the functions exist. Gap: no entry point for an overlay |
| 1. A provisional id | ids are minted in the register, never reused | Gap, design: the call names provisional ids; the evaluator assigns the next free id per prefix in memory and reports under the provisional one; a register pull request mints |
| 1. No source of record yet | a node without `[source]` passes | Gap, small: the overlay reports "in no tool yet" |
| 1. A copied element | names not compared across nodes | Gap, small: the name match (D3 below) is the signal |
| 2. Deterministic link candidates | none | **Gap**: candidate 3 |
| 2. A model's candidates | `arms.endpoint()` serves the arms' code tasks; no link prompt | Gap, second: candidate 4 |
| 2. Who approves each link | owners known at both ends | Fit, computed. Register side noted: one `approval.by`, not checked (§7) |
| 3. C1, C2, C3 | `check_coverage` gives exactly them once the overlay is read as approved | **Fit**; the gap is only the reading |
| 3. Entity read or written, not registered | `crud`, `manages`; no coverage rule asks for one | Partial: reported only when the input names entities |
| 3. Element without an owner | `owner` required | Fit |
| 3. Keys the reused nodes carry, with levels | `register_impact` per node; 28 of 36 in the example | Fit per node. Gap: aggregated over the overlay |
| 3. Keys a new element needs | no subject has asked about it | Out until a subject declares keys; reported unmapped, never `unknown` |
| 3. Reused node deprecated, lapsed or stale | the walk's withdrawn; the gate's `lapsed` and `stale` findings | Fit |
| 3. An accepted gap | `exceptions/` with `expires`; C rules honour it | Fit; the overlay may carry a proposed exception |
| 4. Dependants of reused nodes, before and after | `impact.walk` on register + overlay | Fit. Gap: the before/after difference |
| 4. Reuse with change | not expressible | Gap, small: each reused node declared `as_is` or `changed`; `changed` reports its dependants as what an existing owner sees change |
| 4. What the new node rests on | no walk | Gap, small: composed from `requires` targets and `realisers` |
| 5. Route per unit | the gate's `owner` and `route` (task-0102, task-0110); questionnaires per unit (task-0043) | Fit for keys. Gap: the approvals per unit for overlay nodes and links |
| Input: held in the call, over MCP | five tools, read-only | **Gap**: candidate 1, read-only kept |
| Input: a register branch | `KG_REGISTER` serves a checkout; drafts withdrawn | Partial: candidate 2, the overlay is the branch's diff against its base |
| Input: first seen in an export | `reconcile.py` lists ids added since the previous export | Gap: register proposal, candidate 5 |
| Input: a journey partly based on another | no type; single `parent` | Open: §5 |

## 4. Opportunity canvas and SWOT

| Block | Content |
|---|---|
| Users and customers | Enterprise architects and product owners at initiative intake; capability owners asked to approve reuse; delivery leads judging readiness; an agent drafting the new product's design (task-0101's `design` class) |
| Problem | At intake, the questions are answered in workshops and on slides: what can be reused, what is new, what is missing, who must say yes, and which existing products it touches. The modelling tool shows the model, not whether the knowledge behind a reused capability is verified, current or contested. A proposal is invisible to every governed walk until it is approved, which is too late to change the design. |
| Solution | A read-only what-if. The proposal is an overlay, held in the call or taken as a branch's diff, read as if approved by the register's own checker and walks. Reports: deterministic link candidates; coverage and reach before and after; what the new node rests on; the keys the reused nodes carry, with their gate levels; the route per unit. Nothing is stored. The proposal becomes record only through a register pull request. |
| Value | C1/C2/C3 found at intake, not at approval. A reuse rate with the quality of its evidence. Owners of existing products warned before their product changes. An agent's design starts from the reused nodes' keys and their levels, not from the slides. |
| Metrics | Share of proposed elements reused versus new; gaps found at intake versus at approval; share of inherited keys verified or better; days from intake to an approved register pull request; candidate precision (accepted over proposed), deterministic and model counted apart |
| Channels | MCP in Claude Desktop and Claude Code (task-0117); the CLI on a register pull request in the instance CI; the page's impact box beside the two walks (task-0112); the lighthouse pilot's architects (m-8) |
| Cost | One evaluator module, a tool, a CLI and a report schema; tests on the public register; the candidate matchers. A new tool and schema are a contract addition: a minor version while 0.x (decision-0003), with a line under `## Unreleased`; `test_five_tools_every_one_marked_read_only` counts the tools, as doc-0016's run index would also change it |
| Risks | The overlay read as record: answered by `hypothetical` on every element and edge, never stored. Name matches proposing wrong links: answered by `inferred`, never above `proposed`, precision measured. Drift into an EA tool: knowgov never mints ids or writes register files. A second walk semantics: only the register's functions are called, loaded by path as `register_impact` does. The payload as a write path in disguise: the store view stays read-only |
| Unfair advantage | The gaps come from the register's own approved rules, and the reuse comes with statement-grain epistemic levels. A modelling tool shows that a capability exists, not whether what is known about it can be built on |

- **Strengths.** The register's functions take a dict, so the overlay needs no register change (shown in §2). The coverage rules are the gap rules. `register_impact` already joins nodes to keys, levels and owners. The read-only stance holds. *Response:* build on these and nothing else; no new walk semantics.
- **Weaknesses.** The knowledge side of a new element is empty by construction. The public register has 57 nodes, so name matching has not met real names. The register does not record two approvals on a cross-domain link. One maintainer. *Response:* report unmapped plainly; measure candidate precision at the pilot before a model joins; note the approval point to the register (§7).
- **Opportunities.** Initiative intake is an architect's first question, so it is a visible case for the ARIS lighthouse (m-8, decision-0006). An agent designing the new product can call the tool before it drafts. The branch route turns a register pull request into a reviewed what-if. *Response:* offer it as a pilot demonstration once candidate 1 runs on the public register; it does not displace m-8's prerequisites.
- **Threats.** ARIS, LeanIX and Ardoq offer impact analysis and roadmapping natively, so knowgov's edge is the epistemic layer alone. The work can pull effort from m-8. An overlay can be mistaken for an approval, and a model's candidate for a fact. *Response:* position the tool as "can this reuse be built on", never as a modelling feature. Candidates 1 to 3 stay one evaluator with no UI of its own. `hypothetical` and `inferred` are in the report schema, so a consumer cannot drop them silently.

## 5. Journey reuse: the open question

| Option | What it is | Gains | Costs |
|---|---|---|---|
| (a) No new type | Reuse shows through shared processes (`is_supported_by`) plus the name match D3. The overlay reports "same step as JRN-0002" | Nothing to decide. A process change already reaches both journeys (§2) | A change to the base journey that is not a process change (wording, order, a touchpoint) does not reach the derived one. Copied names stay unchecked by the register |
| (b) `derives_from` | A register relationship type, step to step (or journey to journey), walked from base to derived in `FORWARD`'s journeys row | Explicit lineage. A change to the base journey reaches the derived one | A register decision, a relationship file and a matrix row at `unverified` (no ARIS connection is asserted without a test). A re-vendor here |
| (c) Shared steps | One step referenced by several journeys (an `includes` link, the step's `parent` its first journey) | No copies | Hierarchy stops being `parent` alone. C1 counts a step once for two journeys. Largest change |

**Recommendation: (a) now, in the overlay. (b) is parked as a register proposal until an instance shows a derived journey whose base changed without a process change. (c) is rejected.** The maintainer decides.

## 6. The evaluator's shape (candidates 1 to 3)

- **Input.** Register-shaped nodes (provisional id, kind, name, parent, owner) and links (type, source, target, rationale). Each reused node is marked `as_is` or `changed`, with optional proposed exceptions. In branch mode, the overlay is every node file and link added or changed on the branch against a base ref. Ids there are the branch's own.
- **Rules.**
  - The overlay's elements are read as approved; the register's own draft and proposed elements keep their states.
  - Only the register's functions decide: `check_nodes`, `check_relationships` and `check_glossary` on the overlay's elements; `check_coverage`; `impact.walk` with `FORWARD` and `REALISERS`, with or without `children`.
  - Every overlay element and edge is marked `hypothetical`.
  - The report names the base (tag, commit) and the overlay's digest, and is never stored.
- **Report.**
  - Placement findings.
  - Candidates, each with basis and reason.
  - Coverage before and after, with denominators.
  - Reach before and after for every reused node, the `changed` ones flagged.
  - What each new node rests on.
  - The keys the reused nodes carry, with level, owner and route, as `register_impact` reads them under one task class and `as_of`.
  - The new elements left unmapped.
  - The approvals per unit.

  JSON is pinned by a schema under `harness/schemas/` and checked by `harness/schema_check.py`.
- **Deterministic candidates, in order.**
  - D1: a register id the input names (`authored`).
  - D2: an external id (`aris_guid`, `archi_id`, `edm_id`) matched through `[source]` after the connector lands an export (`authored`).
  - D3: an exact normalised name match with a node of the same kind, whose live links are offered to the new node (`inferred`). In the example this proposes JRN-0013 `is_supported_by` PROC-0002.
  - D4: for a step with no candidate, the realisers of the product's required capabilities as a pool, listed and never chosen. In the example the pool is PROC-0002, PROC-0003 and PROC-0004; none negotiates terms, so JRN-0014 and JRN-0015 stay C1 gaps.
  - D5: a forbidden synonym in a name is a placement error.

  A candidate never closes a gap by itself.

## 7. Candidates

| # | Candidate | Disposition |
|---|---|---|
| 1 | The evaluator and a further read-only MCP tool (`proposal_impact`), the overlay held in the call, report schema pinned | **Build**, medium; m-6 by kind, behind m-8's prerequisites unless the pilot asks |
| 2 | Branch mode: the overlay from a register checkout's diff against a base ref, CLI first, an optional step in `instance/ci/` | **Build**, small, after 1 |
| 3 | Deterministic candidates D1 to D5 | **Build**, medium, with 1 |
| 4 | A model's candidates through `arms.endpoint()` for rows D3 and D4 leave empty or ambiguous; `inferred`, never above `proposed`, off until the key variable holds a value | **Park** until 3's precision is measured on a real register at the pilot |
| 5 | Proposal to ieam-register: `reconcile.py` lists the export ids that no register node carries | **Register proposal**, small, with the ARIS connector's follow-ups (task-0121) |
| 6 | Proposal to ieam-register: `derives_from` (§5 b) | **Park**, on the trigger in §5 |
| 7 | The walkthrough in the demo README once 1 exists | **Document** |
| 8 | knowgov minting ids, writing proposal files into the register, or storing an overlay | **Reject** |

Noted for the register, not proposed here: a cross-domain link's two approvals are asked for by the README and recorded as one `approval.by`; a node without `[source]` passes the checker; names are not compared across nodes.
