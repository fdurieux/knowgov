---
id: doc-0012
title: >-
  Positioning: the governed-context quadrant, the market, and the route to the
  top-right
type: specification
created_date: '2026-11-03T22:44:00Z'
updated_date: '2026-11-06T09:38:00Z'
tags:
  - brief
  - positioning
  - market
  - quadrant
---
*2026-11-03. Maintainer register. A study: nothing built, nothing queued. Trigger: the maintainer's question of this date, where knowgov, Legible and ieam-register sit on a Magic Quadrant, the market potential of "the governed knowledge layer of a declarative twin", and what moves the stack to the far top-right. Scored at knowgov `5af89c4`, ieam-register `71de2d0` (v0.2.3), pumllint `38c5679`; recorded on `main` at `e2902b8` (register v0.2.4, `docs/guide.md` #80, the three saved queries #81), which moves no score: the walk itself is unchanged. Method: pumllint `docs/positioning-quadrant.md` (2026-08-28). Validated the same day by two external models, blind then adversarial (§5). The artifact page "Governed Context Quadrant" (https://claude.ai/artifact/Jizk9X9Gt6hKKGwxsZo82m) is a view of this doc. One record per thing: the twin wording stays doc-0010's, the walk, process-mining and code-traceability fit-gaps doc-0011's; this doc adds the market reading and the scores.*

## Verdict

**Visionary, deep: Vision 16, Execute 3 as first scored; 17.3 · 3 on the mean of three scorings (§5); 13 · 2 under a neutral rubric.** The differentiator survives review: nobody else gates delivery on whether design knowledge is verified (V2 epistemic governance, V3 delivery-time enforcement). The top-right corner (V ≥ 16 and E ≥ 16) is empty on the mean and contested: Palantir sits at 15 · 19, OpenAI's blind 17 puts it inside. "Empty corner" holds only for the narrow category, declared architecture upstream of delivery. The gap is execution: every other product averages Execute ≥ 10. Route: borrow execution from the incumbents (one lighthouse connector, the gate behind MCP, an outcome study), standardise second, company last.

Not in Gartner's DTO Magic Quadrant (first edition 2026-07-27, 18 vendors): its definition needs operational data, knowgov holds the declarative twin. Not a fourth register in the EA Tools MQ (2025-10-06) either, at E ≈ 3 against 16–20. The position is the seam between them. Positioning line: *"Before an AI agent builds on what your architecture says, know whether it is true."*

*2026-11-06: re-scored by the home team under the neutral rubric at 16 · 4 (18 · 5 on the note rubric), still Visionary (§8). doc-0027 is the brief for the external pass.*

## 1. Category and field

Governed context for AI-assisted delivery over the declarative twin: products holding what an organisation declared about its design and making it usable by agents and pipelines. The stack is scored as one dot (knowgov, ieam-register, Legible's gate contract with pumllint and aris2puml). Field as first drawn: SAP LeanIX + Signavio, Palantir Ontology/AIP, Celonis PI Graph/AgentC, Bizzdesign, Atlan, Ardoq, FINOS CALM, Backstage/Port, Spec Kit/Kiro, Structurizr/LikeC4, Neo4j. Added by the reviewers: ServiceNow, Collibra, Microsoft Fabric IQ (OpenAI also Orbus, Avolution, Sparx, unscored here).

## 2. Rubric

Eight criteria 0–5, two unweighted sums 0–20, midlines 10.

- V1 declarative model and identity; V2 epistemic governance; V3 delivery-time enforcement; V4 agent grounding and openness.
- E1 maturity; E2 adoption; E3 integrations with systems of record and delivery tools; E4 sustaining backing.

**Bias, accepted (§5).** V2 and V3 as first worded name knowgov's mechanisms (documented absence, invalidation on source change, exit codes). Neutral wording, OpenAI's: V2 "machine-readable trust controls: provenance, ownership, status, freshness, conflict handling, audit, policy mapping"; V3 "enforceable decisions in agent and delivery workflows: policy, permissions, approvals, exceptions, audit, integration breadth". Re-issue the rubric in that form before any re-scoring.

## 3. Scores

| # | Product | Note V · E | Gemini blind | OpenAI blind | Mean V · E |
|--:|---|--:|--:|--:|--:|
| 1 | knowgov stack | 16 · 3 | 18 · 4 | 18 · 2 | 17.3 · 3 |
| 2 | SAP LeanIX + Signavio | 12 · 20 | 13 · 20 | 14 · 20 | 13 · 20 |
| 3 | Palantir Ontology / AIP | 14 · 19 | 14 · 19 | 17 · 19 | 15 · 19 |
| 4 | Celonis PI Graph / AgentC | 10 · 20 | 12 · 19 | 14 · 20 | 12 · 19.7 |
| 5 | Bizzdesign | 11 · 19 | 11 · 17 | 13 · 18 | 11.7 · 18 |
| 6 | Atlan | 12 · 16 | 11 · 16 | 14 · 17 | 12.3 · 16.3 |
| 7 | Ardoq | 10 · 16 | 13 · 13 | 13 · 16 | 12 · 15 |
| 8 | FINOS CALM | 13 · 12 | 13 · 9 | 15 · 10 | 13.7 · 10.3 |
| 9 | Backstage / Port | 9 · 19 | 13 · 18 | 14 · 18 | 12 · 18.3 |
| 10 | Spec Kit / Kiro | 8 · 17 | 15 · 14 | 11 · 16 | 11.3 · 15.7 |
| 11 | Structurizr / LikeC4 | 7 · 11 | 13 · 11 | 11 · 13 | 10.3 · 11.7 |
| 12 | Neo4j | 5 · 20 | 9 · 19 | 9 · 20 | 7.7 · 19.7 |
| 13 | ServiceNow | — | 13 · 20 | 14 · 20 | 13.5 · 20 |
| 14 | Collibra | — | 12 · 17 | 14 · 20 | 13 · 18.5 |
| 15 | Microsoft Fabric IQ | — | — | 15 · 19 | 15 · 19 |

The note's criterion scores for the stack: V 3/5/5/3, E 1/0/1/1. Both blind reviews: V 4/5/5/4; E 1/1/1/1 (Gemini), 1/0/1/0 (OpenAI). Under the neutral rubric (OpenAI): V 3/4/3/3, E 1/0/1/0.

**Cells that decide it.** V2 = V3 = 5 rest on the three-valued answer, `valid_until`, the S6 staleness chain, declared gaps and `harness/gate_cli.py` (PROCEED/QUALIFIED/BLOCKED, exit 0/1/2, baseline), the only V3 with a measured effect (pumllint `docs/neo4j-governed-knowledge-evaluation.md`: governed arm 0 generations under BLOCKED in 20 cells; baseline generated in 35 of 35; "supported for the mechanism, unproven for the outcome"). V1 = 3: synthetic content; the walk follows 5 of 10 relationship types (doc-0008, doc-0010 gap 2; doc-0011 §1 measures the dependants rule that would close it, the register's to adopt; #81's saved queries answer from a capability or an entity without changing the walk). V4 = 3: no MCP surface, no interchange standard. E: own repository since 2026-11-01, 0–1 stars per repository, pumllint about 1,000 PyPI downloads a month, no client instance, 0 of 3 export routes verified (`mapping/matrix.toml` all `unverified`), one maintainer.

**Incumbents under-scored in the note, accepted:** Celonis V1 (4, its process graph is more than event logs), Backstage/Port V1 and V3 (typed catalogs, scorecards that break builds), Structurizr/LikeC4 V1 and V4 (git-native), Neo4j V4 (official MCP). **Rejected:** Gemini's Spec Kit/Kiro V3 = 5 (task gating is not a verdict on whether a spec is verified).

## 4. Market

No analyst sizes the category. Adjacent, scopes incompatible, context only: EA tools $1.2–1.7 bn (2025, about 6–7 % a year); DTO $2.5–3.5 bn (2026, secondary estimate); knowledge graphs $1.1–2.5 bn (2024–25, 23–37 % a year); AI TRiSM $2.3–3.1 bn (2026, 18–30 % a year). Demand signals: AI coding tools at 97 % of large enterprises with about a third fully governed (Black Duck); 55 % name reliability and hallucination as the top agentic challenge (Futurum, n = 820, H1 2026); "context layer" a product category in 2026 (Atlan, Fabric), data-side only; Spec Kit past 115k stars; SAP LeanIX MCP server GA, 200+ customers querying.

**Serviceable, own arithmetic:** 7,500–15,000 EA-tool customers × 25–35 % regulated with AI delivery at scale × €40–120k a year ≈ €0.1–0.5 bn; at Gemini's 5 % attach rate €15–90 m. Read as €15 m to €0.5 bn. **Obtainable, three years:** 3–8 instances × €60–150k ≈ €0.2–1.2 m a year, services-led through an integrator or design partner only (both reviewers).

*2026-11-05, from doc-0019 (C4).* Adjacent category, not scored and not added to §1's field: GraphRAG, an LLM answering from a knowledge graph built out of documents (Neo4j's llm-graph-builder; Barry et al., GenAIK 2025, BNP Paribas IT Group with Lingua Custodia and Neo4j, FinanceBench and DORA against FFIEC). Demand signal: a regulated organisation's IT group publishing GraphRAG on Neo4j, the buyer m-8 targets. It scores whether an answer is faithful to its retrieved context, by an LLM judge; it has no statement status and no score for an abstention. Line beside the Verdict's: *GraphRAG makes an answer faithful to its graph; knowgov says whether the graph may be built on.* No score moves.

## 5. External review

Two passes per model: blind scoring from the rubric and a fact sheet on the stack, then an adversarial critique of the published note. OpenAI `gpt-5.5` (2026-04-23), high effort, web search. Google `gemini-pro-latest`, medium effort, no search: at high effort the egress proxy answered 502 before the first byte. Both verdicts **AGREE WITH CHANGES**. Bounds: the fact sheet was written by the note's author, so its framing is not independent; transcripts were not kept in the repository, this section carries their numbers.

Agreed by both, accepted: the rubric favours the home team (§2); the incumbents' vision is under-scored (§3); ServiceNow and Collibra are missing; plug in first, standardise later; the thesis holds ("most incumbents stop at search, chat and visualize", OpenAI).

Differ: the corner (Gemini empty, OpenAI Palantir); the market (Gemini 5 % attach, OpenAI the upper figure plausible as a back-of-envelope).

Rejected: Gemini's EU AI Act date ("Annex III roughly August 2027"). Under the Act as adopted, Annex III applies from 2026-08-02; 2027-08-02 is Annex I. The reported deferral of Annex III to December 2027 stays unverified until the Official Journal confirms it, and is not a demand signal. Gemini's "S1 builds a native capture tool" misreads ieam-register (the tools of record stay authors); its point stands that capture must not delay the first connector.

Factual corrections applied to the page: CALM self-reports more than 2,000 application *deployments*, not applications described; SAP "furthest on vision" in the DTO MQ is vendor-reported only.

## 6. Route to the corner

Three routes: **B, plug in, first**; **A, standard (an epistemic extension to FINOS CALM, register-to-CALM mapping), second**; **C, product company, last**, though a legal entity is a pilot prerequisite (OpenAI).

| Stage | Target V · E | Moves |
|---|---|---|
| S1, 0–6 months | 17 · 6 | One lighthouse: one incumbent (LeanIX + Signavio, or Ardoq), one paid pilot in a regulated organisation, that export route verified with evidence. The gate and the three-valued query behind a read-only MCP server, same verdicts, same schema. The outcome study pre-registered on the pilot's backlog. Legal entity, permissive licence for adapters, security pack, support terms. One buyer-facing name. doc-0009's capture milestone continues without delaying the connector (its adopter milestone is under way: `docs/guide.md`, #80). |
| S2, 6–18 months | 18 · 11 | The outcome study run (defect escape, rework, review time, governed against ungoverned). Three referenceable clients in one vertical through one integrator. A second connector; the CALM proposal upstream. The walk over all ten relationship types, by ieam-register decision. A second maintainer. |
| S3, 18–36 months | 19 · 16 | The extension accepted, knowgov its reference implementation. Ten or more instances; one incumbent marketplace listing. Optional join to the running twin when Loop B's trigger fires: conformance received as evidence on `PROC-` ids, never produced (doc-0010 §6, doc-0011 §2). 1.0 contracts after a foreign corpus. |

Targets are the first-scored rubric's; under the neutral rubric each stage sits about three points lower on Vision.

## 7. What would reopen this

- CALM ships statement-level provenance or a verification gate: the differentiator contested from a better execution base. Watch CALM 1.3 and its 2026 roadmap.
- LeanIX or Palantir withholds from agents on unverified fact sheets or objects: V2 and V3 to 4, into the corner.
- The outcome study is null: V2 and V3 stay mechanism claims, and the position is a niche player with a strong method.
- A paying pilot, a verified export route, or an MCP surface: re-score E and V4, re-issue the figure with the neutral rubric.

Nothing else changes. S1's items became tasks on the maintainer's go of 2026-11-03, in milestone m-8 "The lighthouse": task-0062 (choose the incumbent and the pilot; the connector choice is the maintainer's), task-0063 (the connector, verified), task-0056 (the gate behind a read-only MCP server), task-0057 (the outcome study pre-registered), task-0058 (licence for adapters), task-0059 (security pack), task-0060 (legal entity and support terms), task-0061 (one buyer-facing name). doc-0009's two milestones are m-5 (capture) and m-6 (adopter), doc-0011's code traceability m-7; m-8 runs beside them and does not wait for them.

## 8. Re-score, 2026-11-06 (home team, neutral rubric)

*2026-11-06. Triggers:
- §7's "an MCP surface: re-score E and V4" fired with task-0056 (the reader has grown to 16 tools since);
- the maintainer's question of this date: the quadrant now and as a v1.0.

Scored in session at knowgov `43ee83f` (after v0.7.0), ieam-register `735b2e2` (v0.2.12) and pumllint `a39d800`. Checked again at knowgov `a743cca`: no cell moves. That includes decision-0015 and task-0161 (`b44b9bd`), and task-0159's CI hygiene (#285), whose coverage figure is not counted here. The wording is §2's neutral wording, with no anchors (doc-0027's anchors are for the external pass). The field is not re-scored. This is home-team scoring with no external pass yet: doc-0027 is the brief for one, and its output is compared here when it returns. The v1.0 gap lists are doc-0028's; the definition of 0.9 and 1.0 is proposed in decision-0016.*

| | V1 | V2 | V3 | V4 | **V** | E1 | E2 | E3 | E4 | **E** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| §3, neutral (2026-11-03) | 3 | 4 | 3 | 3 | 13 | 1 | 0 | 1 | 0 | 2 |
| **2026-11-06, neutral** | 4 | 4 | 4 | 4 | **16** | 2 | 0 | 2 | 0 | **4** |
| §3, note | 3 | 5 | 5 | 3 | 16 | 1 | 0 | 1 | 1 | 3 |
| 2026-11-06, note | 4 | 5 | 5 | 4 | 18 | 2 | 0 | 2 | 1 | 5 |

**What moved.**

- **V1, 3 → 4: the walk.** §3 counted 5 of 10 relationship types walked, at register v0.2.3. Since then:
  - register decision 0010 (2026-11-03) walks dependants from every kind, over 8 of the 10 types, with `owns` and `maps_to` excluded by rule;
  - decisions 0012 (realisers), 0014 (`parent` descent on request) and 0018 (thread) add named walks.

  §6 S2's "the walk over all ten relationship types" is met in substance. It is not 5: the content is synthetic.
- **V3, 3 → 4 (neutral).**
  - fail-closed Claude Code hooks at plan, spec commit and push (task-0099, task-0102), and on attestation paths (task-0147);
  - the GitHub action's SARIF upload to code scanning (task-0116);
  - the permission matrix (task-0059 AC #5).

  It is not 5: the GitLab include has not met a runner (task-0108), and no enforcement has been measured at an organisation (task-0103).
- **V4, 3 → 4.** §3 recorded "no MCP surface". There are now 16 read-only tools and 2 prompts on the reader:
  - over stdio and Streamable HTTP, in both protocol eras (task-0079);
  - with conformance checked against the official SDK (task-0056);
  - beside the runs server (decision-0008).

  It is not 5: there is no interchange standard; §6's route A is untouched.
- **V2 stays 4.**
  - Stronger: review lapses (decision-0005), owner and closer routing (task-0102, task-0110), staling on a register change (task-0122).
  - Still absent: policy mapping to an external framework.
- **E1, 1 → 2.**
  - For: seven tags (v0.1.0–v0.7.0), each with its image; the 2026-11-05 review's critical fixes closed (task-0141); the security pack (task-0059); digest pins with Dependabot (task-0092).
  - Against: six contract-changing minors in four days; no coverage figure at the scored commit (task-0159, merged since as #285); no published image that runs the arms until 0.8.0.
- **E3, 1 → 2, on the delivery side only.** On the system-of-record side, the ARIS connector is built (task-0063 AC #1, #3, #4), and `mapping/matrix.toml` reads 17 rows `unverified` and 0 verified.
- **E2 stays 0:** no stars, forks or instance. **E4 stays 1 on the note rubric** and is 0 on the neutral: one maintainer, no entity (task-0060).

**Reading.** Still Visionary, deep.
- §6 S1's target was 17 · 6 (note rubric). Vision is past it, and Execute stands at 5. That Execute came from engineering maturity and the delivery side, not from S1's own items. Every one of S1's own Execute items is untouched: the pilot organisation (task-0062 AC #2), a verified route (task-0063 AC #2, #5), the outcome study (task-0057), the entity (task-0060), the licence (task-0058) and the name (task-0061). Each remaining Execute point needs a third party or a decision that is not code; more code moves E1 by one at most.
- On the note rubric 18 is the field's highest Vision (Palantir 15 on the mean). The field was never scored on the neutral rubric, so no comparison holds there.
- ARIS, decision-0006's incumbent, is not in §1's field. doc-0027 adds it, with Orbus, Avolution and Sparx.

**As a v1.0 (neutral; doc-0028, decision-0016):**

| state | V | E | cells |
|---|--:|--:|---|
| contracts frozen, 1.0 by declaration | 16 | 5 | only E1 moves, 2 → 3 |
| 1.0 at the lighthouse: one paid pilot in a regulated organisation, the ARIS route verified on its installation, an entity with support terms | 17–18 | ≈ 9 | V1 5, V3 4–5; E1 3, E2 1, E3 3, E4 2 |
| S3 (note rubric target) | 19 | 16 | §6 |

A version number is an E1 lever, worth one point. The dot moves right with the lighthouse, not with the tag.

## 9. External pass, 2026-11-06 (doc-0027, first runner)

*Drafted by the v1.0 session from the coordinating session's run; recorded by the coordinator.*

The run:
- Brief: doc-0027, sent unedited by the coordinating session.
- Model and settings: OpenAI `gpt-5.5-2026-04-23`, Responses API, effort high, web search on. This is the operator's record; the report's own runner section says "model not exposed".
- Time: 09:02–09:10 UTC; 237,973 input tokens and 29,060 output.
- Inputs: the 13 files doc-0027 §4 marks required, fetched at its pins and attached (aris2puml `main` at `ca22e13`). It also browsed the §4.4 pages.

The raw report stays outside the repository; this is our reading of it. It is one runner of the two families doc-0027 asks for. It did not read the code, so most of the stack's cells rest on `documented` evidence. Its contamination log names pumllint's PyPI page (the diagram-as-code quadrant), influence "none", and J-F mentions, ignored.

**The stack.**

| scoring | V1 | V2 | V3 | V4 | **V** | E1 | E2 | E3 | E4 | **E** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| §3, neutral (2026-11-03) | 3 | 4 | 3 | 3 | 13 | 1 | 0 | 1 | 0 | 2 |
| §8, home re-score, neutral | 4 | 4 | 4 | 4 | 16 | 2 | 0 | 2 | 0 | 4 |
| **external, neutral with doc-0027's anchors** | 3 | 4 | 3 | 3 | **13** | 2 | 0 | 1 | 0 | **3** |

- **Blind, it reproduces §3's neutral Vision exactly (13).** What it credits since 2026-11-03 is one point of E1, the releases. §8's +3 on Vision (V1, V3, V4) is not confirmed. This is the home-team lift §2 named ("about three points lower on Vision"), seen again under the neutral wording.
- **V1, 3 against §8's 4.** It read the three walks and the `owns`/`maps_to` exclusion correctly. It held V1 at 3 for synthetic content and unverified export mappings: identity *across the authoring tools* is unproven. Accepted: under the anchors, "all elements working" needs that cross-tool identity.
- **V3, 3 against 4.** Some integrations are not proven on real runners (GitLab) or real installations. Accepted.
- **V4, 3 against 4.** It weighed GPL-3.0-or-later against embedding, and the domain formats as non-standard, beside the MCP surface. §8 left out the licence, which the rubric's V4 names. Accepted. task-0058 is the lever.
- **E3, 1 against 2.** It treats the delivery integrations as built but not verified at an adopter. The anchor's "verified" is undefined for delivery tools: the GitHub action runs for real in `harness.yml`, so 2 is arguable. Recorded as a scale question, not conceded.
- **V2, E1, E2, E4: agreed** (4, 2, 0, 0). V2's 4 is marked as resting on `documented` evidence alone.

**The field.**
- The corner holds **Palantir (17 · 16) and ServiceNow (16 · 20)**. §3's "empty on the mean, contested" does not hold under the neutral wording with anchors, as OpenAI's blind 17 already hinted.
- The stack's Vision of 13 is mid-field. It equals LeanIX + Signavio's 13 and sits below Palantir, ServiceNow, Collibra and Fabric IQ, and below Celonis and CALM at 14. §8's "the field's highest Vision" holds on the note rubric only.
- 17 of the 18 field products land in Leaders (all but FINOS CALM, at 14 · 9), with Structurizr / LikeC4 on both midlines at 10 · 10. That is a property of doc-0027's midline at 10 with anchors that reward scale, not a finding about the field.
- Its category verdict: "coherent but not yet an analyst-standard category name"; the field is heterogeneous by design.

**As a v1.0.**

| state | external V · E | §8 (home) V · E |
|---|--:|--:|
| v1.0-minimal / contracts frozen | 13 · 3 | 16 · 5 |
| v1.0-as-defined / at the lighthouse | 16 · 8 | 17–18 · ≈ 9 |

- **Both readings agree on the claim that matters.** The version number moves nothing, or one E1 point. The lighthouse moves Execute to about 8–9, still left of the midline, and still Visionary.
- **Its conditions match decision-0016's,** points 1, 3 and 4, and doc-0028's G9 and G1:
  - stable contracts, including the MCP tools' schemas;
  - a public external pilot on real content;
  - a system-of-record route verified on a real installation;
  - CI integrations proven on the platforms they name;
  - a legal entity and support terms;
  - a licence decision for adapters;
  - a release image that matches the security claims.
- **It adds four conditions:**
  - an independent security review, or an adopter's security sign-off;
  - a compatibility statement for the two MCP protocol eras;
  - a bus-factor disclosure;
  - adoption metrics that tell stack use apart from pumllint's downloads.

**Errors it found in the sources.** Two of them this session had found too (doc-0028 G9-9):
- `README.md` says Python 3.13, but the image is 3.12;
- `docs/guide.md` §6 says the review step is not built.

Two are new:
- `docs/guide.md` still describes a narrower impact walk than the register's three walks;
- 0.7.0's Known limits (no containment, no whole publication) read against Unreleased's fixes: the published image lags `main`.

**What would change its mind:**
- a public pilot on real content, with a redacted evidence pack;
- a real system-of-record run, with a redacted reconciliation report;
- a sustaining model: an entity or governance, support terms, bus-factor disclosure and an adapter licence strategy.

These are G1-1, G1-2 and G1-4, and G9-8.

**Bounds.** One runner, not two. It worked from documentation, not code. doc-0027's anchors are new, so their effect cannot be separated from the runner's. The second runner, from another model family, is still owed. Proposed: until it reports, this doc reads the stack at the external 13 · 3, and keeps §8's 16 · 4 as the home team's reading.
