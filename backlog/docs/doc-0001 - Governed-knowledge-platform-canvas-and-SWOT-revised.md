---
id: doc-0001
title: 'Governed knowledge platform: canvas and SWOT, revised'
type: specification
created_date: '2026-11-01T14:28:00Z'
updated_date: '2026-11-01T14:29:00Z'
tags:
  - canvas
  - swot
  - brief
---
*2026-11-01. Maintainer register. Nothing built; this note is the brief to carry into the
main session. Record first (ROADMAP, decisions/), pages are views.*

## 0. Decisions taken in the side conversation

- **Vocabulary.** *Store* is the graph; *repository* is git. *Platform* is the harness, store
  port, page and register adapter, a programme project in the site's sense. An *instance* is
  a git repository holding one organisation's register and artefacts; a *subject* is its kit.
  The word *project* is not used: it already means a programme item on fdurieux.github.io,
  a change initiative in EA, and would collide with both.
- **Taxonomies, from `metamodel/types.toml`:** capabilities CAP (business capability map,
  Archi), products PRD (ARIS), journeys JRN (ARIS), processes PROC (ARIS), applications APP
  (Archi), information ENT (EDM), organisation ORG (authored; ownership is `owns`, never a
  parent). Ten relationship types: requires, concerns, is_supported_by, realizes, delivers,
  supports, crud, manages, owns, maps_to. Lifecycle draft → proposed → approved → deprecated
  → retired; four eyes; both owners on a cross-domain link. No metamodel change needed.
- **Instances are public or private.** The public test case is vendored at a tag; a private
  instance is created from it inside the client's repositories, mounted by the container,
  never pushed out. One stack per instance.
- **The instance repository holds the artefacts** of the site's "Artefact by artefact" table,
  in four trees: the register's own trees; `artefacts/<kind>/` for authored content (git
  authoritative); `exports/<system>/<date>/` with manifests (git a mirror); `record/`.
  The store holds status, provenance and links, never content.
- **Store is a port, Neo4j the first adapter**, in-memory rdflib the second (already a
  dependency; lets the deterministic half and the tests run without a container).
- **Model endpoint: option 1.** One OpenAI-compatible adapter configured by base URL, key
  variable and model name. Covers OpenAI, Google's compatible endpoint and a private model
  behind a gateway. Off for a private instance until an endpoint is set; any model other
  than the record's is marked a deviation.
- **Systems of record staging.** ARIS and Archi first, export routes verified on the pilot
  slice. Then one taxonomy at a time into git by decision record (sources.toml
  `authoritative_for` and `id_field`); the register ids survive. Diagrams are views; a model
  as text (BPMN, Structurizr DSL, ArchiMate XML) can be a record. Journeys and products have
  no as-code notation: the register itself becomes their record, ARIS a publication.
- **Tacit knowledge: written down or recorded as a gap, nothing else.** Captured by the three
  cheap routes: a static questionnaire generated from the gate's gap list per owner; required
  fields in the register (`rationale`, exception reason, decision record, plus a "source of
  this knowledge" person-and-date field); review-driven elicitation on `review_due`. A model
  may propose (`inferred`, `proposed`) and never promote; the transcript is never the record.
  Still needed in the metamodel: a person as a source kind and an `elicited` evidence class
  with a shorter review period.

## 1. The objective, as a prompt

> Create a private instance of the IEAM register inside the client's repositories from the
> public test case, for a pilot slice of one product and one journey. Register the client's
> artefacts by kind: tool-authored content stays in ARIS, Archi and the data model, referenced
> by id and mirrored as dated exports once each route is verified; plain-text artefacts are
> authored in the instance; identities, the ten relationships, approvals, decisions and
> glossary are the record. Link nodes by approved relationships and artefact fragments to
> nodes as evidence. Gate each artefact kind with the tool the site marks Covered, name the
> gap for every other kind, run the register's checker in CI. Make the pilot answer the
> IEAM's three decision questions and the three-valued answer through the demo's query layer
> once it reads a subject root, with the model endpoint configurable and off by default.
> Capture undocumented knowledge by questionnaire, required fields and review, never by a
> model's say-so.

## 2. Opportunity canvas

| box | content |
|---|---|
| What hurts today | One subject, fixed in seven places of the harness and page. A client instance has nowhere to live. Every export route `unverified`. Tribal knowledge shows up as `unknown` and blocks the gate, with no capture path. |
| What the platform adds | A subject manifest and instance layout read by harness and page; a store port; a configurable model endpoint; the gate, three-valued answer, staleness chain and impact walk on any instance; a gap-driven questionnaire per owner. |
| Who touches it | The maintainer as platform author. The client's architects and process owners as instance authors and approvers. A reviewer replaying a record. An AI coding assistant as the gate's consumer, never a writer. |
| How it is done now | One public demo, CargoQuote only; reuse means a fork. Knowledge capture is ad hoc. |
| What a user gets | Their own register and artefacts answered by the same queries as the demo, their record kept apart from the public one, their gaps listed by owner with a form to close them. |
| What to watch | Second subject loads with no harness edit. CargoQuote comparator green after each refactor. Hard-coded subject sites left: target zero. Export routes verified: 0 of 3 today. Declared gaps closed per review cycle, with denominator. |
| How it starts | 1. Private register instance from the test case, pilot slice, routes verified. 2. Subject root and manifest in the lab tree; comparator green. 3. Second public subject (aris2puml pilot corpus, needs an EPC mapper). 4. Mount route for the private instance; store port; endpoint option 1. 5. Questionnaire and capture fields. |
| What the business risks now | Platform work displacing aris2puml A1b–A4. A second record during the as-code move. Private content near a GPL tree or leaving for a hosted model. Coverage read as a percentage. |
| What the business gains | Evidence toward trigger 8c and Arc E. The IEAM step-4 projection reading a register tag. Artefact kinds moving from Open to Covered rows as they go as-code. A capture path for knowledge that today exists only in people. |
| What it costs | Harness and page refactor with the record as oracle; a layout contract and its test; a third repository and a licence decision; per instance a container, a volume and, if wanted, a model endpoint. No new dependency on pumllint's product path. |

## 3. SWOT, each item with its response

**Strengths**
- Staged pipeline with tests, a byte-for-byte comparator, a published image → keep as the
  regression oracle for every step.
- Vendoring tool, SOURCE note, label namespace of the projection → the instance pattern exists
  in miniature; generalise, do not reinvent.
- Standard-library page reading result files → a subject root is a path change for most of it.
- The register's one-record rule, minted ids and `[source]` pointer → the as-code move is a
  per-taxonomy field change, not a migration.
- Assertion basis and declared gaps already model "a person said" and "nobody knows".

**Weaknesses → response**
- Subject hard-coded in seven places → subject manifest; kit table and family map become data.
- One Community database, wiped whole → one stack per instance; instance id on every write in
  the port; constraints keyed by instance and id.
- No login → read-only, single-operator page; private instances run on the client's network;
  writes stay a pull request.
- Scenarios are a plant, not a feature → optional subject content; the products are the
  queries.
- GPL tree beside private content → third repository; licence decision recorded; the register
  gets a LICENSE file.
- No person as source, no elicited evidence class, no capture practice → two metamodel fields
  by decision record; questionnaire and review as the practice.

**Opportunities → how realised**
- First private instance → instance layout plus mount route; its record stays in its repo.
- Second public subject → aris2puml pilot corpus; the EPC mapper is also the site's planned
  EPC toolchain project.
- IEAM step 4 reading a register tag → the projection becomes the register adapter.
- One layout for register and platform instances → the four trees above.
- Gate-contract conformance → CLI form of the gate: exit codes 0/1/2, JSON under a schema,
  record as baseline, evidence tags; claims the cross-artefact and glossary rows honestly.
- As-code move → Open rows become Covered rows (Structurizr, bpmnlint, pumllint).

**Threats → mitigation**
- Drift onto pumllint's product path (never-build N1) → structural boundary of a third
  repository; `pumllint/` imports nothing from the lab and reads no register.
- Scope against the critical path → step 2 time-boxed by the comparator; steps 4–5 only on
  the client's go, which is the §11 trigger.
- Enterprise-only features → port tested on Community; refused constraints stay application
  checks (D1).
- Exposure: live console, and private artefacts or interview answers leaving for a hosted
  model → localhost rule and firewall; endpoint off by default; option 1 sends only where
  the instance's configuration says.
- Two records during the as-code move → one taxonomy at a time; the old tool read-only for
  that taxonomy; decision record per move.
- A model leading the witness → questions generated from the gap list and reviewed; model
  output stays `inferred`/`proposed`; the dated note and human verification are the record.
- Built for an imagined adopter → layout proven on two public subjects before any private one.

## 4. Open for the main session

1. Whether the harness leaves pumllint's tree, and under which licence.
2. Which export route to verify first on the client's installation, and whether ARIS stays
   as publication (needs an import route, untested).
3. Which of the six demo questions the pilot must answer first; proposal §5 names three.
4. The two metamodel additions (person as source kind, `elicited` evidence class with shorter
   `review_due`) as one decision record.

---

*Added to the backlog 2026-11-01 as the brief behind decision-0001 and tasks task-0001 to
task-0009. Open item 1 was answered the same day: the harness moves here under
GPL-3.0-or-later (decision-0001). Items 2 to 4 stay open; item 4 belongs to ieam-register's
decision records, not to this backlog.*
