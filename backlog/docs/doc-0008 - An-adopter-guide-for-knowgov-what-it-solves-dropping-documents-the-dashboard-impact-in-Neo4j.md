---
id: doc-0008
title: >-
  An adopter guide for knowgov: what it solves, dropping documents, the
  dashboard, impact in Neo4j
type: specification
created_date: '2026-11-02T23:32:00Z'
updated_date: '2026-11-02T23:35:00Z'
tags:
  - brief
  - guide
  - fit-gap
  - canvas
  - swot
  - impact
---
*2026-11-02. Maintainer register for the verdict, the findings and the analysis; the sample guide section in the adopter register. A study: nothing is built. The trigger was the maintainer's ask of this date, an adopter guide covering the problem, the route for documents, the dashboard and impact in Neo4j; the deliverable is this brief, not the guide. Every command was run on `main` at `45a6720` in a Python 3.12 venv with the pins `harness.yml` installs: the page on the in-memory store (`KG_STORE=rdflib`, port 8080) and on Neo4j 5.26.0 community from its tarball with Java 21 (port 8081). Run outputs stayed in the session's scratchpad; only this brief is committed. Public, synthetic content only.*

**The screens, field by field, with screenshots:** [knowgov dashboard, screen by screen](https://claude.ai/artifact/RNpHTUDJW93AXoWCDYTvtj) (artifact page; a view, not the record).

## Verdict

Sense: write the guide, as one page, `docs/guide.md`, linked from `demo/README.md`. The adopter material exists and is accurate but is spread over four files written for four readers (the demo's viewer, the instance operator, the subject author, the page's own wording rules); nothing tells an adopter in one place what problem knowgov solves, in what order to do things, or how to ask the graph what a change touches. Three findings change what the guide can promise today:

1. **The impact walk starts only from applications, processes and journeys.** `tools/impact.py`'s `FORWARD` table follows `supports`, `delivers`, `realizes`, `is_supported_by` (inverse) and `concerns`; from a capability (CAP-0002), an information entity (ENT-0003), a product (PRD-0002), an organisation unit or a journey step (JRN-0003) it walks 0 edges. `crud`, `manages`, `requires`, `owns` and `maps_to` are never followed. The page says so honestly ("No link starts at this node in a direction the walk follows"), but an adopter asking "what touches the Quote entity?" gets nothing. Two read-only Cypher queries, run here, answer the capability and the EDM questions over approved links (sample section below). Whether the register's walk should grow is the register's decision, not this backlog's.
2. **A module is in the register; its code is not.** QuoteAPI is APP-0002, kind `module` under the applications taxonomy, and the walk from it is the page's default (5 edges, PRD-0002 and JRN-0002 reached). The brief's premise that a module is no register taxonomy holds for the *code* module (`reference_impl.py`'s QuoteAPI) and the kit's entity `QuoteAPI` (kind `service`), which the store holds and nothing joins to APP-0002 except `register_map.toml`, which is not projected. One query joins them today through `REG_CITES` → `Artefact` by path: from APP-0002's approved links to the documents they cite, the statements those documents support and the derived code (REL-08001 → `contract/openapi.yaml` → 10 statements → `derived:S1:G:run1`). It works at document grain, not at anchor grain. A change *to code* reaches nothing: the store's direction is document → statement → code.
3. **No step checks a document's form before the load.** The instance layout, `tools/check_instance.py`, the load's `unmapped` report and the gate CLI exist; a linter does not run anywhere on the route. The pre-load gate below is PROPOSED: a pull request into `artefacts/<kind>/` whose CI runs the kind's linter under the gate contract, the load reading only the merged tree. It is a different gate from `harness/gate_cli.py` and replaces nothing.

Executed: the dashboard on both stores, every screen captured; S2 deterministic on rdflib (BLOCKED, identical on all 108 compared fields with `results/S2`); S6 deterministic on Neo4j (4 invalidated, BLOCKED then PROCEED); the register projected at v0.2.3 (56 nodes, 65 links, 377 relationships); `tools/impact.py` from nine nodes; the saved `register-impact` from seven starts, edge for edge the same as `impact.py`; `/api/register/impact/<id>`; the panel's Browser guide clicked and played in Browser 5.26; the S6 invalidation query; three proposed queries; `gate_cli.py --scenario S2` (exit 1); `tools/example_instance.py` (layout holds). Not executed: an Arms run (no key was set), the J-F oracle, a Neo4j stack under Docker (no daemon).

## 1. The problem, from the record

- **What breaks without it.** An assistant given the documents builds from whatever they say, including what nobody decided. CargoQuote S2 (pumllint `docs/neo4j-governed-knowledge-evaluation.md`, one model, n = 5): the outage rule is declared open (REQ-06, OD-1); arm B, the documents only, generated code with assumptions in 5 of 5 runs and failed `screening_down_hold` 5 of 5 (10/11 each); arm G, given the gate's BLOCKED and its bundle, abstained 5 of 5 and named the open item. The record also has arm B adopting an unreviewed machine note as a decision 4 of 5 (S5) and resolving an undeclared contradiction by an invented precedence 4 of 5 (S4). The governed arm never generated under BLOCKED, 20 of 20 cells.
- **What breaks even with good documents.** The degradation test (J-F, `recreate_experiment/degradation-2026-10-28`, quoted in Legible's v0.3 change note): six of fifteen planted defects reached the code, each through the highest-ranked layer that stated the behaviour. In knowgov's J-F subject the gate says PROCEED for C and D1 and QUALIFIED for D2 to D5; in D3 and D5 the defect is consistent in every layer and reached the code (the pristine oracle fails 17 and 20 scenarios). The gate sees missing, contradictory, unverified and stale knowledge; it cannot see knowledge that is consistently wrong. The guide must say this in its first page.
- **What changes over time.** S6: a verified tariff number changes (P2 surcharge 316.00 → 341.00); the store invalidates four assertions, ends their verifications, marks `derived:S1:G:run1` suspect and blocks until re-verification. Files alone cannot list what the change touched.
- **Why a separate platform.** decision-0001: the demo leaves pumllint so that private instances never sit beside a public GPL linter; doc-0001 frames the objective: a client's own register and artefacts answered by the same queries, knowledge in people's heads captured or declared a gap, a model's output never promoted. The capture path is in doc-0007 (the John Doe walkthrough, branch `claude/capture-walkthrough`, not merged when this was written); the guide points to it and does not repeat it.

## 2. Fit/gap of the existing adopter documentation

| File | Reader it is written for | What exists | What is missing for an adopter | What would move to the guide |
|---|---|---|---|---|
| `demo/README.md` (920 lines) | a viewer of the public demo; an operator on a Mac or EC2 | what the page shows, what Neo4j holds and who writes it, the three modes, the Arms models table, the gate CLI, start-up, keeping vendored copies current | the problem in one page; an order of work; impact beyond the default start; the second kind of impact as a task, not a scenario; a pre-load check | "What Neo4j holds…" and "The gate as a command" summarised with links back; the page tour replaced by a link to the screens section; the start-up blocks stay |
| `instance/README.md` (138) | the operator of a private instance | layout, kinds and mappers, `check_instance.py`, the example instance, capture, the instance compose file | which linter checks each kind; how a document gets into `artefacts/` (by whom, through what review); what the load does with a malformed file | the kinds table gains a "checked by" column (section 5); the route becomes the guide's "Adding a document" section |
| `subjects/README.md` (256) | a subject author | every manifest field, scenarios, plants, queries, vendoring | why one would write a subject (the task and its keys) in plain English | nothing moves; the guide links it as the reference |
| `demo/GLOSSARY.md` (148) | the page's sentence generator and its test | approved terms, forbidden synonyms, shared register terms | nothing for its purpose | the guide adopts it: same words, same 20-word rule |

The gap is not accuracy but order and audience: an adopter must read 1,400 lines across four files to learn that the gate judges knowledge and not form, that the walk follows approved links only, and that a deterministic run wipes the projection.

## 3. Proposed outline of `docs/guide.md`

Adopter register throughout; every concept named before use; each command followed by "In plain English". Target under 600 lines; detail stays in the four files, linked.

1. **What knowgov is for.** The problem (section 1 above, rewritten for an adopter), what the gate decides, what it cannot see (consistently wrong knowledge), what stays the adopter's (approval, review).
2. **The words.** Register, node, link, subject, document, kind, assertion, key, gate, verdict, store, projection; pointer to `demo/GLOSSARY.md`.
3. **Try it on public content.** The quick start (link), Replay S2 and S6, the example instance.
4. **Your instance.** Layout, `check_instance.py`, the instance compose file; one register per organisation.
5. **Adding a document.** The kinds table with its linter; the pull-request route; what the load refuses; what `unmapped` means. Marks the pre-load gate PROPOSED until built.
6. **Capturing what people know.** A paragraph and a pointer to doc-0007 and `instance/README.md`.
7. **Reading the dashboard.** The screens, field by field (the artifact page's content, made a section; screenshots regenerated by a script, not committed by hand, or left out).
8. **Seeing what a change touches, in Neo4j.** The sample below.
9. **The gate in a pipeline.** `gate_cli.py`, exit codes, `--fail-on`, `--baseline record|FILE`, JSON schema; how it differs from the pre-load gate.
10. **Choosing the model, or none.** `models.toml`, the key variable, deviations; off by default.
11. **Keeping it current.** Link to the demo README's section.
12. **Limits.** One scenario in the store at a time; a run wipes the projection; no login; the walk's starting taxonomies; QUALIFIED is not safe (J-F D3, D5).

## 4. Sample section, fully drafted: Seeing what a change touches, in Neo4j

*(Adopter register. Values are the public register at v0.2.3 and CargoQuote S6; every query below was run on Neo4j 5.26 community.)*

### Two kinds of impact

A change can travel two ways, and knowgov answers each with a different part of the store.

- **A change to the architecture.** You plan to retire, replace or rework one building block of your register: a capability, a journey, a process, an application or one of its modules, or an information entity. You want to know which other building blocks rest on it. The *register* answers this: its *nodes* are the building blocks and its *links* are typed, approved relationships between them.
- **A change to a document.** Someone edits a document the store has read: a decision table, a requirement. You want to know which statements no longer hold and which generated code was built on them. The *knowledge store* answers this: it holds every *assertion* (one statement each), the fragment of the document it came from, its verifications, and the code that used it.

Both live in one Neo4j database once you *project* the register into it, so one query can cross from one to the other.

### Before you start

1. Start the stack and open the page (`demo/README.md`, quick start).
2. On a scenario card, press **Deterministic** for the scenario you want in the store. For the document example below, that is **S6**.
3. In the **store** card, press **Project the register**.

In plain English: the store holds one scenario at a time, and every run first empties it. So load the scenario first and project the register second. If you do it the other way round, the register is wiped and every query below returns no rows, with a warning that the `RegNode` label is not in the database. That warning means "project again", not "something is broken".

4. Open **Open Neo4j Browser** from the store card and log in as `neo4j` with your password.

### The walk: what retiring a node touches

The page's **Register** entry has an **Impact** box. Type a node id and press **walk**.

In plain English: the walk starts at your node and follows links outwards. From an application or module it follows `supports` to processes. From a process it follows `delivers` to products, `realizes` to capabilities, and `is_supported_by` backwards to the journey steps the process supports. From a journey it follows `concerns` to products. It follows **approved** links only (the register's decision 0007). A link that is not approved, or whose far node is deprecated or retired, is listed as *withdrawn* and not followed. The walk does not climb to a node's parent.

Example: the QuoteAPI module, `APP-0002`.

| from | relationship | to | name | followed |
|---|---|---|---|---|
| APP-0002 | supports | PROC-0002 | Validate the request | yes |
| APP-0002 | supports | PROC-0001 | Quote process | yes |
| PROC-0002 | is_supported_by (inverse) | JRN-0002 | Submit a quote request | yes |
| PROC-0002 | realizes | CAP-0004 | Validate a quote request | yes |
| PROC-0001 | delivers | PRD-0002 | CargoQuote instant quote | yes |

Five edges, none withdrawn: retiring QuoteAPI touches two processes, one capability, one journey step and the product. The same walk runs from the command line with the register's own tool:

```bash
python demo/register/tools/impact.py --from APP-0002
```

In plain English: this prints one line per edge with its state, owner and evidence, then a summary: "5 edges walked, 0 withdrawn; products reached ['PRD-0002']; journey elements reached ['JRN-0002']". It reads the register's files directly and needs no database.

A process: `PROC-0004` Price the quote reaches JRN-0003 (Receive the quote, hold or refusal) and CAP-0002 (Price a shipment), two edges. A journey: `JRN-0001` Get a freight quote reaches PRD-0002, one edge. A process with withdrawn links: `PROC-0006` Daily chain (J-F) meets six edges, two withdrawn (REL-05002 to the Seam frame product and REL-03006 to the deprecated step JRN-0008), and reaches PRD-0005 and three journey steps.

### Seeing the walk as a graph

Under the walk's table the panel shows **The walk in Cypher**, in two forms: *rows*, one row per edge, and *paths*, which the Browser draws as a graph. Beside each is **copy** and **open in the Browser**.

In plain English: **open in the Browser** opens Neo4j Browser on a small guide page. Click the grey query block once: the query moves into the editor. Nothing runs until you press the play button. For APP-0002 the graph shows 6 nodes and 8 relationships. Two of them, a `REG_PARENT` and a `REG_REQUIRES` edge, are drawn because the Browser draws every relationship between the nodes it shows; the walk did not follow them. The table on the page is the walk; the graph is a picture of its neighbourhood.

The same query, with the default start, is in the store card's **Saved Cypher** as *The impact walk from APP-0002*.

### Starting from a capability or an information entity

The walk does not start from a capability, an information entity or a product: from `CAP-0002` or `ENT-0003` it meets no edge, and the panel says "No link starts at this node in a direction the walk follows". That is the walk's design: it answers "what would retiring this application or process touch", going upwards. To ask "what rests on this capability" or "what touches this entity", go the other way. These queries are not on the page yet; paste them into the Browser.

**A capability.** What realises or requires it, then one step on from each process that realises it over an approved link:

```cypher
MATCH (c:RegNode {reg_id:'CAP-0002'})
CALL (c) {
  MATCH (x:RegNode)-[r:REG_REALIZES|REG_REQUIRES]->(c) RETURN x, r, null AS via
  UNION
  MATCH (p:RegNode)-[r0:REG_REALIZES {state:'approved'}]->(c), (x:RegNode)-[r:REG_SUPPORTS|REG_IS_SUPPORTED_BY]->(p) RETURN x, r, p.reg_id AS via
  UNION
  MATCH (p:RegNode)-[r0:REG_REALIZES {state:'approved'}]->(c), (p)-[r:REG_DELIVERS]->(x:RegNode) RETURN x, r, p.reg_id AS via
}
RETURN x.reg_id AS node, x.name AS name, toLower(replace(type(r), 'REG_', '')) AS relationship, via,
       r.state AS `link state`,
       CASE WHEN r.state = 'approved' AND NOT x.state IN ['deprecated', 'retired'] THEN 'yes' ELSE 'no, withdrawn' END AS followed
ORDER BY via, node
```

In plain English: the first branch finds what points at the capability: the process that realises it and the product that requires it. The other two branches step from each such process, over approved links only, to the applications that support it, the journey steps it supports and the products it delivers. For CAP-0002 Price a shipment: PROC-0004 Price the quote (realizes), PRD-0002 CargoQuote instant quote (requires), and through PROC-0004 the TariffEngine module APP-0003 and the journey step JRN-0003.

**An information entity (the EDM).** The register's information taxonomy holds the business entities of your data model under `ENT-` ids. What creates, reads, updates or deletes the entity, what application manages it, then one step on:

```cypher
MATCH (e:RegNode {reg_id:'ENT-0003'})
CALL (e) {
  MATCH (x:RegNode)-[r:REG_CRUD|REG_MANAGES]->(e) RETURN x, r, null AS via
  UNION
  MATCH (p:RegNode)-[r0:REG_CRUD {state:'approved'}]->(e), (x:RegNode)-[r:REG_SUPPORTS|REG_IS_SUPPORTED_BY]->(p) RETURN x, r, p.reg_id AS via
  UNION
  MATCH (p:RegNode)-[r0:REG_CRUD {state:'approved'}]->(e), (p)-[r:REG_REALIZES|REG_DELIVERS]->(x:RegNode) RETURN x, r, p.reg_id AS via
}
RETURN x.reg_id AS node, x.name AS name, toLower(replace(type(r), 'REG_', '')) AS relationship, via,
       r.state AS `link state`,
       CASE WHEN r.state = 'approved' AND NOT x.state IN ['deprecated', 'retired'] THEN 'yes' ELSE 'no, withdrawn' END AS followed
ORDER BY via, node
```

In plain English: for ENT-0003 Quote, the process PROC-0004 Price the quote works on it and the QuoteAPI module APP-0002 manages it; from PROC-0004 the query reaches TariffEngine (APP-0003), the capability CAP-0002 and the journey step JRN-0003. For the J-F entity ENT-0010 Seam frame, the link from the Daily chain (REL-07008) is deprecated and shows as withdrawn; the approved one from PROC-0010 Seam frame export leads on to the product PRD-0004. For ENT-0005 Screening result the only link is a draft, so nothing is followed: a draft link is not yet knowledge you can act on.

### From a module to the documents and the code

A module in your register, such as QuoteAPI (APP-0002), is a node; the code that implements it is not. The store reaches from one to the other only through the documents the register's links cite:

```cypher
MATCH (n:RegNode {reg_id:'APP-0002'})<-[:REG_LINK_OF]-(l:RegLink {state:'approved'})-[c:REG_CITES]->(d:RegDocument)
MATCH (a:Artefact {id:d.path})-[:CURRENT]->(:Version)-[:HAS_FRAGMENT]->(:Fragment)<-[:SUPPORTED_BY]-(x:Assertion)
OPTIONAL MATCH (dv:Derived)-[:USED_ASSERTION]->(x)
RETURN l.reg_id AS link, d.path AS document, count(DISTINCT x) AS statements,
       collect(DISTINCT x.status) AS statuses, collect(DISTINCT dv.id) AS derived
ORDER BY link
```

In plain English: start at the module, take each approved link it is part of, follow the link to the documents it cites as evidence, then to every statement the current version of each document supports, and to any generated code that used them. With S6 loaded: REL-06001 and REL-06004 cite `kit/links.toml` (15 statements each); REL-08001 cites `contract/openapi.yaml` (10 statements, used by `derived:S1:G:run1`); REL-08002 cites `kit/requirements.md` (8). This works at the grain of a whole document: a link that cites one requirement still reaches every statement of the file. It needs the register projected and a scenario loaded.

What a module change cannot reach today: a change to the *code* itself. The store records code only as a *derived output* that used certain statements; it does not read code, so editing `reference_impl.py` invalidates nothing. The direction is always document → statement → code.

### When a document changes: statements invalidated, code marked suspect

Load **S6** deterministically. In S6 the decision table changes: the P2 surcharge goes from 316.00 to 341.00 and the file is read in again as version 2.

In plain English: the store compares the new version's fragments with the old ones by their digests. Two fragments are new, 16 are reused. Every statement supported by a fragment that changed is *invalidated*, its verifications end, and any code built on it is marked *suspect*. The gate blocks until the replacement statements are verified again.

The saved query *The invalidation traversal (S6)* lists it:

| changed fragment | invalidated | old value | verification ended | code | successor |
|---|---|---|---|---|---|
| DT-P/row/P2 | A:dt:P2\|surcharge@v1 | 316.00 | price_exact_heavy, valid_until v2 | derived:S1:G:run1 suspect | 341.00, approved |
| DT-P/row/P2 | A:dt:P2\|threshold@v1 | 1244 | price_exact_heavy, valid_until v2 | derived:S1:G:run1 suspect | 1244, approved |
| DT-P/para/worked-example | A:dt:worked_example\|price@v1 | 8652.49 | none | none | 8682.24, proposed |
| DT-P/para/worked-example | A:dt:P3\|order@v1 | after P2 | price_exact_both, valid_until v2 | derived:S1:G:run1 suspect | after P2, approved |

Read it row by row: this fragment changed; this statement no longer holds; this check no longer counts; this code must be looked at again; this is the statement that replaces it, and its status. The worked example's new price is only *proposed*: no one has verified it yet, so the gate would treat it as an assumption if a task needed it. On the page, S6's second strip shows the same: re-ingest, R-STALE, gate BLOCKED, re-verification, gate PROCEED.

### What this section does not do

- The walk and these queries read the register as approved. A proposed or draft link is listed but never followed.
- Nothing here writes to the register or the store. Projecting is a copy; a run deletes it.
- The capability, entity and module queries are proposals in this brief, not yet saved queries on the page.

## 5. The pre-load gate (PROPOSED)

### Kinds and the tool Legible names

From the site's table "Artefact by artefact: tools, practices, gaps" (read 2026-11-02) against `instance/kinds.toml`. "Gate-capable" means the tool meets the contract's exit-code property today.

| `artefacts/` folder | Site state | Tool the site names | Gate-capable | knowgov mapper | Note |
|---|---|---|---|---|---|
| plantuml-models | covered | pumllint | yes (score, ratchet) | sequence, containers, plantuml_realises | the reference row; also C4-in-PlantUML |
| aris-epc | covered | aris2puml, then pumllint | via pumllint | none | converted output goes under plantuml-models; the EPC itself is not linted |
| textual-requirements | planned | StrictDoc, Doorstop, Sphinx-Needs, OpenFastTrace | pass/fail, no threshold | requirements, requirements_json | J-F's `requirements.json` has no named linter; a JSON Schema check (sourcemeta jsonschema) covers form only |
| user-stories | open | none maintained | no | none | |
| specification-prose | covered | Vale, markdownlint | yes | spec, contracts_markdown | prose linters miss vague guards (R-VAGUE does) |
| acceptance-scenarios | covered | gplint | partial | gherkin, gherkin_tagged | |
| bpmn-process-models | planned | bpmnlint | errors vs warnings | bpmn | |
| decision-tables | covered | dmnlint (small rule set) | no threshold | decision_table, dmn, dmn_decisions | dmnlint reads `.dmn` only; CargoQuote's `decision_table.md` is Markdown: markdownlint for form, nothing for content |
| cross-artefact-links | planned | pumllint `trace` | yes | links | |
| architecture-decisions | open | adr-guard, adrpy-ai (pre-1.0) | yes, immature | none | |
| c4-models | covered | Structurizr CLI | yes | none | a Structurizr DSL file has a linter and no mapper |
| archimate-models | open | Archi's validator | no | none | |
| sysml-capella-models | open | Capella rules (commercial gate only) | partial | none | |
| api-contracts | covered | Spectral, vacuum, Redocly | yes (vacuum score) | openapi | |
| schemas | covered | buf, graphql-eslint, sourcemeta jsonschema | yes (buf breaking) | none | |
| data-models | covered | SQLFluff, dbt-checkpoint, dbt_project_evaluator | yes | none | conceptual and logical models have nothing; the register's ENT taxonomy is the only record of them here |
| threat-models | open | pytm, Threagile | script your own | none | |
| event-logs | planned | PM4Py conformance | script your own | none | |
| glossary | open | none | no | none | |
| property-invariants | covered by a practice | the test runner | yes | none | |

Read across the twenty kinds: 5 have a covered tool and a mapper (PlantUML, specification prose, Gherkin, DMN, API contracts), where the pre-load gate is worth most; 3 have a mapper and only a planned tool (textual requirements, BPMN, cross-artefact links); 5 have a covered tool and no mapper (ARIS EPC through aris2puml, C4 in Structurizr, schemas, data models, property invariants): checked, not read; 7 have no gate-capable tool (user stories, ADRs, ArchiMate, SysML and Capella, threat models, event logs, glossary).

### The route

1. A contributor opens a pull request into the instance repository adding or changing a file under `artefacts/<kind>/`.
2. The instance's CI runs, per changed file, the linter its kind names (a new `lint` field per row of `kinds.toml`, empty where the site names none), then `tools/check_instance.py`.
3. Branch protection requires the job green and a reviewer who is not the author. An empty `lint` field passes with a finding at `info` saying the form is unchecked, so the gap stays visible.
4. The load reads only the merged tree (the read-only mount of the default branch). Nothing loads from a branch.

### Exit codes, per the contract

- 0: every changed file passed its kind's linter at the configured threshold, and the layout holds.
- 1: a finding at or above `--fail-on` in any file, or `check_instance.py` reported the layout broken.
- 2: could not run: a linter missing, a kind unknown, a file unreadable.

A baseline per kind (`--baseline FILE`, the linter's own where it has one: pumllint's ratchet, vacuum's score, buf breaking) fails only on regression, so an organisation can adopt the gate over an existing corpus. JSON report under a schema beside `gate-report.schema.json`.

### What the load refuses

Today the load refuses nothing for its form: a file no mapper reads is reported `unmapped` and loaded as a document with no statement; a file a mapper cannot parse fails the run. Proposed: the load refuses a document whose path is outside `artefacts/<kind>/` for a known kind, and records each document's linter verdict (tool, version, digest of the file it judged) on its `Version` node, so a document loaded without a passing check is visible in the store and in the gate's bundle. The load does not re-run linters; the merge is the check.

### Why neither gate replaces the other

| | Pre-load gate (PROPOSED) | knowgov gate (`gate_cli.py`, task-0007) |
|---|---|---|
| Question | Is this document well-formed for its kind? | Is the knowledge this task needs good enough to build on? |
| Unit | one file | one task's keys, across all documents |
| When | on the pull request, before merge | after the load, before a build |
| Sees | syntax, rule violations, a score | absence, declared gaps, contradictions, unverified, invalidated knowledge |
| Cannot see | that two well-formed documents disagree, or that a required fact is missing | a malformed file the mapper still parsed; anything no mapper reads |

A lint-clean set can still block (S2: every file well-formed, the rule declared open). A lint-dirty file can still yield verified statements. And both pass a set that is consistently wrong (J-F D3: the pristine oracle fails 17 scenarios; J-F #309: 100/100 and 25 contradicted claims). The guide must say the third point plainly.

## 6. The dashboard

Field by field on the [artifact page](https://claude.ai/artifact/RNpHTUDJW93AXoWCDYTvtj). Observations an adopter guide must carry, from running it:

- On the in-memory store the store card shows only the census: no Browser link, no saved Cypher, no Project button. An adopter trying impact without Neo4j has the panel and `impact.py`, nothing more.
- A deterministic run of S2 took 3 s on rdflib; S6 took 25 s on Neo4j (the second stage).
- The plain-English block's last sentence carries the comparator's result ("identical on all 108 fields compared with results/S2"), which is the adopter's proof the platform behaves.
- The saved walk's `CALL { WITH a … }` form draws a deprecation notice in Neo4j 5.26 ("CALL subquery without a variable scope clause is deprecated"); it runs. The scoped form `CALL (a) { … }` is available in 5.26.

## 7. Opportunity canvas

| Box | Content |
|---|---|
| What hurts today | An adopter reads four files written for other readers to learn the order of work; impact stops at three taxonomies; nothing checks a document's form before it reaches the graph. |
| What the guide adds | One page in the adopter register: the problem, the route for a document, the screens, the two kinds of impact with the queries that answer them, the limits. |
| Who reads it | An architect or process owner in a client organisation; the operator of an instance; a reviewer replaying the record. |
| How it is done now | `demo/README.md` doubles as the guide; impact means the default start or `impact.py`. |
| What a reader gets | A start-to-finish path on public content, then on their own instance; an honest list of what the graph answers and what it does not. |
| What to watch | Questions an adopter asks that the guide does not answer (count, from the first pilot); queries pasted from the guide that return no rows because of store state. |
| How it starts | 1. `docs/guide.md` from the outline, the sample section first. 2. The three proposed queries as saved queries. 3. The `lint` column in `kinds.toml`. 4. The pre-load CI job in `tools/example_instance.py`'s output. |
| What the business risks | A guide that promises more than the platform does; a fifth file to keep current. |
| What it gains | A first pilot that needs no session with the maintainer; Legible's gate contract shown at the document level. |
| What it costs | A few days for the guide; an hour per saved query with its stack-job check; the pre-load job a task of its own. |

## 8. Sense and nonsense

**Sense**
- One guide, linking the four files as references: the content exists; the order does not.
- The second kind of impact (S6) is the stronger selling point: it is the one a document search cannot give, and it is measured.
- The capability and entity queries: read-only, approved links only, the same withdrawn rule as the walk; they answer the IEAM's question from the side an architect usually starts.
- A pre-load gate as a pull request: the instance is a git repository already; review and CI are the natural check; the load reads only what merged.

**Nonsense or weak**
- Promising "impact of a module change" end to end: code is not read; a module reaches documents at file grain. Say what it reaches.
- Treating a lint-clean instance as governed: form is not knowledge (section 5's table).
- Re-running linters inside the load: a second gate with no review behind it; the merge is the check.
- Extending `tools/impact.py` from this backlog: the walk is the register's, under its decision 0007; knowgov may propose, the register decides.
- Committing screenshots: they rot with every page change and bloat the repository; the artifact page or a script that regenerates them.

## 9. Fit/gap, the ask against the platform

| Asked | Today | Gap |
|---|---|---|
| The problem, from the record | decision-0001, doc-0001, the record's numbers, J-F's degradation arms | none; scattered |
| Documents checked by their tool before the load | `check_instance.py` (layout), `unmapped` report | no linter step anywhere; no `lint` field per kind |
| Exit codes per the contract | `gate_cli.py` and `check_instance.py` both 0/1/2 | the pre-load job does not exist |
| Every dashboard screen | the page, `demo/README.md`'s "What you see" | no field-by-field reference in the repository |
| Impact from a capability | none: 0 edges | the CAP query (proposed) |
| Impact from a journey | journey kind: `concerns` only; a step reaches nothing | steps and touchpoints never start a walk |
| Impact from a process, an application | the walk, the panel, the saved Cypher, the Browser guide | none |
| Impact from an information entity (EDM) | none: 0 edges | the ENT query (proposed) |
| Impact from a module | APP-0002 is a register node: walk works | code not linked; module → documents at file grain (proposed query); a code change reaches nothing |
| Document change → statements → code | S6, the invalidation saved query | none for the demo; for an instance, needs a derived output registered by the build |

## 10. SWOT

**Strengths**
- Every claim in the guide can be run on public content and checked against the record → the guide quotes numbers, not adjectives.
- The page's wording rules already hold the page to plain English → the guide adopts them, no new style.
- One store holds both namespaces → module → document → code is one query.

**Weaknesses → response**
- The walk starts from three taxonomies → the two queries now; a register proposal for `crud`, `manages`, `requires` inverses later.
- Document-grain citing → the anchor is already on `REG_CITES`; an anchor-to-fragment match is the next step.
- One scenario in the store, a run wipes the projection → the guide's "Before you start" says so first.
- No pre-load check → the PROPOSED gate.

**Opportunities → how realised**
- The site's table becomes executable per instance → the `lint` column and the CI job.
- An adopter pilot without the maintainer in the room → the guide plus the example instance.
- The saved-query list as the guide's index → each query a section, each section a query.

**Threats → mitigation**
- The guide drifts from the page → the screens section generated from the page's own endpoints or kept as an artifact view; a test that every query in the guide is a saved query.
- A pre-load gate read as governance → section 5's comparison in the guide's first page.
- Private content reaching a public linter service → every named linter runs locally; the CI is the instance's own.

## 11. Follow-ups proposed (not created as tasks)

1. `docs/guide.md` from section 3, with section 4 as its first written section; `demo/README.md` links to it.
2. The capability, information-entity and module-to-store queries as saved queries in the store adapter, checked by the stack job as `check_saved_queries.py` checks the others.
3. Move the saved walk to the scoped `CALL (a) { … }` form; one line, removes the 5.26 deprecation notice.
4. A `lint` field per row of `instance/kinds.toml`, filled from section 5's table, held by `tests/test_instance.py`.
5. The pre-load CI job as a workflow template an instance copies, exit codes per the contract, proven on the example instance in `harness.yml`.
6. Record each document's linter verdict on its `Version` node and in the gate's bundle.
7. Propose to ieam-register: walk starts from capabilities and information entities (inverse `realizes`, `requires`, `crud`, `manages`), under its decision 0007's approved-only rule.
8. Anchor-grain citing: match a `REG_CITES` anchor to the fragments it names, so a link citing REQ-06 reaches REQ-06's statements only.
