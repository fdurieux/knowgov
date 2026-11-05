---
id: doc-0019
title: >-
  GraphRAG read against knowgov: the paper verified against its tables, fit/gap,
  opportunity canvas, SWOT, candidates
type: specification
created_date: '2026-11-05T17:21:00Z'
updated_date: '2026-11-05T17:22:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - brief
  - positioning
  - arms
  - capture
---
*2026-11-05. Maintainer register. A study. Trigger: the maintainer's question of this date, the relevance and applicability to knowgov of Barry, Caillaut, Halftermeyer, Qader, Mouayad, Cariolaro, Le Deit, Gesnouin, "GraphRAG: Leveraging Graph-Based Efficiency to Minimize Hallucinations in LLM-Driven RAG for Finance Data", GenAIK workshop at COLING 2025, pp. 54–65 (https://aclanthology.org/2025.genaik-1.6.pdf; BNP Paribas IT Group, Lingua Custodia, Neo4j, Graph Thinking Consulting), asked as an opportunity canvas, a fit/gap, a SWOT and a proposal. Evidence: the paper, all 12 pages; knowgov `main` at `473ab65` (0.6.0); the CargoQuote record as vendored (`subjects/cargo_quote/vendor/kg_experiment/results/`). Not opened: the paper's two repositories (`gcaillaut/financebench-graph-rag`, `halftermeyer/dora-ffiec-hybrid-rag-neo4j`), licences unchecked; GraphRAG work after January 2025, not surveyed. The artifact page "GraphRAG against knowgov" (https://claude.ai/artifact/Gz7HNfg6dnvQdshuLt2WS6) is a view of this doc. Settled the same day on the maintainer's go: this doc, C1 and C3 as tasks (§5), C4 as a dated entry in doc-0012 §4.*

## Verdict

**Different questions. GraphRAG makes an answer faithful to what was retrieved; knowgov decides whether what was retrieved may be built on, and stops the build when it may not.** The failure modes line up: the paper's faithfulness metric gives full marks to an answer faithful to a wrong fact, which is the blind spot `docs/guide.md` states for consistently wrong knowledge (J-F D3 and D5, 17 and 20 failing scenarios); and it has no score for an abstention, knowgov's main measured outcome (S2: the governed arm abstained 5 of 5; no code under BLOCKED in 20 of 20 runs).

**Relevance: medium.** As evidence, the paper is the framing a regulated buyer brings to the lighthouse (m-8): a bank's IT group publishing GraphRAG on Neo4j. As technique, three bounded borrowings, each into an existing slot, each a model's output kept below `proposed`:

1. Key-constrained fact extraction (FactRAG) into route (c) (`harness/transcript.py`, task-0041), widened from a transcript to a prose document. The deterministic mappers supply what the paper lacked: a ground truth to score the extractor against (C1).
2. Compact facts in place of quoted evidence (the paper's graph-only ablation). In the record the governed prompt is 2.0–2.7× the baseline's (C3).
3. Blocked pairwise contradiction search (HybridRAG, O(n²) to O(k·n)) for prose fragments that R-CONFLICT cannot pair because they share no key, blocked by the graph rather than by embeddings so the pair set stays deterministic (C2).

Does not transfer: text-to-Cypher, a vector index in the store port, an LLM judge in the record, a DORA/FFIEC subject (C7, C8). Proposal: one spike (C1), one measured deviation run (C3), one park (C2), one positioning line (C4). None displaces m-8.

## 1. The paper, verified against its tables

Systems: Text RAG (500-character chunks, all-MiniLM-L6-v2, chromadb); Facts RAG (an LLM turns retrieved chunks into triples and one-sentence facts); KG-RAG (Neo4j's llm-graph-builder with a schema derived from the benchmark's questions; chunks plus one-hop neighbours); HybridRAG (an LLM routes to text-to-Cypher or vector KNN), tested on contradictions between DORA and the FFIEC IT handbook. Generators Llama 3.2 3B, Llama 3.1 8B, Qwen 2.5 32B; judge GPT-4o through DeepEval; FinanceBench, 150 questions over 84 filings.

| Claim | Tables | Reading |
|---|---|---|
| "6 % reduction in hallucinations" | Faithfulness Text → Facts: 3B 0.844 → 0.937, 8B 0.843 → 0.891 (+5.7 %), 32B 0.954 → 0.970. The paper's hallucination metric Text → Facts: 3B 0.704 → 0.679, 8B 0.659 → 0.658, **32B 0.395 → 0.594**. KG-RAG 3B faithfulness 0.790 < Text 0.844 | Partly. The faithfulness gain holds for small models; on the largest the hallucination metric worsens, undiscussed |
| Graph-only context best (Table 2) | Faithfulness graph only / text + graph: 0.940/0.790, 0.965/0.890, 0.988/0.963. Hallucination: 0.665/0.660, 0.576/0.532, 0.619/0.407 | Metric-dependent: graph-only wins faithfulness and loses hallucination on all three models |
| "80 % decrease in token usage" | Figure 4 only, input tokens Facts vs Text over the 150 questions | Plausible; whether the fact-generation calls are counted is not stated |
| "734-fold decrease in token consumption", O(n²) → O(k·n) | 1,975,944 → 2,690 LLM calls, k = 10; "eight potential contradictions" | Thin. A ratio of calls against an all-pairs run not made; the eight unvalidated; recall unknowable by construction (pairs outside the top-k never judged). Standard blocking |
| Explainability, traceability | Figure 5, a demo screenshot | Qualitative |
| Method | LLM-as-judge, one run, 150 questions; no accuracy against FinanceBench's gold answers; English only; the hallucination metric is contradicted contexts over contexts, so it moves with the context set, which differs between systems | Faithfulness to the retrieved context, not correctness; no score for abstention. The authors list the judge's cost and English-only prompts among their limits |

The paper's own statement of the trade-off: a graph is "either hand-crafted (extremely costly and difficult to maintain) or automatically generated (error-prone and compute-intensive)". knowgov's deterministic mappers, the `inferred` basis and owner confirmation sit in that space.

## 2. What exists, verified

**Tokens.** The API's `usage` in `results/S*/run*_*.json`, governed against baseline prompt tokens: S1 17,394/6,832 (2.55×), S2 16,123/6,213 (2.60×), S3 14,855/6,267 (2.37×), S4 18,102/6,637 (2.73×), S5 16,222/6,312 (2.57×), S6 17,917/6,874 (2.61×), S7 13,402/6,832 (1.96×). Model `gpt-5.1-2025-11-13`.

**Bundle composition.** Every line of `results/S*/bundle_G.txt` classified by its prefix (`gate.render_key`). S1–S6: evidence quotes 27–30 % of the characters, verification 19–22 %, approval 10–11 %, assertion text 8–10 %, assertion lines 21–23 %, key headers 3 %, verdict, policy and sections 3–8 %. Kept to key headers, assertion lines and sections: 28–34 % of the bundle (S7, with no verification or approval lines, 51 %), 0.63–0.90× the baseline prompt's characters. `gate.knowledge_reader` already serves a key's full section on demand (task-0022.03).

**References.** M5 resolves every claim's `ref` against the bundle ids (`measures.resolvable_refs`): S2 run 1, G 42/42, B 20/20. It checks that a reference resolves, not that the claim's value matches the cited assertion's.

**Extraction.** `extract.py` is hand-written per artefact family. `instance/kinds.toml`: 20 kinds, 8 with mappers; 12 with `mappers = []`, of which two reach a mapper by conversion (`aris-epc` through aris2puml, `c4-models` drawn in PlantUML). The other ten: user stories, architecture decisions, ArchiMate, SysML/Capella, schemas, data models, threat models, event logs, glossary, property invariants. A model's output already has a slot: route (c) proposes values for the task's keys at `absent` or `declared_gap` (`transcript.EMPTY`) from a transcript, loaded by `load.load_inferred_proposals` as basis `inferred`, status `proposed`, attributed to the model, never promoted, listed in the questionnaire's `known`; `gate.py` flags a key whose rows are all `inferred`, `assumed` or `hypothesised`.

**Contradictions.** R-CONFLICT pairs assertions of one key, and a person's statement against a document's (task-0038). No rule pairs prose fragments that share no key. Ground truth on public content: CargoQuote S4 (contradictory); J-F D1 and D2 (layers disagree); D3 and D5 (consistently wrong, which no consistency check can see).

## 3. Fit/gap

| Paper | knowgov today | Fit/gap |
|---|---|---|
| Grounding before generation | `gate.render_bundle`: per key the assertions with value, basis, status, source, evidence, verifications, approvals; `evidence_bundle` over MCP | Fit, stronger: status and a verdict that can stop generation |
| Validation after generation (set aside by the paper) | M5 references, M4 oracle, `trace.py check` | Fit, mechanical. Small gap: claim value against the cited assertion (C5) |
| FactRAG: an LLM extracts triples and facts | Mappers for 8 kinds; route (c) for transcripts | Partial: prose documents of the unmapped kinds, a generic fragmenter (C1) |
| Extraction schema from the questions | The task's required keys `entity\|predicate` | Fit, stronger: free predicates ("up to 3 words") would join no key |
| KG-RAG: chunk embeddings and neighbours | No embeddings; retrieval exact, by key | Gap by design; only C2's blocking would need it, and the graph serves |
| Concise facts beat raw text | Bundle 2.0–2.7× the baseline's tokens | Gap: no compact form measured (C3) |
| HybridRAG router: text-to-Cypher or vectors | Typed read-only MCP tools; no Cypher outside `store_neo4j.py` (task-0003); saved queries console text | Reject text-to-Cypher (C7) |
| Contradictions across corpora | R-CONFLICT on a shared key | Gap (C2) |
| LLM-judge faithfulness, hallucination | M1, M3, M4, M5, M7, tokens per call | Fit, stronger; no judge in the record (C7) |
| Gateway, monitoring, audit logs, caching | `demo/models.toml`, `arms.endpoint()` (doc-0006); `runs/`; usage with cached tokens; token ceiling | Fit |
| Guardrails | The gate as a command; fail-closed hooks (task-0099, task-0102) | Fit, stronger: delivery-time enforcement |
| Trace to sources | Assertion → fragment (locator, digest) → document version; invalidation and suspect code on change (S6) | Fit, stronger: a fact has a lifecycle |
| English only | Mappers structural; `vague_words` per subject; route (c)'s prompt English | Partial: C1 states its language |
| FinanceBench, DORA, FFIEC | Synthetic CargoQuote and J-F; no bank-related data | Out: boundary (C8) |

## 4. Opportunity canvas and SWOT

| Block | Content |
|---|---|
| Users and customers | Process and product owners answering the questionnaire; an architect onboarding an instance of mostly unmapped kinds; the pilot's delivery leads, who pay for tokens; buyers in regulated organisations already running GraphRAG on Neo4j |
| Problem | Prose kinds load as `unmapped`, their keys read `absent`, and the gate blocks on knowledge the documents may state; a mapper per kind per organisation is the first wall. The governed context costs 2.0–2.7× the documents, against GraphRAG's promise of fewer tokens. Prose contradictions with no shared key are invisible. Buyers hear "graph-grounded" as "trustworthy", and GraphRAG's metric cannot tell faithful from correct |
| Solution | C1 route (c) over a document, constrained to the empty keys, each proposal naming its fragment, scored against the mappers first. C3 a compact bundle, an option measured as a deviation run. C2 graph-blocked contradiction candidates, advisory. C4 one positioning line |
| Value | `absent` keys at first load become owner confirmations rather than owner authoring; a measured token cost of governance; a consistency signal across prose; an answer to "why not just GraphRAG?" |
| Metrics | C1 precision, recall, inventions against the mappers; no value for S2's declared gap, no silent resolution of S3; owners' acceptance rate at the pilot. C3 prompt tokens with M1, M4, M5, compact against full. C2 recall on S4 and D1/D2, false positives per 100 pairs, nothing new on D3/D5 |
| Channels | The questionnaire's `known`; the pre-load report at info; the page's Arms mode; `evidence_bundle`; doc-0012 and the lighthouse conversation |
| Cost | C1: `transcript.py`'s call with a document's fragments as input, a generic prose fragmenter, a scoring script; one call per document per task. C3: a render option and about 70 calls (S1–S7 × 5 runs × 2 forms), about 0.8 M tokens against the 6 M ceiling. C2: graph blocking and one call per pair. A new option or info finding is additive: a minor version while 0.x (decision-0003), a line under `## Unreleased` |
| Risks | A candidate read as knowledge: `inferred`, never promoted, flagged by the gate. A model filling a declared gap or resolving ambiguity: measured on S2 and S3 first. Content leaving the network: off until the key variable holds a value. Drift into a RAG product |
| Unfair advantage | knowgov holds the ground truth the paper lacked: mappers to score an extractor, an oracle to score answers, plants with known defects (S2, S3, S4, D1–D5). Each borrowing is measured against them, not against a judge |

- **Strengths.** Statement-grain status, basis, verification, lapse and invalidation (S6), which GraphRAG has none of. Abstention measured (20 of 20). Evaluation by oracle (M4) and mechanical reference resolution (M5). Neo4j already the default store. The `inferred` basis and route (c) already receive model output safely. *Response:* borrow only into these slots.
- **Weaknesses.** Mappers by hand, 8 of 20 kinds. The bundle 2.0–2.7× the documents. No semantic retrieval: a key must match `entity|predicate` exactly. No contradiction detection across prose. One maintainer. *Response:* C1, then C3, then C2, each measured before it ships.
- **Opportunities.** m-8's buyer, a regulated organisation, already invests in GraphRAG on Neo4j; knowgov is the layer that tells such an assistant whether its graph may be built on. Neo4j is in doc-0012's field: a partner angle. The paper's admitted trade-off is the space knowgov occupies. A public measurement of LLM extraction against deterministic mappers is Execute-axis evidence. *Response:* C4 now; C1's measurement as the evidence.
- **Threats.** "GraphRAG reduces hallucinations" read as solving knowgov's problem, with cheaper stacks, so knowgov looks like overhead. Faithfulness as the yardstick, on which abstention scores zero. LLM extraction eroding "never invents" if a candidate reaches the record. A numbers fight over the paper's headline figures. *Response:* S2 against D3 (an answer faithful to its graph against a graph worth trusting); every model output below `proposed`; cite the paper's tables, not its abstract.

## 5. Candidates

| # | Candidate | Disposition |
|---|---|---|
| C1 | Route (c) over a document: key-constrained proposals from prose kinds, each naming its fragment and digest so a change invalidates it, listed in the questionnaire, never promoted. Scored first on the public subjects' mapped documents with the mapper withheld, the mapper's assertions the truth (`rules.compatible`). Bar set before the run: no value for S2's declared gap, no silent resolution on S3, precision ≥ 0.9 on S1; missed, it parks. Structured kinds get a mapper instead | **Spike**, task-0139, m-6, behind m-8's prerequisites unless the pilot asks |
| C3 | A compact bundle form (verdict, policy, key headers, assertion lines, the conflict, stale, lapsed and suspect sections; no text, evidence, verification or approval lines), measured on CargoQuote S1–S7, 5 runs per form, one current model, as a deviation never written into `results/`. Hypothesis: M1 unchanged, M4 and M5 within the full form's range, prompt tokens ≤ 40 % of the full form's | **Spike**, task-0140, m-8; an `evidence_bundle` option only if it holds |
| C4 | GraphRAG as the adjacent category in doc-0012 §4, and the line *GraphRAG makes an answer faithful to its graph; knowgov says whether the graph may be built on* | **Document**, done: dated entry in doc-0012 §4 |
| C2 | Contradiction candidates across prose fragments, blocked by a shared entity, register node or glossary term; one model call per pair; info findings in the pre-load report or the questionnaire, never a gate input (decision-0002 gives a model no ruling) | **Park** until C1 has run; ground truth S4, D1/D2, negative control D3/D5 |
| C5 | M5 extended: the claim's value against the cited assertion's, mechanically | **Park**; useful if C3 loosens the inline evidence |
| C6 | A third party's GraphRAG graph (llm-graph-builder output) read as `inferred` | **Park**: not a system of record; only if a pilot runs one |
| C7 | Text-to-Cypher; a vector index in the store port; an LLM judge (DeepEval) in the record | **Reject**: the port (task-0003), decision-0008's typed read-only surface, the deterministic comparator; embeddings are not reproducible across model versions |
| C8 | DORA/FFIEC, or any finance-regulation corpus, as a public subject | **Reject**: the no-bank boundary; external law is not an organisation's design knowledge. Re-opening is the maintainer's |

## 6. What would reopen this

- A pilot whose documents are mostly prose kinds: C1 ahead of m-6.
- A buyer at the lighthouse raising the token cost: C3 urgent.
- C1 meeting its bar: C2 unparked.
- A GraphRAG graph already running at the pilot: C6 unparked.

Unchanged: the gate's verdict stays deterministic and no model output moves it; the record stays frozen; the store port stays as it is; no bank-related data, ever.
