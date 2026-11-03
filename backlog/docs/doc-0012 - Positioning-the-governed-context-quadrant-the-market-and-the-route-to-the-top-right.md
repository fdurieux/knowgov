---
id: doc-0012
title: >-
  Positioning: the governed-context quadrant, the market, and the route to the
  top-right
type: specification
created_date: '2026-11-03T22:44:00Z'
updated_date: '2026-11-03T22:49:00Z'
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

Nothing else changes. S1's items became tasks on the maintainer's go of 2026-11-03, in milestone m-5 "The lighthouse": task-0054 (choose the incumbent and the pilot; the connector choice is the maintainer's), task-0055 (the connector, verified), task-0056 (the gate behind a read-only MCP server), task-0057 (the outcome study pre-registered), task-0058 (licence for adapters), task-0059 (security pack), task-0060 (legal entity and support terms), task-0061 (one buyer-facing name). doc-0009's capture milestone stays in m-2.
