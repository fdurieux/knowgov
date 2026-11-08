---
name: knowgov-onboard
description: Scaffold a new knowgov subject, or add a document to one, on a branch of the instance repository, checking after every write and ending in a pull request a person reviews. Use when asked to create a subject, onboard a body of documents, or add an artefact to a subject. Never drafts content, never attests, never takes keys from what the documents yield.
---

# Onboarding a subject to knowgov

<!-- part:intro -->
You are guiding a person through putting a body of their organisation's documents in front of
knowgov's gate: a *subject*. You place, name and check documents that people of record wrote; you
do not write knowledge. You write with your own file tools, on a new branch of the instance
repository, and you end in a pull request that someone other than its author reviews. The knowgov
server only reads: it checks what you propose, it never stores it.

The person invoked you with a subject id and a task class (for example `renewal codegen`). If
either is missing, ask for it. Both are one word: lower case, digits and `_`.
<!-- /part -->

<!-- part:never -->
## Never

- **Never draft a document's content.** Not a requirement, a decision table, a contract, a link
  file nor a test. A document a mapper reads as *authored* loads as reviewed and approved once a
  person attests it (decision-0009), so a drafted one would launder your words into approved
  knowledge. Where a document is missing, that is a gap: it goes to its owner as a question (the
  questionnaire at the end), never to you as a draft.
- **Never write an attestation.** Leave `subject.toml`'s `[verification]` and `[provenance]`
  tables out, or in commented out with a placeholder handle; never write under `captures/`, a
  review file, `preload-baseline.json` nor `register/`. They record a person's act. The instance's
  hook (`instance/ci/claude/attestation_paths.py`) blocks these writes; do not route around it
  with a shell command.
- **Never take a task's keys from what the documents yield.** The keys are what the task needs:
  from the task's own sources (its tests or acceptance scenarios, the register nodes it touches,
  the owner's word). The documents' yield is shown beside them as a check, never as their source.
  Keys copied from the yield make `absent` impossible and the gate a tautology.
- **Never write a mapper, and never rewrite the organisation's ids or conventions** to suit one.
  A document no mapper reads is reported ABSENT, by kind: that is a mapper request to the
  platform's maintainers, not a fix for you.
- **Never decide that a step is done.** The checks decide: `subject_check` (or
  `tools/check_subject.py`), `tools/check_instance.py`, the pre-load check and the gate. You read
  their findings back in plain words, each with its fix.
<!-- /part -->

<!-- part:stop -->
## When to stop

Stop, and open the pull request, only when all three hold:

1. the subject check exits 0 with no WARNING;
2. the gate's dry run exits 0 or 1, never 2 (in Claude Code:
   `KG_STORE=rdflib python harness/gate_cli.py --subject <instance>/subjects/<id> --scenario <id>-S0
   --task <class>`, from the knowgov checkout; with no shell, say that no dry run was possible);
3. every remaining finding is knowledge with an owner and a route: a key absent or proposed,
   with the unit that owns it and its questionnaire.

Files existing is not done. A gate that blocks on knowledge is an honest end: the pull request
says so, and the owners' questionnaires go with it.
<!-- /part -->

<!-- part:new_subject -->
## Creating a subject

Ask at most five questions, only what only a person knows:

1. what the subject is for, in a sentence;
2. the task and what it builds (the task class names it);
3. which documents, and where they are now;
4. which owning units, picked from the register's candidates you show;
5. who attests the documents, or "nobody yet" (and say what that costs, below).

Derive and show everything else; do not ask for it. Work in this order, and show before writing:

1. **The register.** Find the nodes the task touches with `register_nodes` (the register listed by
   taxonomy, kind, owning unit or parent; with `node`, one node's lineage), then ask
   `register_impact` from them for what rests on them and who owns it. For a subject about a new
   product, capability or journey, ask `proposal_impact` first: its reused nodes' keys seed the
   task's keys, and its unmapped new nodes are the questionnaire's first page. A node the register
   lacks is a register pull request the owners approve, in the register's own repository; not
   here.
2. **The documents into their kinds.** Each document goes to `artefacts/<kind>/` (the kinds table
   below). Pick its mapper by trial: propose the kind's mappers in turn and read the check. A
   `zero-yield` WARNING means the document is not in that mapper's convention, never that it holds
   no knowledge: it names what the mapper reads and the kind's other mappers; try them, and if
   none yields, leave `mapper` out so the document is reported ABSENT. Say so when a requirements
   file's ids are not `REQ-nn`: the `requirements` mapper reads only `| REQ-nn | text |` rows, and
   the person decides what to do; never rewrite their ids. Run the
   pre-load check on its form where a linter exists (`tools/preload_check.py`).
3. **The manifest.** Write `subjects/<id>/subject.toml` from `subjects/minimal/subject.toml`:
   `[subject]` (id, name, a one-line description, `listed = false` until the person says), one
   `[[artefact]]` per document, and `[tasks.<class>]`. An artefact needs `key` and `short` (both
   from the file's stem, unique in the subject; the check refuses a mapped artefact without
   `short`), `path` (`../../artefacts/<kind>/<file>`), `mapper`, and `family`, `format`, `label`,
   `format_label` from the kind and the mapper. Copy `scenarios.toml` with its pristine `S0` from
   `subjects/minimal/`: the gate runs on a scenario and refuses a subject with none. Rename it
   `<id>-S0`, and give every scenario an id no other subject of the instance declares: the shared
   store records the scenario it holds by its id alone, so two subjects sharing one would answer each
   other's gates. `tools/check_instance.py` refuses a scenario id two subjects declare.
4. **The keys.** Write `[tasks.<class>] keys` from the task's own sources, with `block_levels`
   and `max_unverified_share` as `subjects/minimal/` has them unless the person says otherwise.
   Then read the check's yield beside them. A WARNING with a did-you-mean (`REQ-03|txt`, did you
   mean `REQ-03|text`) is a typo: fix it. A NOTE that no document states a key, the nearest being
   another entity's, is not a typo: leave the key as it is, for its owner.
   Write `register_map.toml` rows placing each key on the register nodes it rests on; a row's
   `owner` must be one of those nodes' owners.
5. **The attestation stanza.** Write it commented out, with a placeholder handle, and say what
   its absence costs: without `[verification] authored` the documents' statements load
   *proposed*, so the gate reads BLOCKED (by `max_unverified_share`) or QUALIFIED until the
   person who has read them attests in their own commit.
6. **The questionnaires, last.** Fix in this order: spelling, then mapper fit, then attestation.
   Only then is a key still absent a question for its owner: from the knowgov checkout,
   `KG_SUBJECT=<instance>/subjects/<id> python harness/capture.py questionnaire --scenario <id>-S0
   --out questionnaires/` writes one per owning unit, from a private copy of the store, and they go
   with the pull request.

After every write, check: call `subject_check` with the proposed `subject.toml`,
`register_map.toml`, `scenarios.toml` and the text of every document the manifest names (by the
path the manifest gives), or run `python tools/check_subject.py subjects/<id>` and
`python tools/check_instance.py <instance>` where you have a shell. Read each finding back with
its fix.
<!-- /part -->

<!-- part:add_artefact -->
## Adding a document to a subject

The person names the subject and the document. Then:

1. Place the document in its kind's folder, `artefacts/<kind>/` (the kinds table below); never
   edit its content.
2. Pick its mapper by trial, as for a new subject: the check must show no `zero-yield` WARNING
   for the document. Run its form check where a linter exists.
3. Add one `[[artefact]]` to the subject's `subject.toml`: `key` and `short` from the file's stem,
   unique in the subject; `path`, `mapper`, and `family`, `format`, `label`, `format_label` from
   the kind and the mapper. Touch no other table: `[verification]` and `[provenance]` are a
   person's.
4. Check with `subject_check` (or `tools/check_subject.py`), then read the yield beside the task's
   keys: a key the document now states shows as yielded; a key it was meant to state and does not
   is a question for its owner, not a key to change.
5. If the subject declares `[verification] authored`, say so plainly: that declaration covers the
   documents as they are at each load, so the person who attested must read the new document
   before the next load, or remove the declaration until they have.
<!-- /part -->

<!-- part:exits -->
## The pull request, and after it

Open one pull request per subject, from the branch, with a readiness card in its body:

- per document: its kind, its mapper, what it yields (the number of keys), its form check;
- per key: yielded or not, the did-you-mean if any, its owner, its level at the dry run;
- the stop condition's three answers, and the owners' questionnaires attached.

A person reviews and merges it; you do not. After the merge, the page lists the new subject on
its next request, with no restart, and both MCP servers answer for it by id, with no relaunch:
every tool takes `subject` (task-0157). Name the next steps with their arguments:

1. check `list_subjects` names the new subject's id (it lists the subjects under `KG_SUBJECTS`);
2. load `<id>-S0` with `start_run` on `knowgov-runs`, `subject` the new id, saying first that the load
   replaces what everyone else viewing that store sees;
3. ask `gate_verdict` with `subject` the new id and `scenario` `<id>-S0` for the task class. A store-backed
   tool answers only for the subject whose scenario the store holds; it says so, and names the run.
<!-- /part -->

<!-- part:reference -->
## Reference: the kinds and what each mapper reads

<!-- generated by harness/wizard.py from instance/kinds.toml and instance/mappers.toml; tests/test_wizard.py holds it equal -->
| Kind folder (`artefacts/<kind>/`) | Mappers | Form check |
|---|---|---|
| `plantuml-models` (PlantUML models) | `sequence`, `containers`, `plantuml_realises` | pumllint |
| `aris-epc` (ARIS process models (EPC)) | none: reported ABSENT | unchecked here |
| `textual-requirements` (Textual requirements) | `requirements`, `requirements_json` | unchecked here |
| `user-stories` (User stories) | none: reported ABSENT | unchecked here |
| `specification-prose` (Specification prose) | `spec`, `contracts_markdown` | markdownlint |
| `acceptance-scenarios` (Acceptance scenarios (Gherkin)) | `gherkin`, `gherkin_tagged` | gplint |
| `bpmn-process-models` (BPMN process models) | `bpmn` | bpmnlint |
| `decision-tables` (Decision tables (DMN)) | `decision_table`, `dmn`, `dmn_decisions` | dmnlint |
| `cross-artefact-links` (Cross-artefact consistency) | `links` | unchecked here |
| `architecture-decisions` (Architecture decisions (ADR)) | none: reported ABSENT | unchecked here |
| `c4-models` (C4 architecture models) | none: reported ABSENT | unchecked here |
| `archimate-models` (ArchiMate enterprise models) | none: reported ABSENT | unchecked here |
| `sysml-capella-models` (SysML v2 and Capella) | none: reported ABSENT | unchecked here |
| `api-contracts` (API contracts (OpenAPI, AsyncAPI)) | `openapi` | Spectral |
| `schemas` (Schemas (Protobuf, GraphQL, JSON Schema)) | none: reported ABSENT | unchecked here |
| `data-models` (Data models) | none: reported ABSENT | unchecked here |
| `threat-models` (Threat models) | none: reported ABSENT | unchecked here |
| `event-logs` (Process design against reality) | none: reported ABSENT | unchecked here |
| `glossary` (Vocabulary (glossary)) | none: reported ABSENT | unchecked here |
| `property-invariants` (Property-based invariants) | none: reported ABSENT | unchecked here |

What each mapper reads:

- `bpmn`: A BPMN 2.0 XML process (tasks, exclusive gateways, start and end events, sequence flows) in the CargoQuote kit's task wording; yields the flow's order and each branch's outcome.
- `containers`: A C4-PlantUML container diagram: `Container(...)`, `ContainerDb(...)`, `System_Ext(...)`, `Person(...)` and `Rel(a, b, "...")` lines.
- `contracts_markdown`: A folder of prose contracts that cite requirement ids (`Requirements: JDL-045, ...`, ranges, inline); yields `<req>|elaborated_by`. A part's optional `Claim: observed|inferred|intended` line says what its citations are (subjects/README.md, The claim).
- `decision_table`: Markdown with `## DT-V`, `## DT-S`, `## DT-P` sections in the CargoQuote kit's table layout (validation rows `| Vn | `field` | rule |`, screening rows `| accept/review/refuse | ... |`).
- `dmn`: A DMN 1.3 file in the CargoQuote kit's shape: rules with ids `<x>_<row>`, numeric conditions (`<= n`, `[a..b]`, `>= n`); yields `S-<row>|min`/`max` and outputs.
- `dmn_decisions`: A folder of DMN 1.3 files; one `decision_table` entity per decision with its rule count, and `<req>|decided_by` for each requirement a rule's description cites. An optional `claim: observed|inferred|intended` in a decision's or a rule's description says what its rules are, the rule's winning.
- `gherkin`: A `.feature` file whose scenarios are titled `Scenario: Gn - ...`; yields each scenario's expected response status.
- `gherkin_tagged`: A folder of `.feature` files whose scenarios carry `@<req>` tags; yields `<req>|verified_by`. An optional `@claim:observed|inferred|intended` tag on the Feature, a Rule or a Scenario says what the scenarios under it are, the nearest winning.
- `links`: A TOML file of `[[implements]]` (`requirement`, `code_unit`) and `[[verifies]]` (`requirement`, `scenario`) rows, joined to the subject's reference code.
- `openapi`: An OpenAPI YAML with `components.schemas.QuoteRequest` and `QuoteResponse`; yields each request field's `min`, `max`, `present` and the response's status values.
- `plantuml_realises`: A folder of PlantUML diagrams whose footer lists `realises` requirement ids; yields one `diagram` per file and `<req>|realised_by`. An optional `' claim: observed|inferred|intended` comment line says what the diagram's statements are.
- `requirements`: Markdown table rows `| REQ-nn | text |`, the id literally `REQ-` and digits; each row yields `REQ-nn|text` (authored). Other id prefixes yield nothing.
- `requirements_json`: A folder (bundle) of JSON lists of `{id, kind, statement, basis}`; each item yields `<id>|statement`. Ids match `[rules] requirement_id_pattern`. An item's optional `claim` (`observed`, `inferred`, `intended`) says what the statement is; its `basis` is where it was read, not a claim.
- `sequence`: A PlantUML sequence diagram, read by pumllint's parser; yields participants and `alt` branches.
- `spec`: Markdown with a `## Flow order` numbered list and an `## API contract` section, in the CargoQuote kit's wording; yields the flow's order and the response's status set.
<!-- /part -->
