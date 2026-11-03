---
id: doc-0013
title: >-
  Palantir Ontology read against knowgov: the assessment verified, fit/gap, the
  epistemic model, candidates
type: specification
created_date: '2026-11-03T23:44:00Z'
updated_date: '2026-11-03T23:44:00Z'
tags:
  - brief
  - palantir
  - fit-gap
  - lighthouse
  - epistemic
---
*2026-11-03. Maintainer register. A study: nothing built, no task opened here (the coordinating session mints the ids). Trigger: the maintainer's assessment "Palantir Ontology — Architectural and Technical Assessment" (dated 4 November 2026, uploaded 2026-11-03), read against knowgov. Read on `main` at `1579d57`, register v0.2.6; decision-0004 as proposed in PR #100; the MCP server as in PR #94. Product claims carry the URL of Palantir's public documentation they were checked against. The assessment's mortgage and banking examples are restated here in neutral terms or on the public subjects (CargoQuote, the J-F data load); nothing banking-related enters this repository. One record per thing: the twin wording stays doc-0010's, the walk and code traceability doc-0011's, the market and scores doc-0012's; this doc adds the reading of an operational ontology against them.*

## Verdict

**The assessment is sound on architecture and mostly right on the product; its sharpest point is knowgov's thesis in other words.** "Being present in an Ontology does not automatically make information correct, complete, current, or verified" is doc-0010 §3 and doc-0012's positioning line. knowgov sits in the assessment's **first concern (authoritative knowledge) and third (AI consumption)**, on the reading side only: it holds the epistemic state of what the organisation declared and tells an agent or a pipeline whether it may build on it. It does not sit in the second concern (an operational model with functions and actions) and should not: it never executes a business action (§5, candidate 9).

**Palantir is a consumer, not a competitor, on the narrow category** (doc-0012 §1: declared architecture upstream of delivery). Its documentation shows strong governance of *the model* (branches, proposals, reviews, ontology roles, action logs, submission criteria) and of *access*, and nothing native for the *epistemic state of a fact*: no per-property provenance-of-claim, verification status, confidence, or declared absence (§1, A12). That is exactly the assessment's §7 proposal, and knowgov already has most of it (§3).

**Of nine candidates: build three (round-trip proof, the POC criteria as the lighthouse's evaluation protocol, superseded shown in the answer), one more after a maintainer decision (date lapse of review verifications); document two (a basis crosswalk, a permission matrix); park two (an operational projection, business validity dates); reject two (a confidence number, executing actions)** (§5). None displaces m-8's lighthouse: an export to an operational ontology is a *second connector in the other direction*, and both reviewers of doc-0012 put one lighthouse ahead of four connectors. One proposal goes to ieam-register (a decision-model taxonomy), never built here.

## 1. The assessment verified

Verdict per claim: **holds**, **partly**, **wrong**, **not found**. Quotes are verbatim from the URL beside them.

Checked 2026-11-03 against palantir.com/docs. Quotes marked † come from a search snippet, not a fetched page; the rest were fetched, the ones the doc leans on (export, Ontology MCP, consistency) twice.

| # | The assessment's claim (§) | Verdict | Palantir's documentation |
|---|---|---|---|
| A1 | The Ontology combines data, logic, actions and security; an operational model, not merely a knowledge graph (§1) | **holds** | "The Ontology models decisions through the four-fold integration of data, logic, action, and security." https://www.palantir.com/docs/foundry/architecture-center/ontology-system ; "The Palantir Ontology is an operational layer for the organization." https://www.palantir.com/docs/foundry/ontology/overview |
| A2 | Primitives: object type, object, property, link type, interface, function, action type (§2) | **holds** | "An object type is the schema definition of a real-world entity or event."; "A function is a piece of code-based logic that takes in input parameters and returns an output."; "An action type is the schema definition of a set of changes or edits to objects, property values, and links" https://www.palantir.com/docs/foundry/ontology/core-concepts |
| A3 | An interface defines shared properties or behaviour across object types (§2) | **holds** | "An interface is an Ontology type that describes the shape of an object type and its capabilities." https://www.palantir.com/docs/foundry/interfaces/interface-overview |
| A4 | "Kinetic" names functions and actions (§2) | **holds** | "semantic elements (objects, properties, links)" and "kinetic elements (actions, functions, dynamic security)" https://www.palantir.com/docs/foundry/ontology/overview |
| A5 | OSDK: typed programmatic access to objects, queries, functions and actions (§4) | **holds** | "Types and functions are generated from your Ontology"; "The OSDK supports npm for TypeScript, pip or Conda for Python, Maven for Java, and OpenAPI spec for any other language." https://www.palantir.com/docs/foundry/ontology-sdk/overview |
| A6 | Ontology MCP makes *selected* capabilities available as tools to agents (§4) | **partly** | Holds on exposure: "exposes your application's ontology resources as Model Context Protocol (MCP) tools", "such as object types, action types, and query functions". Omits that it writes: "Ontology MCP enables controlled writes to ontology data"; selection is by "application restrictions" and OAuth scopes. https://www.palantir.com/docs/foundry/ontology-mcp/overview ; https://www.palantir.com/docs/foundry/ontology-mcp/authentication-and-authorization |
| A7 | Authoring interfaces are separate; model-edit permissions differ from operational ones (§4, §6) | **holds** | Legacy roles: an Editor role "does not grant any permission on the data or datasource itself" https://www.palantir.com/docs/foundry/object-permissioning/ontology-permissions-legacy ; current, project-based: "To see objects, you must hold View permissions on the object type and access to the data." https://www.palantir.com/docs/foundry/object-permissioning/ontology-permissions ; actions: "Submission criteria … determine whether an action can be submitted." https://www.palantir.com/docs/foundry/action-types/submission-criteria |
| A8 | Ontology changes go through development and review mechanisms (§6) | **holds** | "An ontology proposal is analogous to a Pull Request in a version control system."; "Ontology proposals are merged through merging a Global Branching proposal." https://www.palantir.com/docs/foundry/ontologies/review-ontology-proposals |
| A9 | An action is transactional within the Ontology; external calls can fail independently (§6) | **holds** | "Actions behave as database transactions and provide the standard ACID properties"; atomicity "does not extend to other side effects of the action, such as notifications or webhooks" https://www.palantir.com/docs/foundry/action-types/consistency-guarantees ; a writeback webhook runs first, yet "it is still possible that the external request may succeed but Ontology changes could fail." https://www.palantir.com/docs/foundry/action-types/webhooks |
| A10 | The documentation discusses exporting model information; export does not prove portability (§6) | **holds, and understated** | "Ontology schema definitions are stored in a JSON file."; "You should not depend on the exported JSON schema as it may change over time."; some working states "cannot be imported to an Ontology other than the one it was exported from." https://www.palantir.com/docs/foundry/ontology-manager/export-import . No OWL, RDF or JSON Schema export in the current documentation; a 2019 white paper claims RDF/OWL import and export† (https://www.palantir.com/assets/xrfr7uokpv1b/7BxLPkTqJU9QhLTQCjJMo6/eed1457949dc2d1cd6b6e71936c0aa9c/Enabling_Interoperability_and_Embracing_Openness_with_Foundry.pdf), unconfirmed on any current page |
| A11 | AI integration through AIP, the SDK and agent-facing interfaces (§5) | **holds** | Agent tool types "Action", "Object query", "Function", …, "Request clarification"; action tools run "automatically or … after confirmation from the user." https://www.palantir.com/docs/foundry/agent-studio/tools |
| A12 | Presence in the Ontology does not make information correct, current or verified (§4) | **holds, by absence** | Status exists per *type* only: Experimental, Active, Deprecated (also Promoted, Example) https://www.palantir.com/docs/foundry/object-link-types/metadata-statuses . Provenance exists for *data* and *edits*: lineage of backing datasets https://www.palantir.com/docs/foundry/data-lineage/faq ; "Submitting an action generates a single new object of the corresponding action log object type." https://www.palantir.com/docs/foundry/action-types/action-log . No per-object or per-property verification status, confidence or declared absence was found |
| A13 | The four references (§ References) | **partly** | 1, 2 and 4 resolve as cited; 3 is served at https://www.palantir.com/docs/foundry/ontology-mcp/overview |
| A14 | Neo4j: graph retrieval and agent integrations; ARIS: depends on deployed capabilities (§5) | **holds for Neo4j, not checked for ARIS** | Neo4j's official MCP server, accepted in doc-0012 §3; ARIS left unchecked here, no knowgov position rests on it |

### What the assessment omits that matters for knowgov's position

1. **Ontology MCP writes; Palantir MCP edits the model.** OMCP "allows LLM agents to read objects, execute predefined actions, and query data" (https://www.palantir.com/docs/foundry/ontology-mcp/overview). A second server, Palantir MCP, is for builders: it "can modify ontology types, but cannot write ontology data" (https://www.palantir.com/docs/foundry/palantir-mcp/overview). The assessment's read / model-edit / execute split is real in Palantir as two servers and two scopes; knowgov's MCP server (PR #94) offers the read alone, by design.
2. **Versioning and branching of the model.** Proposals on Global Branching, reviewed per change (A8); breaking changes need a migration: "Ontology Manager will block the user from saving changes until they define a migration for the breaking change." (https://www.palantir.com/docs/foundry/object-edits/schema-migrations); history with restore: "any changes that were made after the entry you selected will be undone" (https://www.palantir.com/docs/foundry/ontology-manager/restore-changes). Governance of *the model* is strong; it is the register's counterpart (four eyes, decision records), not knowgov's.
3. **Validation is of form, not of truth.** "Value types encapsulate domain-specific data types and enforce data validation in a manner reusable across the platform." (https://www.palantir.com/docs/foundry/object-link-types/value-types-overview); submission criteria (formerly "validations") check an action's inputs (A7). Both are knowgov's pre-load check in kind (task-0045: "form, not knowledge"), not its gate.
4. **Provenance of edits, not of claims.** Edit history "records every edit to an object, regardless of how the edit was made" (https://www.palantir.com/docs/foundry/object-edits/user-edit-history); the action log records "successful action submissions only" (https://www.palantir.com/docs/foundry/action-types/action-log). Who changed a value is recorded; on what evidence a value is true, and how well it is known, is not.
5. **Status is type-level and cascades.** "an experimental object type cannot have an active link type"† (https://www.palantir.com/docs/foundry/object-link-types/metadata-statuses). A lifecycle of the schema, like the register's node states, not an epistemic state of a fact.
6. **Agent tooling has human confirmation, not evidence checks.** Action tools may require the user's confirmation (A11); AIP Logic can stage consequential actions for review† (https://www.palantir.com/docs/foundry/logic/aip-logic-integration-automate). Nothing withholds a tool because the objects it reads are unverified: the place knowgov's gate would sit. The studio is being renamed AIP Chatbot Studio† (https://www.palantir.com/docs/foundry/aip/aip-features).
7. **Reverts stop at the Ontology.** "An action revert only reverts the edits to the object instance, but it will not revert side effects."† (https://www.palantir.com/docs/foundry/action-types/action-reverts); proposals "cannot be reverted automatically"† (https://www.palantir.com/docs/foundry/ontologies/ontologies-proposals). Strengthens the assessment's consistency qualification.
8. **Open standards in concept only.** Data types are "inspired by similar concepts in RDF, OWL and XSD"† (https://www.palantir.com/docs/foundry/object-link-types/type-reference); users report writing their own JSON-to-OWL converter (community thread, not Palantir: https://community.palantir.com/t/is-there-a-native-rdf-or-owl-export-for-the-ontology/7187). A one-way projection *into* Palantir is the realistic direction; a round trip out of it is the evaluator's to prove, as the assessment says.

### Smaller corrections to the assessment

- §4's "selected Ontology capabilities" reads as reading; OMCP also executes actions and writes (omission 1). The security boundary the assessment draws (consume vs change the model) exists, but execution sits on the *consuming* side.
- §6's permission risk cites "read, model-edit, and execute"; the role model it implies is now legacy, replaced by project-based permissions (A7).
- §6's portability qualification is right and understated: the export is the working state of one ontology, its schema unstable by Palantir's own words (A10).
- §3's six taxonomies include decision models; ieam-register has seven taxonomies and decision models is not one of them (§5, R1). Information and organisation, which the register has, are missing from the assessment's six.
- §7 asks agents to "surface gaps rather than silently filling them" but gives a gap no shape; knowgov's gaps are typed nodes (§3).

## 2. Where knowgov sits: fit/gap against the assessment's frame

### The three concerns (assessment §9)

| Concern | What it needs | knowgov | ieam-register | Fit |
|---|---|---|---|---|
| 1. Authoritative enterprise knowledge | governed taxonomies, definitions, evidence, ownership, versions, verified relationships | statements with basis, status, verifications, approvals, gaps; invalidation on source change; the gate | seven taxonomies, ten typed relationship types, lifecycle and four-eyes approval, owners, dated exports, review cadence | **Fit.** Split by design: the register holds identity and links, knowgov the epistemic state of what documents and people say about them |
| 2. Operational enterprise model | business objects (instances), links, functions, decision logic, controlled actions | none: no instance data, no functions, no actions; decision logic only as *statements read from* decision tables | none | **Out of scope, by design** (doc-0010 §5: the running twin is out) |
| 3. AI consumption and execution | grounded retrieval, reasoning, impact assessment, authorisation-constrained operations | the bundle, `read_knowledge`, the three-valued answer, the gate's verdict and exit code; read-only MCP (PR #94); the walk (register 0010) | `tools/impact.py` | **Fit on consumption, deliberate gap on execution.** knowgov's only "operation" is a verdict that stops delivery |

### The comparison table (assessment §5), with a knowgov column

| Dimension | Palantir Ontology | knowgov + ieam-register |
|---|---|---|
| Primary role | operational model of the running business | governed knowledge layer of the *declared* design |
| Objects and relationships | object and link types, instances backed by datasets | register nodes and typed links (TOML in git); statements about them in a store |
| Graph exploration | Object Explorer, Vertex, search-around | the walk (seven start kinds since register 0010), saved Cypher, Neo4j Browser |
| Executable business actions | action types, functions, writeback | **none, by decision**; the gate's exit code stops a build |
| AI integration | AIP agent tools, OSDK, Ontology MCP (reads *and* executes actions) | gate and three-valued answer over MCP (PR #94), the governed agentic arm (task-0022) |
| Epistemic state of a fact | not native (A12): lineage of data, an edit log, a status per type; no verification status of a claim | native: basis, status, verifications with scope and validity, approvals, gaps, the three-valued answer |
| Change governance | branches, proposals, reviews, migrations on the model (A8, omission 2) | pull requests, four eyes, decision records; a source change invalidates statements and marks derived code suspect |
| Portability | ontology JSON export, schema unstable, same-ontology import; Marketplace products between Foundry enrolments (A10) | plain files in git (register, instance), Turtle from the rdflib store, the same record on two stores (task-0004) |
| Likely role | operational semantic and execution layer | the check *before* an agent or a pipeline builds on a declared fact, and the source an operational ontology would project from |

### The POC criteria (assessment §8), scored for the stack today

| Criterion | knowgov stack today | Evidence | Gap |
|---|---|---|---|
| Semantic modelling | **met, synthetic**: seven taxonomies, ten relationship types, owners per node and link | `demo/register/metamodel/types.toml` | the assessment's sixth taxonomy, decision models, is no taxonomy here (candidate R1) |
| Traceability | **met on the register; partial to code** | register 0010 walk; S6 invalidation; task-0046 anchor-grain query | code → knowledge needs m-7 (tasks 0050, 0051) |
| Knowledge quality | **met**: unsupported statements are found and gated | the min rule, flags for inferred/assumed/hypothesised, declared gaps, the record's D-measures | currency by date for non-elicited verifications (candidate 3) |
| Agent grounding | **met for the mechanism, unproven for the outcome** | pumllint `docs/neo4j-governed-knowledge-evaluation.md`: governed arm 0 generations under BLOCKED in 20 cells | the outcome study (task-0057) |
| Operational safety | **n/a for actions; met for writes**: the store and register change only through pull requests and recorded rulings | decision-0002; MCP read-only view (PR #94) | a stated permission matrix (candidate 5) |
| Interoperability | **partial**: open files, Turtle, two stores, one record | task-0004 comparator; `KG_RDFLIB_FILE` | 0 of 3 export routes verified (m-8, task-0063); no round-trip test (candidate 7) |
| Performance and cost | **not measured** beyond the record's token counts | task-0027 | lighthouse scale unknown |

### SWOT, the stack against an operational ontology

- **Strengths.** The epistemic state Palantir lacks natively, at statement grain; declared absence as a first-class answer; invalidation that reaches derived code; a gate with an exit contract; open files, no lock-in.
- **Weaknesses.** Execute 3 (doc-0012): no installation met, synthetic content, one maintainer. No instance data and no actions, so to an operational buyer it looks like "only metadata". Decision models are documents, not register nodes.
- **Opportunities.** Palantir's own documentation leaves the gap open (A12); an organisation running Foundry and an EA repository has the assessment's §5 reference architecture and no box for "verified entities, links and provenance": that box is knowgov plus the register. The MCP surface lets an AIP agent consult the gate without any sync, if the operational platform's agents can call an external MCP server (not checked here).
- **Threats.** Palantir adds a verification status or "Proposed/Approved" property pattern to object types and an agent policy reading it (doc-0012 §7: V2 and V3 to 4, into the corner). An operational ontology becomes the de facto register in a client, and the authoring tools and knowgov are routed around (the assessment's "authority and ownership" risk, seen from the other side).

### Opportunity canvas: knowgov as the governed source of an operational projection

| Block | Content |
|---|---|
| Users and customers | an organisation running an operational ontology (Palantir, Fabric IQ, a Neo4j application) beside EA authoring tools; its platform team, its architects, its agent builders |
| Problem | agents and actions in the operational layer rest on objects and links whose truth nobody states; the platform governs access and model edits, not whether a claim is verified, current or contested (assessment §4 "critical limitation", §6 data quality risk) |
| Solution | knowgov stays the source of the epistemic state: a schema-pinned, one-way projection (entities by register id, links, statements with status, provenance, validity and gaps) and the gate over MCP; the operational ontology reads, never writes back |
| Value | the "verified entities, links and provenance" arrow of the assessment's §5 diagram, with a contract and an exit code; the operational side keeps its actions, knowgov its authority |
| Metrics | share of an agent's grounding keys that are verified; actions deferred because their keys are BLOCKED; drift between the projection and the operational copy found by reconciliation |
| Channels | the integrator of the lighthouse; the operational vendor's marketplace much later (doc-0012 S3) |
| Cost | one adapter per consumer, a projection schema, reconciliation; the maintainer's time, which m-8 already spends |
| Risks | a second connector before the first is verified (doc-0012); vendor-specific code under `harness/` (forbidden by task-0002's rule); content leaving a private instance |
| Unfair advantage | statement-grain epistemic state and declared absence, which an operational ontology does not carry natively |

### What an operational-projection consumer needs from knowgov and ieam-register

1. **Stable identity.** Register ids (`CAP-`, `PRD-`, `JRN-`, `PROC-`, `APP-`, `ENT-`, `ORG-`, `REL-`) as primary keys; the external tool ids (`aris_guid`, `archi_id`, `edm_id`, `sources.toml`) beside them; `maps_to` as the join into the consumer (register 0010: "the join into a knowledge store, which is that store's to make").
2. **Links with state.** Only approved links by default (register 0007), withdrawn ones reported; owner and approval `{by, on, record}` on each.
3. **Per statement:** key, value, basis, status, source document and fragment digest, version, verifications (method, scope, at, `valid_until`), approval and its lapse, gaps; per key, the level and the three-valued answer.
4. **Change signals.** Invalidations, suspect derived outputs, stale external ids (a vanished id is a finding, never a deletion), each dated, so the consumer can mark its own objects.
5. **A pinned schema and a version** under decision-0003, so the consumer can pin; an append-only, dated delivery, the way exports arrive.
6. **No write-back.** The consumer reads; a disagreement it finds comes back as a capture (a person's answer) or a pull request, never as an edit.
7. **What it does not get:** content beyond the statements' values (doc-0001 §0: the store holds status, provenance and links), any personal key (register 0009), anything from another organisation.

## 3. The assessment's §7 against knowgov's assertion model

The assessment proposes a `KnowledgeAssertion`/`Evidence` concept. Field by field:

| Assessment field | knowgov today | Has / lacks / differs |
|---|---|---|
| `subject`, `predicate`, `object` | `entity`, `predicate`, `value` (raw and normalised); the key is `entity|predicate` (`harness/extract.py`) | **Has.** Differs: the object is a literal value; links between register nodes are the register's, with their own fields, not statements in the store |
| `source` | artefact, version, fragments with sha256 (`SUPPORTED_BY`); for a person, `record = capture:<id>` | **Has**, at fragment grain, digest-pinned |
| `asserted_by` / `approved_by` | `ATTRIBUTED_TO` an agent (harness, model, person handle, human stand-in); approval `{by, on, record}`; the verifying agent | **Has, stronger:** decision-0002 forbids approving what one's own handle gave; a model never rules |
| `derivation_method` | `basis`: authored, extracted, elicited, inferred, assumed, hypothesised; the activity's kind (extraction, inference, review) | **Partly.** Origin is typed; the logic is not (no deductive/inductive/abductive). `hypothesised` reads as abductive, `inferred` is a model's proposal; candidate 1 |
| `validation_status` | status: proposed, validated, verified, approved, disputed, invalidated; rejected and lapsed (decision-0002); per key, the level adds absent and declared_gap | **Has, richer.** "unverified" is proposed or validated; "superseded" is invalidated with a verified or approved successor (`gate.resolve`); candidate 4 |
| `confidence` | none, by design: ordinal statuses and a three-valued answer | **Lacks, deliberately**; candidate 2 |
| `effective_date` / `expiry_date` | verification `valid_until` (a version tag, set when a source change ends it); approval lapse six months after an elicited capture (register 0008); register `review_due`, exception expiry | **Partly.** Knowledge validity by version and, for people, by date; no date lapse for documents' verifications; no business validity of the fact itself; candidate 3 |
| `version` | artefact Version (tag, sha256), assertion id `@version`, register at a tag, instance commit | **Has** |
| `supporting_evidence` | Verification nodes (method execution or review, scope, `evidence_sha256`, at); corroborating pairs; the register's `evidence` list | **Has** |
| — (not in the assessment) | **gaps as first-class**: declared, ambiguous, conflict, absent artefact, unverified requirement, silent entity; the three-valued answer; invalidation reaching derived code (S6); the gate's verdict and exit; the consulted set | knowgov's difference. The assessment asks agents to "surface gaps rather than silently filling them" but gives a gap no shape |
| tacit knowledge (§7 list) | the capture route: a questionnaire per owner, an `elicited` statement, a review, a six-month lapse | **Has** (task-0009, task-0037) |

Where the two differ in kind: the assessment puts every quality attribute on one assertion. knowgov keeps three levels apart, as decision-0004 also assumes: the **statement** (basis, status), the **key** (level, the min rule, flags, the three-valued answer) and the **task** (verdict over required keys). The last two are what make "may I build on this?" answerable, and they have no counterpart in §7.

## 4. Roadmap items the candidates touch

m-5 capture (decision-0004 / task-0039, tasks 0040–0043, 0054, 0055); m-6 adopter (0047, 0064–0066); m-7 code (0050–0052); m-8 lighthouse (0056 MCP in PR #94, 0057–0063, 0062/0063 naming LeanIX + Signavio, Ardoq or ARIS); m-4 parking (0008, 0053). Register decisions 0001 (structure), 0007 (approved links only), 0008 (elicited, six months), 0009 (handles), 0010 (the walk), 0011 (compliance unit). knowgov decisions 0001 (boundary), 0002 (rulings), 0003 (contracts), 0004 proposed.

## 5. Candidates

Size: S under a day, M a few days, L more. Contract: decision-0003's list (gate exit codes or flags, `harness/schemas/`, instance layout, store port, subject manifest).

### 1. A typed `derivation_method` (deductive, inductive, abductive)

- **In knowgov:** a second field beside `basis` on inferred statements, or a widening of `basis`. M; schema and SHACL shapes change: minor.
- **Reading:** knowgov's statements are almost all *read* (extracted, authored) or *given* (elicited). The only derived ones are a model's proposals (`inferred`, candidate for a gap, never above proposed) and the assumptions an arm declares. The rules do not derive statements; they move status. A logic label on a model's proposal would be the model's claim about its own reasoning, unverifiable.
- **Compatibility:** no conflict.
- **Decision: do not build.** Document the crosswalk (`authored` → authored, `extracted` → imported, `elicited` → tacit captured, `inferred` → model-derived, `hypothesised` → abductive, `assumed` → assumption) in the glossary and the guide. Reopen if a rule or a reasoner ever *creates* statements (for instance an OWL or SHACL-rule entailment), when deductive gets a meaning here.

### 2. `confidence` beside verification

- **In knowgov:** a number on a statement or a verification. M; schemas: minor.
- **Conflict:** the gate's design (ordinal statuses, the min rule, three values) and the record's measure, which rests on discrete levels (pumllint evaluation). A number invites a threshold, and a threshold invites tuning until the gate passes.
- **Decision: reject on statements and keys.** The assessment itself says it is "not a substitute for verification". A number is admitted in one place only: received evidence that carries its own method, as doc-0011 §2 already designs for process mining (fitness with its method, flags a key, never verifies it; task-0053, parked).

### 3. `effective_date` / `expiry_date`: validity in time

Two different things the assessment merges:

- **(a) Currency of the knowledge:** how long a verification holds. knowgov has it by version (a source change ends it) and, for a person's answer, by date (six months). It lacks a date lapse for a document's verification by review: a statement verified by review in 2026 is still verified in 2030 if nobody touches the document. The register already has the cadence (`lifecycle.toml` `[review] default_months = 12`, per kind). **In knowgov:** a review-method verification gets `valid_until` as a date from the owning kind's review months; past it the statement reads `validated` (or `proposed`) and the key falls. M. **Contract:** changes what PROCEED means and adds a value form to `valid_until`: minor; the gate report schema may gain a finding kind. **Needs a maintainer decision first** (it is decision-0004's question in another form: what lowers a key). Compatible with decision-0004 B: a lapse lowers by time, not by an agreeing capture. Execution verifications (the oracle) stay version-scoped; a test re-run renews them.
- **(b) Validity of the fact in the business** (a surcharge valid from a date). Content, owned by the document; a key could become time-qualified. **Decision: park**; no public subject needs it. Reopen when a subject's documents carry dated values.

### 4. A `superseded` status

- **Reading:** knowgov has the state as a reading: an invalidated statement with a verified or approved successor on the same key is superseded (`gate.resolve`; `stale_on_keys` lists "superseded or not" with the successor). The register has `deprecated` and `retired`.
- **Decision: no new status** (a stored status would duplicate a derived fact and touch both adapters, the schemas and the record). Expose it: the three-valued answer and the bundle say `superseded_by <id>` where a successor exists. S; additive to the MCP output, a patch unless the gate report schema gains a field (then minor). Fold into the MCP follow-up, not its own milestone item.

### 5. Read, model-edit and execute permissions separated for agents

- **Reading:** knowgov already separates them, but nowhere states it as one matrix: read (the page, MCP read-only, `gate_cli`); propose (a capture by an issued handle with `gives`; a pull request); approve, close, settle (`approves`, `closes`, decision-0002; four eyes in the register); edit the model (register pull request, four eyes, both owners on a cross-domain link); execute a business action (nobody: knowgov executes none); a model (`agent:*`) may only read and propose `inferred` statements, never rule.
- **Compatibility:** overlaps task-0059 (security pack), which lists data flows, not authority.
- **Decision: documentation, folded into task-0059** as an added criterion, with a test per row where a test can hold it (the MCP server's refusal of writes, review.py's refusals). S.

### 6. Export to an operational projection (Palantir OSDK or Ontology), one-way

- **In knowgov:** a projection file (register nodes and approved links, statements with their epistemic fields, gaps, change signals; §2's list), schema-pinned, dated, append-only; a per-consumer adapter outside `harness/` mapping it to the consumer's types (for Palantir: a dataset backing object types, or the OSDK and action types to write, which a Foundry enrolment must accept). M for the neutral file, L for a vendor adapter verified on an enrolment. **Contract:** a new schema under `harness/schemas/`: minor.
- **Conflict: m-8's single lighthouse** (task-0062/0063: one *inbound* incumbent, LeanIX + Signavio, Ardoq or ARIS; doc-0012 §6 "one lighthouse ahead of four connectors").

| Block | A. Lighthouse inbound connector (task-0063) | B. Operational projection outbound |
|---|---|---|
| Problem | 0 of 3 export routes verified; nothing has met an installation (E3 = 1) | operational agents rest on unqualified objects |
| Customer | the EA team owning the register's content | a platform team running an operational ontology |
| Value | the gate and the walk answer on a client's own design; E moves | epistemic state reaches the operational layer |
| Precondition | an incumbent and a pilot (task-0062) | a *verified* source to project from, which is A's output |
| Cost | one connector, verified once | one schema, one adapter per consumer, a Foundry enrolment to verify on |
| Evidence it is wanted | both external reviewers, doc-0012 | this assessment only; no pilot asks |
| Risk | the pilot slips | building a projection of synthetic content |

**A wins.** B projects what A makes real; built first, it projects synthetic content and verifies nothing. Two connectors in two directions split one maintainer against both reviewers' advice. **B parked in m-4** with a trigger: the lighthouse pilot, or a second organisation, operates an operational ontology and asks for it. Until then the read-only MCP server (task-0056) is the cheap route: an operational platform's agent can consult the gate directly, with no sync and no copy. One exception, cheap and vendor-neutral, is allowed now: a test that the rdflib store's Turtle carries every field §2 lists (candidate 7), which is the projection's content without its contract.

### 7. Round-trip portability proof

- **In knowgov:** the store serialised to its open form (Turtle, `KG_RDFLIB_FILE`), reloaded into a fresh store of the other kind, gives the same gate reports and three-valued answers for every scenario; the register is plain TOML in git and needs no proof beyond its checker. M (a Neo4j-to-Turtle read through the port's existing reads; no new port method if `assertion_rows`, `supported_by`, `candidate_for` and the verification reads suffice, else the port grows: minor).
- **Compatibility:** supports task-0058 (licence for adapters), task-0059 (security pack: exit) and the assessment's interoperability criterion, asked of knowgov itself. No conflict.
- **Decision: build, low priority, m-8** (a buyer's exit argument), after task-0056 lands.

### 8. The POC sequence as a lighthouse scenario

- **Reading:** the assessment's nine steps map onto m-8: 1–2 task-0062; 3 task-0063; 4 the capture milestone and the gaps; 5 the walk and task-0056; 6 no counterpart (knowgov executes nothing; its analogue is the gate stopping a build); 7 the security pack and reconciliation (task-0059, the export's `RECONCILE.json`); 8 candidate 7; 9 the outcome study (task-0057) plus a cost line.
- **Decision: build as an evaluation protocol**, not a new scenario: the seven criteria of §2, restated for the stack, become the lighthouse's acceptance checklist, rehearsed first on CargoQuote and the J-F kit in the example instance with public evidence, then run on the pilot with private evidence. S–M, docs plus a script that collects the public evidence. Depends on task-0062 for the pilot half only. No banking scenario: the rehearsal uses the public subjects.

### 9. Actions

- **Should knowgov ever execute business actions? No.** The assessment's own recommendation separates concern 1 from concern 2; executing would need transactions, compensation and operational authorisation (A9 shows how much even Palantir bounds), would put knowgov on the operational path, and would break "writes are pull requests" (decision-0001's boundary, the MCP server's read-only rule).
- **What it can do instead:** gate the *definition* of actions. An action type's submission criteria and the decision logic it calls are declared design, read from documents like any decision table. knowgov can answer "may this action type's change ship?" in the consumer's model-change review (Palantir: an ontology proposal on a branch, A8) exactly as it answers for code. That is the integration point worth keeping in view; it waits on candidate 6's trigger.

### R1. Proposal to ieam-register: decision models as a taxonomy

The assessment's sixth taxonomy, decision models, governs processes and constrains actions. The register has seven taxonomies without it; decision tables and DMN files are documents whose statements knowgov reads (CargoQuote `screening_decision.dmn`; the J-F decision tables). **Proposal, not built here:** a `DEC-` taxonomy (decision_domain, decision, decision_table) and a `governs` relationship (DEC → PROC), so the walk reaches "what a change to a decision touches" and a decision has an owner and an approval. ieam-register's decision, under its 0001; trigger: the lighthouse incumbent holds decision models (Signavio and ARIS both author DMN), which task-0062 decides. Until then decision logic stays documents and statements, which already works.

## 6. Proposed tasks (for the coordinator to mint)

| # | Title | Milestone | Priority | Depends on | Decision first |
|---|---|---|---|---|---|
| P1 | Decide whether a document's verification by review lapses by date, under the register's review cadence | m-5 | medium | decision-0004 (PR #100) | yes |
| P2 | Lapse by date for review verifications, as P1 decides | m-5 | medium | P1 | — |
| P3 | Lighthouse evaluation protocol: the seven POC criteria for the stack, rehearsed on the public subjects | m-8 | medium | task-0056; task-0062 for the pilot half | no |
| P4 | Round-trip proof: the store through Turtle into the other adapter, the same gate | m-8 | low | task-0056 | no |
| P5 | Superseded and its successor in the three-valued answer and the bundle | m-8 | low | task-0056 | no |
| P6 | Crosswalk of knowgov's basis and status to provenance vocabularies (the assessment's §7, PROV-O) in the glossary and the guide | m-6 | low | — | no |
| P7 | Amend task-0059: a permission matrix (read, propose, approve, close, edit the model, execute) with a test per enforceable row | m-8 | medium | — | no |
| P8 | Operational projection: a schema-pinned, one-way export for an operational ontology (parked) | m-4 | low | task-0063 verified; a consumer asks | yes |
| P9 | Proposal to ieam-register: a decision-model taxonomy and a governs relationship | m-8 | low | task-0062 | yes (ieam-register's) |

Descriptions and acceptance criteria:

**P1.** A review verification never lapses by date: a statement verified by review stays verified however long its document goes untouched, while a person's answer lapses in six months (register 0008). The register already sets review months per kind. Options to weigh: (a) no date lapse, documented; (b) the owning kind's review months, then the statement reads validated; (c) a single default. AC: a decision record with the options, their effect on the record's S1–S7 verdicts and on `--baseline record`; consistent with decision-0004's answer; names the contract change under decision-0003.

**P2.** As decided in P1. AC: `valid_until` carries a date on review verifications where P1 says so, both adapters; a lapsed verification lowers the key and the gate report names it as a finding; the deterministic record is unchanged (or the comparator's change is recorded with its reason); `instance/README.md` and the guide say when a review falls due.

**P3.** The assessment's POC criteria are what an evaluator will ask of the stack; knowgov should answer them first on public content, then on the pilot. AC: one adopter-register document lists the seven criteria with the stack's evidence for each; a script collects the public evidence from the example instance (walk, gate, three-valued answer over MCP, invalidation, export manifest) on CargoQuote and the J-F kit; the pilot half is a checklist whose evidence stays in the private record; criterion 6 (actions) is stated as out of scope with the reason; no banking scenario.

**P4.** Portability is asked of every platform, knowgov included; the rdflib store already writes Turtle. AC: a test loads a scenario, serialises the store, reloads it into a fresh store and compares gate reports and three-valued answers for every scenario of both subjects; the Neo4j direction runs in the stack job; any port method added is named as a contract change.

**P5.** "Superseded" is a reading of an invalidated statement with a verified or approved successor; agents see "invalidated" and miss the successor. AC: the three-valued answer and the bundle name `superseded_by` where a successor exists; the S6 record shows it after re-verification; schema change, if any, recorded.

**P6.** Evaluators arrive with provenance vocabularies (the assessment's derivation methods and validation statuses, W3C PROV-O). AC: a table maps every basis and status to them, including what has no counterpart; `demo/GLOSSARY.md` and `docs/guide.md` carry it; no field changes.

**P7.** The assessment's separation of read, model-edit and execute is a procurement question. AC (added to task-0059): one table of who may do what, per actor (model, agent over MCP, pipeline, person by role, register approver); "execute a business action: none" stated; each enforceable row cites its test.

**P8.** Parked until a pilot runs an operational ontology. AC when started: a projection schema under `harness/schemas/` (§2's seven points); dated, append-only delivery; a reconciliation that reports drift; no vendor named under `harness/` or `demo/app`; an adapter verified on a real enrolment.

**P9.** AC: an ieam-register issue or pull request proposing a `DEC-` taxonomy and `governs`, with the walk row it adds and the CargoQuote and J-F nodes it would hold; nothing in this repository changes until it is approved and vendored.

## 7. What would reopen this

- Palantir documents a native verification status, provenance of a claim, or an agent policy that withholds on unverified objects: re-score doc-0012's V2 and V3 for Palantir and revisit candidate 6's priority.
- A pilot operates an operational ontology: start P8; candidate 9's model-change gate with it.
- A reasoner creates statements here: candidate 1.
- A subject's documents carry dated values: candidate 3 (b).
