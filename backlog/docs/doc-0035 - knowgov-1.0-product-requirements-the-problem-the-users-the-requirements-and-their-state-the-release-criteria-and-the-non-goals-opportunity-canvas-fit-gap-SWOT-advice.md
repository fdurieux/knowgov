---
id: doc-0035
title: >-
  knowgov 1.0 product requirements: the problem, the users, the requirements and
  their state, the release criteria and the non-goals; opportunity canvas,
  fit/gap, SWOT, advice
type: specification
created_date: '2026-11-09T11:21:00Z'
updated_date: '2026-11-09T11:21:00Z'
---
*A draft for the maintainer: nothing built, no task or decision minted, nothing decided. Drafted on 2026-11-09 by session `session_01HTAA1RLu8EC3tLChRMvA5r`, read on `main` `ee84120` (VERSION 0.8.0, Unreleased gathering for 0.9.0) with the register at v0.2.13 (`7980708`). Trigger: the maintainer, 2026-11-09: "Draft a PRD for knowgov itself", horizon 1.0.0, filed as a backlog doc. A PRD is a view: every internal claim restates a decision, a doc or a task and names it; the record stays `backlog/decisions/`, doc-0028 §4–§5 the gap ledger, doc-0012 the scores. External claims carry a numbered source in §12, from a deep-research run of the same date (fan-out search, three-vote adversarial verification). A claim the verification killed is not used. A claim the run extracted but left unvoted is used only after the drafter checked it against its page, and §12 says which.*

## Verdict

knowgov 1.0 is **the 0.9 contracts, frozen, proven on one foreign corpus** (decision-0016 point 4). The product is already built to that scope: each of the eighteen requirements in §5 has its core on `main`, and three carry an open part: FR-09's Desktop test (the maintainer's), FR-10's GitLab runner and FR-13's real installation (both at the pilot). 0.9.0 still waits on the validation pass's fifteen cut builds (G9-17, decision-0033) and the Desktop test (G9-3). After that, what 1.0 lacks is not code but evidence from outside the maintainer's hands:
- the pilot's go (task-0062 AC #2, #3);
- the ARIS route on a real installation (task-0063 AC #2, #5; the vendored `mapping/matrix.toml` at v0.2.13 has 16 rows, all `unverified`);
- a counterparty that can sign and support (task-0060). The PRD's job is therefore to make the 1.0 promise legible to the pilot's buyer and to hold the scope where decision-0016 and decision-0031 put it.

Positioning line (doc-0012): *"Before an AI agent builds on what your architecture says, know whether it is true."*

## 1. Problem

A model that writes code builds from whatever its documents say: what nobody decided, what two documents say differently, what a person guessed and nobody checked (`docs/guide.md` §1). Nothing in an organisation's delivery path tells the agent, or the reviewer after it, which of those statements it may build on.

Evidence from the record:
- **The mechanism works** (pumllint `docs/neo4j-governed-knowledge-evaluation.md`, one model, five runs per arm). S2 leaves one rule open (the screening service down): the baseline arm wrote code in 5 of 5 runs and failed the planted check each time; the governed arm stopped in 5 of 5 and asked. Across the blocked scenarios the governed arm wrote no code under BLOCKED in 20 of 20 runs.
- **Change is followed.** S6: a verified price moves 316.00 → 341.00; the store ends the four verifications resting on the changed text and marks the code built from them suspect; the gate blocks until the new values are verified.
- **The outcome is unproven.** "Supported for the mechanism, unproven for the outcome" (the same evaluation). doc-0012 §7: a null outcome makes the position a niche player with a strong method.
- **What the gate cannot see.** Knowledge that is consistently wrong: J-F D3 and D5 planted one defect in every document, the gate said QUALIFIED, and only the oracle caught it (17 and 20 failing scenarios). QUALIFIED is not safe (`docs/guide.md` §12).
- **An adopter cannot tell what holds.** Six contract changes in four days; the version counted changes and promised nothing (decision-0016 canvas). 0.9.0 names and freezes the contracts; 1.0.0 proves them.

## 2. Users and their jobs

| # | User | Job to be done | Where the record names them |
|--:|---|---|---|
| U1 | The lighthouse pilot's platform team | Run an instance on the organisation's own corpus; know which interfaces hold at procurement and at each upgrade | decision-0016 canvas; task-0062 |
| U2 | Architects and process owners (instance authors and approvers) | Keep identities, links and approvals in the register; answer the gaps routed to them; approve, since knowgov never does | doc-0001 §2; decision-0002; decision-0019 |
| U3 | A delivery squad and its product owner | Slice an initiative along the register's chain; read the gate as the definition of ready | doc-0022; doc-0034 |
| U4 | An AI coding or design assistant | Ask the gate before building; receive the verdict and its evidence; never write knowledge | doc-0001 §2; task-0056; decision-0008 |
| U5 | A reviewer or auditor | Replay a run; see on what each verdict was decided (task profile, register tag, build) | doc-0001 §2; decision-0029; decision-0031 |
| U6 | An integrator embedding a connector or the schemas | Build on Apache-2.0 surfaces without the GPL platform's obligations | decision-0016; decision-0026 |
| U7 | A security reviewer | Read what is read, stored and sent, and what the code does not enforce | `docs/security.md`; task-0059 |
| U8 | The maintainer | Cut releases whose number means something | decision-0003; decision-0016 |

Not a user: a person expecting knowgov to rank, estimate or plan (doc-0034, the handover's S11 boundary).

## 3. Goals and measures

| # | Goal at 1.0 | Measure | Baseline | Target | Source |
|--:|---|---|---|---|---|
| PG1 | An adopter can tell what holds across an upgrade | Contract changes after 0.9.0 and before 1.0.0 | six in four days (0.x) | none; each one a 0.10.0 restart | decision-0016 canvas, point 2 |
| PG2 | The contracts proven on a foreign corpus | The lighthouse instance runs on the 0.9 contracts | no foreign instance | one, unchanged | decision-0016 point 4; G1-1, G1-3 |
| PG3 | The incumbent's route verified | `mapping/matrix.toml` rows off `unverified`, with evidence | 0 of 16 (v0.2.13) | the ARIS row (decision-0006) | task-0063 AC #2, #5; G1-2 |
| PG4 | Someone can sign and support | A contracting entity and pilot support terms | none | both, and README's one line | task-0060; G1-4 |
| PG5 | The outcome becomes citable | Pre-registration before the pilot's first governed change: defect escape, rework, review time | not committed | committed, each expectation able to fail, null named an outcome | task-0057; G1-5 (an ordering, not a condition) |
| PG6 | The mechanism does not regress | The record comparator; no code under BLOCKED | 0 differing leaves; 20 of 20 | unchanged at every release | `demo/tools/compare_deterministic.py`; the evaluation |

Watched, not targets: the time from 0.9.0 to 1.0.0 and the pilot's breakages (decision-0016 canvas); declared gaps closed per review cycle, with the denominator (doc-0001 §2); the placement of record, 14 · 2.5 (doc-0012 §10), against S1's 17 · 6 on the first-scored rubric (doc-0012 §6); the CI budget, 12 minutes uncontended (task-0084, not a cut condition).

## 4. Non-goals

- **Approval.** knowgov never approves; approval is a person's act with a handle, a date and a record (`docs/guide.md` §1; decision-0019). A model's output stays `proposed` or `inferred`.
- **Being a system of record.** ARIS, Archi and the data model stay the authors; a node file never copies a tool's attributes (ieam-register CLAUDE.md; doc-0001 §0).
- **Planning.** No tracker write-back, no estimate, no prioritised plan (the handover's S11, doc-0034). The refinement-plan view is post-1.0 and parked (task-0254).
- **Executing business actions** (`docs/lighthouse-evaluation.md`, out of scope).
- **The running twin.** Operational data is the DTO category's; the optional join receives conformance as evidence, never produces it, and only when Loop B's trigger fires (doc-0012 §6 S3; doc-0010 §6).
- **A hosted service** (task-0060). An instance is private, inside the client's repositories, never pushed here; no bank-related data, ever.
- **Writes through the page.** The page is read-only and single-operator; a write is a pull request (doc-0001 §3; `docs/guide.md` §12).
- **Detecting consistent wrongness.** Out of the gate's reach by construction (J-F D3, D5); an oracle or a review catches it.

## 5. Functional requirements

State at `main` `ee84120`. "Contract" names decision-0016 point 3's surface the requirement rides on.

| # | Requirement | Contract | State | Evidence |
|--:|---|---|---|---|
| FR-01 | Read a subject's documents into statements, each with its source, status and verification | subject manifest; instance layout | built | `harness/`; `subjects/README.md` |
| FR-02 | Check the statements with the seven rules; one content-derived id per conflict on every store | JSON reports | built | decision-0020; task-0223 |
| FR-03 | Gate a task class: PROCEED, QUALIFIED or BLOCKED, exit 0/1/2, `--fail-on`, `--baseline`; the report names its task profile's digest, the register's tag and the build | gate exit codes and flags; `gate-report` schema v3 | built | task-0007; decision-0017; decision-0029 |
| FR-04 | Follow change: a changed document stales its statements and marks derived outputs suspect; a register change stales the keys resting on what it withdrew | gate report | built | task-0048; task-0122 |
| FR-05 | Review cadence: a verification lapses after its kind's review months, read as of a date | gate flags (`--as-of`) | built | decision-0005; task-0068 |
| FR-06 | Join the register: map keys to nodes; walk dependants, realisers and thread; say what retiring a node touches | MCP tools; register format v0.2.13 | built | decision-0028; task-0111; task-0118 |
| FR-07 | Read a proposed addition as if approved, without approving it; one slice per journey step, read over the task class's keys | MCP tools; `proposal-impact` schema | built | task-0130; task-0152; task-0241; task-0252 |
| FR-08 | Trace built code to the knowledge it rests on: suspect, drift, missing, unmapped | `trace-report` schema | built | task-0051; task-0124 |
| FR-09 | Serve agents read-only over MCP (stdio and Streamable HTTP), one reader for several subjects; runs through a second server | MCP tools and prompts | built; the wizard prompts in progress | task-0056; decision-0008; decision-0013; task-0148 (K10) |
| FR-10 | Gate pipelines and assistants: GitHub action, GitLab include, shell wrapper, fail-closed Claude Code hooks | `instance/ci/` inputs and outputs | built; GitLab runner at the pilot | task-0052; task-0102; task-0108 |
| FR-11 | Check an instance and a proposed subject; lint documents before the load (pumllint, Spectral, markdownlint, gplint, bpmnlint, dmnlint) | instance layout; `preload-report` and `subject-check` schemas | built | task-0135; task-0066; task-0082 |
| FR-12 | Capture what people know: a questionnaire per owner from the gate's gaps, review on cadence; an answer reaches `proposed` until reviewed; an attestation bound to the Versions it attests | capture and review formats | built | decision-0002; decision-0004; decision-0019 |
| FR-13 | Land a system of record's export as a dated, append-only mirror with MANIFEST and RECONCILE; a vanished id is stale, never deleted | instance layout; `connectors.toml` | built on the synthetic export; the real installation open | decision-0010; task-0063 |
| FR-14 | One store port, two adapters (Neo4j, rdflib); a writer's unit published whole; a read from one generation | store port | built | decision-0014; SNAP-01..10 |
| FR-15 | Run model-written code contained: a sibling worker, no network, no secrets | `KG_*` settings the table marks contract | built; Linux with Landlock | decision-0012; decision-0015 |
| FR-16 | Optional assistant arms through one OpenAI-compatible endpoint, off until configured | `KG_*` settings | built | task-0005; doc-0001 §0 |
| FR-17 | Reverse-engineer an existing code base into a subject and find what nobody wrote down | kit fields; routed gaps | built | decision-0018; `docs/reverse-engineering.md` |
| FR-18 | Show it: the dashboard, the register view, the impact walk; four HTTP routes as the page's API | page HTTP API | built | decision-0030 |

## 6. Non-functional requirements

| # | Requirement | State | Source |
|--:|---|---|---|
| NFR-01 | **Contract stability.** 0.9.x fixes only; any contract change 0.10.0. From 1.0.0 a deprecation lasts one further minor and ninety days; removal only in a major. The surface is decision-0016 point 3's, with its settings row as decision-0033 choice 1 amends it | accepted | decision-0016 points 2, 3, 5, 7; decision-0033 (#410) |
| NFR-02 | **Format versions** on every instance input; a missing one reads as 1 in every release; a higher one refused, exit 2; the trace ledger and the proposal overlay included | built; the ledger and overlay a cut build | decision-0023 and A1; task-0236; decision-0033 choice 6, task-0280 |
| NFR-03 | **Reproducibility.** The deterministic run equals the record; one wall-clock read decides an outcome, refused under `KG_CLOCK=pinned` | built | task-0075; the comparator |
| NFR-04 | **Security.** Page token beyond localhost; `KG_MCP_TOKEN` for a wider bind; HTTP refusals close the connection; model endpoint off by default; what the code does not enforce stated | built; the security pack done | `docs/security.md`; task-0059; task-0196 |
| NFR-05 | **Data boundary.** A private instance never leaves the client's repositories; synthetic public content only | standing | CLAUDE.md, Boundaries |
| NFR-06 | **Licence.** Platform GPL-3.0-or-later; `harness/schemas/`, `instance/` and any SDK Apache-2.0 | decided; the re-stamp after counsel | decision-0026; task-0058 |
| NFR-07 | **Platforms.** The image on CPython 3.12; contained execution on Linux with Landlock; the tested platforms and clients stated | the statement open | K1; task-0239 (GAP-06) |
| NFR-08 | **Capacity.** A Neo4j load forecast over the server's transaction memory refused before its first write | built; heap sized per instance | task-0176; K4 |
| NFR-09 | **Support.** The latest minor, best effort, until a counterparty exists | accepted | decision-0016 point 6; task-0060 |
| NFR-10 | **Delivery hygiene.** A PR's `rdflib` and `stack` within 12 minutes uncontended; the record never subset to meet it | partly shown | task-0084; task-0180 |

## 7. Release criteria

**0.9.0, the contract freeze** (decision-0016 point 1; doc-0028 §4, its status table at `6d27961` read forward to `ee84120` by task state). Met: G9-1, G9-2, G9-4, G9-5, G9-6 (bar K10), G9-7 to G9-16 (task-0242 to task-0246 Done since the table, as are task-0241 and task-0252). Open: G9-3 (task-0148 In Progress, its AC #5 the maintainer's Desktop test, which also settles K10) and G9-17 (task-0256, the contract validation pass, decision-0032; only its contract-bearing findings hold the cut). The pass (task-0256, In Progress) found 16 distinct contract-bearing findings and 40 fix-only ones (decision-0033, Context). Fifteen builds hold the cut: task-0257 to task-0262, which keep promises the documents already make, and task-0275 to task-0283, decision-0033's nine choices (accepted 2026-11-09, "all as advised"; landed in #410). Then comes the bounded re-probe of what those builds touch (decision-0032 point 4), and the release PR with its Known limits. The fix-only findings, task-0263 to task-0272, go to 0.9.x (decision-0032 point 3), as does task-0274 (SNAP-04, decision-0014 Amendment A1, built in #415, open): it is fix-only, so it holds nothing.

decision-0033's choices that a buyer will read as contract content:
- Choice 1 amends decision-0016 point 3. A `KG_*` setting is a contract when `instance/README.md`'s one settings table marks it one (task-0275). The maintainer confirms the rows in that build's PR.
- Choice 2: an on/off setting takes `1` for on, and `0`, empty or unset for off. Anything else exits 2 and names the setting (task-0276).
- Choice 3: the image contract is `:vX.Y.Z` per release and `:latest` for the last main. `:<short-sha>` is a build of main, not a contract (task-0277).
- Choices 4, 5 and 6:
  - `keys` is reserved, and task-class names must match `[a-z][a-z0-9_-]{0,31}` (task-0278);
  - a named register that cannot be read exits 2 (task-0279);
  - decision-0023's version rule extends to the trace ledger and the proposal overlay (task-0280).
- Choices 7, 8 and 9:
  - MCP arguments are validated against each tool's `inputSchema` before dispatch, -32602 on any violation, and `POST /api/run` refuses unknown fields (task-0281);
  - a suspect output blocks only the class whose keys its statements sit on (task-0282);
  - `held_keys`' `gate` equals `gate_verdict`'s on the same store (task-0283).

**1.0.0, the contracts proven** (decision-0016 point 4; doc-0028 §5):
1. G1-1 and G1-3: the lighthouse's instance has run on the 0.9 contracts with no contract change.
2. G1-2: the ARIS route verified on its installation (task-0063 AC #2, #5).
3. G1-4: a support counterparty exists (task-0060).

Ordered before the pilot, not a condition: G1-5, the outcome study pre-registered (task-0057). At the pilot, not blocking: G1-6, the gate-unavailable case (task-0103) and the GitLab include on a runner (task-0108).

**Acceptance protocol, not release conditions** (decision-0031): the handover's A01–A18 and AT01–AT12 become the lighthouse's protocol; GAP-03 to GAP-05 are minted at the pilot's go. 1.0 can therefore be cut with A14 (security sign-off) or A18 (upgrade proof) unproven; the decision's advice names a narrow amendment as the route if either should bind.

## 8. Known limits at 1.0

Named by decision-0024 (thirteen), decision-0021 (K21) and doc-0028 §10. The ones a buyer will ask about first:
- K1: contained execution needs Linux with Landlock; Docker Desktop for Mac 4.48.0 has none.
- K8: a file-backed store's writers need POSIX `flock` on a local disk: no Windows, no network file store.
- K11: a proposal's slices are as fine as the register's links.
- K16: the connector has run only on the synthetic export (tasked: task-0063).
- K20: the hooks see Edit and Write, not a shell command writing the same file.
- K21: an execution verification is not bound to the code the suite last passed on.
- U1: a store-backed tool answers for the subject whose scenario the store holds (tasked: task-0164).
- And by construction: QUALIFIED is not safe.

Not a limit, but open beside the cut: SNAP-04 on Neo4j, where a reader could see a generation before all of its data (task-0274, decision-0014 A1, built in #415, open). It is fix-only. Until it lands, FR-14's "a read from one generation" has that window on Neo4j.

## 9. Risks and assumptions

| Risk | Likelihood signal | Response | Source |
|---|---|---|---|
| The pilot needs a contract change in its first week; 0.10.0 follows 0.9.0 and the freeze reads as theatre | the pilot's corpus is foreign by definition | the restart rule, stated in advance | decision-0016 SWOT |
| 1.0's date waits on a third party | task-0062: AC #1 met 2026-11-04 (ARIS, decision-0006); AC #2 and #3 wait for the go | fallback (a) after 0.9.0: 1.0 on a stated quiet period, the pilot's first breaking need 2.0.0 | decision-0016 Advice |
| 1.0 read as product maturity while E2–E4 stay low | placement 14 · 2.5 | say what 1.0 promises in the adopter register (task-0181, done) | decision-0016; doc-0012 §8 |
| The outcome study is null | not yet run | pre-register so a null is citable; the position becomes a niche with a strong method | doc-0012 §7; task-0057 |
| An incumbent gates agents on verified facts (LeanIX, Palantir) or CALM ships statement-level provenance | watch CALM 1.3 and the incumbents' agent surfaces | plug in first (route B), standard second (route A) | doc-0012 §6, §7 |
| Two upstream 0.x formats move under an instance | ieam-register and pumllint at 0.x | the release vendors and tests one register tag; another is untested | decision-0028 |
| Assumption: one foreign corpus is enough evidence for 1.0 | doc-0012 S3 meant more than one | one pilot is the floor, not S3 | decision-0016 fit/gap |

## 10. Context: market, regulation, PRD practice

External, dated, numbered to §12; **V** marks a vendor or vendor-affiliated source. Every step from a source to knowgov is this doc's inference and is labelled so. "DORA (Google)" is the DevOps Research and Assessment programme; "DORA (EU)" is the Digital Operational Resilience Act.

### 10.1 Market and comparables

- **Use without trust.** Stack Overflow 2025 [1]: 45.7% distrust the accuracy of AI output, 32.7% trust it (33,244 responses); the top frustration (66%) is "AI solutions that are almost right, but not quite"; 45.2% say debugging AI-generated code takes more time. DORA (Google) 2025 [2, V]: 90% use AI at work; 30% report little or no trust in AI-generated code. Both measure trust in output, not in the context an agent receives; the step from one to the other is this doc's.
- **More change without control loses stability.** DORA (Google) 2025 [2, V]: AI adoption "does continue to have a negative relationship with software delivery stability"; "Without robust control systems, like strong automated testing, mature version control practices, and fast feedback loops, an increase in change volume leads to instability." The AI Capabilities Model [3, V]: "A healthy data ecosystem, characterized by high-quality, easily accessible, and unified internal data, substantially amplifies the positive influence of AI adoption on organizational performance"; quality and access are scored as separate capabilities. Correlational and self-reported. Reading the gate as one of those control systems is this doc's inference.
- **Speed unsettled.** METR [4]: the early-2025 trial found AI made tasks take 19% longer (CI +2% to +39%). The follow-up gives "an unreliable signal": −18% (CI −38% to +9%) for returning developers and −4% (CI −15% to +9%) for new ones, with 30% to 50% of developers withholding tasks. No settled uplift is citable; PG5 (task-0057) measures defect escape, rework and review time, not speed.
- **More context is not better context.** Gloaguen et al. [5]: context files "do not generally improve task success rates, while increasing inference cost by over 20% on average" (the cost figure for LLM-generated files); repository overviews "are not helpful"; developer-written files beat generated ones by about 7% (p = 0.038). Anthropic [6, V]: "the smallest possible set of high-signal tokens"; recall degrades as the window fills. Neither tests validated or current context as such. knowgov's core hypothesis, that held, validated and current knowledge improves the outcome, has no external measurement; PG5 is where it gets one.
- **Defects are requirement failures first.** Zhang et al., ISSTA 2025 [7]: Task Requirement Conflicts are the largest hallucination class (43.53%), Functional Requirement Violation alone 36.66%; six mostly small 2023–24 models, Python, no agentic tooling. This supports FR-08's trace back to requirements and says nothing about freshness.
- **The EA category moves to agents.** Forrester [14]: the major EAM vendors grew 13–19% a year over three years, "fueled by investment and M&A"; "AI has moved from augmenting EA work to orchestrating it"; an estimated 15% of clients are mature enough for outcome-based architecture, and they want "tooling that connects strategy to execution". The source is an analyst's blog; the report itself was not read.

Comparables, as their own pages document them:

| Comparable | What it gives an agent | Provenance, validation and freshness of that context | Source |
|---|---|---|---|
| Ardoq AI Gateway (MCP server), GA 30 Sep 2025 | queries over the EA repository: reports, dashboards, viewpoints, metamodel awareness; the preview "Secure, Read-Only Access" | asserts "live, governed data" and "Logging, analytics, and accuracy evaluations"; no method or result published; no adoption figures | [8, V] |
| SAP LeanIX MCP server, 4 Nov 2025, "available to all SAP LeanIX customers" | fact sheets, quality seals, indicators; Copilot Studio, Cline, Claude Desktop, custom LLMs | nothing on provenance or freshness; one example prompt writes ("Create a GDPR survey and send it to all application owners in Germany") | [9, V] |
| Palantir Ontology MCP | object types, action types and query functions as MCP tools; reads and predefined writes | agent safety framed as access control (application restrictions); the overview is silent on context provenance and freshness. Foundry has lineage and health checks elsewhere: no claim that Palantir lacks them | [10, V] |
| coArchi and coArchi2 (Archi) | an ArchiMate model kept in Git | "you shouldn't use merge, pull requests or similar features from your Git server as this would most certainly lead to model corruption"; coArchi2: "pull requests and Git stash are not supported". At least one public model is reviewed by PR regardless: unsupported, not impossible | [11] |
| GitHub spec-kit, Kiro, Tessl (spec-driven development) | a spec before the code; Kiro's tasks "trace back to the requirement numbers"; "steering" files | spec-kit "spec-first only, not spec-anchored over time"; the spec maintenance strategy "often ... left vague or totally open"; "I frequently saw the agent ultimately not follow all the instructions" | [12] |
| GraphRAG (Microsoft Research) | community summaries over an entity graph | the original evaluation scored comprehensiveness, diversity and empowerment, not faithfulness; fabrication rates named as further work. Later papers measure GraphRAG faithfulness | [13, V] |

Reading for knowgov (inference): two EA incumbents have exposed their repositories to agents over MCP since late 2025 [8, 9], so route B's "plug in first" (doc-0012 §7) has a surface to plug into. In the pages read, none of the six documents a check, before the agent builds, that what it is handed is approved, validated and current. doc-0012 §7's threat stands: Ardoq already asserts accuracy evaluations [8]. The research verified nothing on ARIS's agent surface, Sourcegraph-style context or code-graph MCP servers, and this doc claims nothing about them.

### 10.2 Regulatory and audit drivers

Generic to regulated enterprises. DORA (EU) binds EU financial entities only; it is the exemplar regime here, not a claim that it binds a given pilot.

- **Verification and independent approval of every change.** Delegated Regulation (EU) 2024/1774, Art. 17(1) [15], applying since 17 Jan 2025. ICT change management covers all changes to software, hardware, firmware, systems or security parameters. It includes "(a) a verification of whether the ICT security requirements have been met" and "(b) mechanisms to ensure the independence of the functions that approve changes and the functions responsible for requesting and implementing those changes". Point (d) requires the change to be documented, and point (g) allows approval after implementation for emergency changes only. Nothing in it depends on how a change was produced. Caveats:
  - an entity under the simplified framework follows Art. 38(2) instead;
  - the procedures are proportionate (Art. 1);
  - the verification is against ICT security requirements, not against the knowledge an agent used;
  - independence is required between functions, not between named people.
- **The supervisor's reading.** AFM, 20 Dec 2024 [16]: "There must be a complete audit trail in place, demonstrating the separation of duties. It is important to document IT changes and the approvals of these changes. This is especially true if change approval is given in meetings or if multiple systems are used for change management, such as a pipeline and service management system." The sample is narrow: a few Dutch proprietary traders.
- **One record of links between assets and business functions.** RTS Art. 4(2)(b)(viii) [15] requires records of "the links and interdependencies among ICT assets and the business functions using each ICT asset". The AFM [16] asks for "extra attention from entities that use multiple records and overviews for their ICT assets".
- **EU AI Act.** Art. 4, AI literacy, has applied since 2 Feb 2025 [17]. Regulation (EU) 2026/1744, the Digital Omnibus on AI (OJ 24 Jul 2026, in force 27 Jul 2026), changes three things:
  - providers and deployers now "take measures to support the development of AI literacy", with no specific level to guarantee;
  - the stand-alone Annex III high-risk obligations move to 2 Dec 2027;
  - Annex I's move to 2 Aug 2028 [17].
  These were read through secondary reproductions, not the Official Journal text. Whether a coding or design assistant is itself a high-risk system was not established, and this doc does not claim it.
- **ISO/IEC 42001:2023** [18] (18 Dec 2023, edition 1) specifies requirements and guidance for an AI management system within an organisation that provides or uses AI-based products or services. A lead auditor's pairing (ISACA, 8 Dec 2025) [19]: "The EU AI Act is the rulebook and ISO/IEC 42001 is the operating system that makes compliance repeatable and auditable". It recommends an "AIMS evidence index", "a controlled register in the AIMS that links each requirement to its evidence location": "Article 43 requirement X -> Test Y -> Evidence Z". The standard's own text was not read.

Reading for knowgov (inference). These sources ask for:
- verification before a change;
- approval independent of the author;
- a complete trail of who approved what;
- one record of the links between assets and business functions;
- requirement-to-evidence traceability.

knowgov answers each in form:
- the register's approval, whose approver is never the author (decision-0019);
- the gate's report naming what it decided on (decision-0029);
- the register's typed links (decision-0028);
- the trace (FR-08).

None of these is a verification against ICT security requirements, and knowgov does not make an organisation compliant. It produces records an organisation can use as evidence, and the buyer-facing claim stops there.

### 10.3 PRD practice

- Rachitsky's list of nine templates [20] names, among its favourites, the Square template's "Non-Goals" section, the Asana brief's "problem statement framework", and a one-pager's "focus on success criteria and risks". None is written for developer or platform tools.
- The Kubernetes KEP template [21] is a platform's design document:
  - Non-goals: "Listing non-goals helps to focus discussion and make progress".
  - Risks and mitigations, drawbacks, and alternatives considered.
  - Graduation: "Beta criteria must include all functional, security, monitoring, and testing requirements"; "GA criteria must not include any functional, security, monitoring, or testing requirements"; and "Generally we also wait at least two releases between beta and GA/stable".
  - A production readiness review, approved before a release.
- The Command Line Interface Guidelines [22]: "Return zero exit code on success, non-zero on failure"; interfaces must not change "without a lengthy and well-documented deprecation process"; "Keep changes additive where you can."

How this doc follows them:
- the sections run problem (§1), users and jobs (§2), goals with baselines and targets (§3), non-goals (§4), requirements with state and evidence (§5, §6), release criteria (§7), limits (§8), risks (§9), open questions (§11);
- decision-0016 already has the KEP's graduation shape. 0.9.0 holds every contract and its build, as beta holds every functional requirement. 1.0.0 adds only evidence from use, as GA adds only adoption. The difference is how the wait is measured: in releases for the KEP, in a run on a foreign corpus for decision-0016. No change is proposed (Advice 4);
- NFR-01 and FR-03 are the CLI guidelines' contract, made stricter: three exit codes, and a deprecation that lasts a further minor and ninety days.

The run verified nothing from Cagan's, Atlassian's or Intercom's own pages, so none of them is cited.

## 11. Open questions for the maintainer

1. The pilot organisation's go, its sector and its slice (task-0062 AC #2, #3).
2. The contracting entity and support terms (task-0060).
3. The buyer-facing name (task-0061; decision-0025 keeps the technical name).
4. Counsel's answer on the re-stamp (task-0058 AC #2, #3).
5. Whether A14 or A18 should bind 1.0 by a narrow amendment (decision-0031 Advice).
6. `rdflib-readers` as a required check (CLAUDE.md, Pull requests).
7. decision-0011, still proposed: whether a reverse-engineered kit becomes the living spec.

## Opportunity canvas (of this PRD)

| Box | Content |
|---|---|
| Problem | What knowgov 1.0 is, for whom and on what conditions is spread over thirty-two decisions, thirty-four briefs and a 1,900-line changelog. The pilot's procurement will ask in one sitting (decision-0016 SWOT, O1) |
| Who, and when | U1 at procurement and at each upgrade; the pilot's sponsor at the go (task-0062 AC #2); U5 and U7 before sign-off; the maintainer at the 0.9.0 and 1.0.0 release PRs |
| Today | The contracts at 1.0 are stated for an adopter (`instance/README.md`, task-0181); the gap ledger is doc-0028; the positioning doc-0012; no one page says problem, users, scope, measures and non-goals together |
| Solution | This doc: a view that quotes the record, with requirement ids FR/NFR an acceptance protocol can cite (decision-0031) |
| Measure | Questions at the pilot's go answered by pointing here; zero claims here the record lacks (the fit/gap below); the doc refreshed, or marked stale, at each release PR |
| Cost | One doc; a refresh per release; an adopter-register version for the buyer at the pilot's go |
| Risk | A second record: a PRD read as the authority over decision-0016. Mitigated by the header, by citing every row, and by advice point 2 |

## Fit/gap

| Must satisfy | How this doc meets it | Gap |
|---|---|---|
| One record per thing (CLAUDE.md, Record and views) | quotes and cites; decides nothing; the decisions and doc-0028 stay the record | it can drift as the record moves: a refresh per release |
| decision-0016 points 1–7 | §7 and NFR-01 restate them unchanged | none |
| decision-0031 (b) | §7: A01–A18 and AT01–AT12 are the lighthouse's protocol, not conditions | none |
| The four parts (maintainer, 2026-11-06) | this section and the three after it | none |
| A recognised PRD form (§10.3) | problem, users and jobs, goals with measures, non-goals, requirements with state, release criteria, risks, open questions | no personas researched with real users: U1–U8 are the record's roles, not interviews; the pilot supplies them |
| External claims verified and dated (§10, §12) | every external line numbered to a dated source, vendors marked, inference labelled, killed claims listed | the run verified nothing on ARIS's agent surface, Sourcegraph-style context, code-graph MCP servers, model-risk guidance or Cagan's, Atlassian's and Intercom's pages; this doc claims nothing about them |
| The adopter register for a buyer (CLAUDE.md, Registers) | none: this doc is the maintainer's | an adopter version at the pilot's go |
| No bank-related data; J-F kept private | synthetic subjects only; J-F named by the public subject `jef_data_load` and its record | none |
| Claims checkable against `main` | every FR and NFR names its task or decision | the state is `ee84120`'s; it ages |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** the scope is already built and tested to the contract list; each requirement has an id, a surface and its evidence; the non-goals are the record's own and sharp (no approval, no planning, no system of record) | **W:** every external user is a role, not a measured person; the measures that matter to a buyer (defect escape, rework, review time) have no baseline until task-0057; E2 adoption is zero |
| **External** | **O:** regulated buyers must verify each change, keep its approval independent of its author and show the trail (§10.2), and the register's approvals and the gate's reports are records of that shape; two incumbents' MCP servers (§10.1) give "plug in first" a surface to plug into; and no comparable read documents a check on the context it hands an agent (§10.1); the PRD hands the pilot a ready requirement list to accept against | **T:** an incumbent adds verification to its agent surface (doc-0012 §7; Ardoq already asserts accuracy evaluations, §10.1); the core hypothesis has no external measurement yet (§10.1), so a null PG5 has nothing to lean on; 1.0 read as maturity (decision-0016 SWOT); the pilot's go slips and 1.0 with it |

## Advice

The drafter recommends:
1. **File this as doc-0035, a view.** It decides nothing and amends nothing. Read it as the one page that says what 1.0 is; the authority stays decision-0016, decision-0031 and doc-0028.
2. **Refresh it in each release PR, or mark it stale there.** A PRD that ages silently becomes the second record the rule forbids. The 0.9.0 release PR is the first refresh: G9-3 and G9-17 closed, the Known limits final.
3. **Write the adopter version at the pilot's go**, not before. Its users U1–U8 become the pilot's people, its measures take task-0057's baselines, and A01–A18 cite FR/NFR ids.
4. **Change no scope for it.** Every gap the PRD shows is either a pilot item (G1-1 to G1-6) or a 1.0 limit already named. Nothing here argues for a contract change during the freeze.

Against it: a PRD written before the first user interview is the record's view of its users, not the users' own; the pilot will correct it, and point 3 is when.

## 12. Sources

Read on 2026-11-09. Flags:
- **3v**: passed the research run's three-vote adversarial verification (at least 2 of 3 to keep).
- **d**: extracted by the run but not voted on; the drafter then checked the quoted text against the page, in a single read.
- **V**: a vendor or vendor-affiliated source.

1. Stack Overflow, *2025 Developer Survey: AI*, Jul 2025. https://survey.stackoverflow.co/2025/ai (3v; independent of tool vendors, self-selected sample)
2. N. Harvey, D. DeBellis, *Announcing the 2025 DORA report*, Google Cloud blog, 23 Sep 2025. https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report (3v, V)
3. *Introducing DORA's inaugural AI Capabilities Model*, Google Cloud blog, 23 Sep 2025; *Healthy data ecosystems*, dora.dev, updated 8 Dec 2025. https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model · https://dora.dev/capabilities/healthy-data-ecosystems (3v, V)
4. METR, blog post updating its developer-uplift study, 24 Feb 2026. https://metr.org/blog/2026-02-24-uplift-update/ (d; independent)
5. Gloaguen et al. (ETH Zurich, LogicStar.ai), *Evaluating AGENTS.md*, arXiv 2602.11988 v3, 29 Sep 2026. https://arxiv.org/abs/2602.11988 (3v; academic, workshop-reviewed; v1 worded more strongly, cite v3)
6. Anthropic Applied AI, *Effective context engineering for AI agents*, 29 Sep 2025. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (3v, V)
7. Zhang et al., repository-level code-generation hallucinations, ISSTA 2025, arXiv 2409.20550 v2. https://arxiv.org/abs/2409.20550 (3v; peer-reviewed)
8. A. Bhatt, Ardoq blog, the AI Gateway (MCP Server) GA announcement, 30 Sep 2025. https://www.ardoq.com/blog/announcing-mcp-ga (d, V)
9. SAP LeanIX blog, the MCP server announcement, 4 Nov 2025. https://www.leanix.net/en/blog/mcp-server-for-sap-leanix-solutions (d, V)
10. Palantir, *Ontology MCP: overview*, undated (© 2026). https://palantir.com/docs/foundry/ontology-mcp/overview/ (3v at 2–1, V)
11. archimatetool, coArchi wiki *Understand the Basics* (edited 27 Oct 2026) and coArchi2 wiki *Technical Considerations* (edited 6 Nov 2026). https://github.com/archimatetool/archi-modelrepository-plugin · https://github.com/archimatetool/archi-modelrepository-plugin2 (3v; the project's own pages)
12. B. Böckeler, *Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl*, martinfowler.com, 15 Oct 2025. https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html (d; practitioner, not the tools' vendor)
13. D. Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, arXiv 2404.16130 v2, 19 Feb 2025. https://arxiv.org/abs/2404.16130 (3v, V: Microsoft Research)
14. S. Vanrechem, Forrester blog on the Enterprise Architecture Management Suite Landscape, Q4 2025, 7 Jan 2026. https://www.forrester.com/blogs/the-enterprise-architecture-management-suite-landscape-q4-2025-is-out (d; analyst)
15. Commission Delegated Regulation (EU) 2024/1774 (RTS on the ICT risk-management framework), OJ L, 25 Jun 2024, Art. 1, 4(2)(b)(viii), 17(1), 38(2); EUR-Lex CELEX 32024R1774 is the authoritative text, read through Springlex's reproduction. https://www.springlex.eu/en/packages/dora/rts-rmf-regulation/article-17/ (3v)
16. AFM, *DORA pilot: proprietary traders*, 20 Dec 2024, §2.2 points 2 and 3. https://www.afm.nl/~/profmedia/files/rapporten/2024/dora-pilot-proprietary-traders.pdf (3v; supervisory)
17. Regulation (EU) 2024/1689 (AI Act), Art. 4; Regulation (EU) 2026/1744 (Digital Omnibus on AI), OJ 24 Jul 2026, http://data.europa.eu/eli/reg/2026/1744/oj. Read through https://artificialintelligenceact.eu/article/4/ and https://www.nicfab.eu/en/posts/digital-omnibus-ai-official-journal/ (d; secondary reproductions)
18. ISO/IEC 42001:2023, *Information technology: Artificial intelligence: Management system*, ed. 1, 18 Dec 2023; IEC webstore listing. https://webstore.iec.ch/publication/90574 (d; the abstract only)
19. G. Reddy, ISACA industry news on pairing ISO/IEC 42001 with the EU AI Act, 8 Dec 2025. https://www.isaca.org/resources/news-and-trends/industry-news/2025/isoiec-42001-and-eu-ai-act-a-practical-pairing-for-ai-governance (d; practitioner)
20. L. Rachitsky, Lenny's Newsletter issue 37, his favourite templates, 4 Aug 2020. https://www.lennysnewsletter.com/p/my-favorite-templates-issue-37 (d)
21. Kubernetes, *KEP template* (`keps/NNNN-kep-template/README.md`, living on master). https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md (d)
22. *Command Line Interface Guidelines*. https://clig.dev/ (d)

The run killed these claims (votes in brackets), and this doc does not use them:
- coArchi's storage layout (0–3);
- that DORA (Google) measured internal-data access raising code quality (1–2);
- Stack Overflow's 84% adoption and about 60% sentiment figures (0–3);
- that GraphRAG shows vector RAG failing on global questions (1–2);
- that Project Context Conflicts show context gaps causing defects (0–3).
