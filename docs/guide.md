# An adopter's guide to knowgov

This guide is for an organisation that wants to try knowgov on its own documents: an architect,
a process owner, or whoever runs the platform for them. It explains what knowgov is for, the
order to do things in, and what each answer can and cannot be trusted for. The detail lives in
four other files, and this guide links to them:

- [`demo/README.md`](../demo/README.md): the demo stack, what the store holds, starting it, keeping it current;
- [`instance/README.md`](../instance/README.md): your own instance, its layout and its checks;
- [`subjects/README.md`](../subjects/README.md): a subject's manifest, field by field;
- [`demo/GLOSSARY.md`](../demo/GLOSSARY.md): the words the page uses, one per concept.

The brief behind this guide is `backlog/docs/doc-0008`. Every number quoted below comes from the
public, synthetic content in this repository: the CargoQuote kit and J-F's data load.

## 1. What knowgov is for

A model that writes code builds from whatever its documents say. That includes what nobody
decided, what two documents say differently, and what a person guessed and nobody checked.
knowgov reads your documents into a store, one fact at a time, and records for each fact where it
came from and whether anyone has verified it. Before a coding task starts, a *gate* reads the
facts the task needs and gives a verdict.

What that changes was measured in the proof of concept (pumllint's
`docs/neo4j-governed-knowledge-evaluation.md`, one model, five runs per arm). In scenario S2 the
documents leave one rule open: what to do when the screening service is down. The *baseline arm*,
which got the documents only, wrote code in 5 of 5 runs. Each time the code turned the outage
into an error and failed the planted check. The *governed arm*, which got the gate's verdict and
its evidence, stopped in 5 of 5 runs and asked for the decision. Across the blocked scenarios the
governed arm never wrote code under a BLOCKED verdict: 20 of 20 runs.

The gate also follows change. In scenario S6 a verified price changes from 316.00 to 341.00. The
store finds the four facts that rested on the changed text, ends their verifications and marks the
code built from them suspect. The gate blocks until someone verifies the new values.

**What the gate cannot see.** It sees knowledge that is missing, contradictory, vague, unverified
or out of date. It cannot see knowledge that is consistently wrong. In J-F's degradation test the
same defect was planted in every document (scenarios D3 and D5). The gate said QUALIFIED, the
defect reached the code, and only the pristine oracle caught it: 17 and 20 failing scenarios.
QUALIFIED means "build, stating your assumptions". It does not mean safe.

**What stays yours.** knowgov never approves anything. Approval and review are a person's act,
recorded with a handle, a date and a decision record. A model's output stays *proposed* or
*inferred* until a person reviews it.

## 2. The words

These are the words the page and this guide use. [`demo/GLOSSARY.md`](../demo/GLOSSARY.md) has the
full list and the synonyms to avoid.

| word | meaning |
|---|---|
| register | the list of your architecture's building blocks and the typed links between them, in its own repository layout ([ieam-register](https://github.com/fdurieux/ieam-register)) |
| node | one building block in the register: a capability (`CAP-`), product (`PRD-`), journey (`JRN-`), process (`PROC-`), application or module (`APP-`), information node (`ENT-`, your data model's business entities) or organisation unit (`ORG-`) |
| link | one typed relationship between two nodes, such as `supports` or `realizes`, with a state, an owner and an approval |
| state | where a node or link is in its life: draft, proposed, approved, deprecated, retired |
| document | one of your files: requirements, a decision table, a BPMN model, an OpenAPI contract |
| kind | the sort of document, one folder under `artefacts/` per kind |
| fragment | a piece of a document (a table row, a process step), with a digest of its bytes |
| assertion | one fact read from a fragment: an entity, a property and a value, with its basis and status |
| status | where an assertion is in its life: proposed, validated, verified, approved, disputed, invalidated |
| subject | one body of documents the platform loads, with the task it answers and the keys that task needs |
| key | one fact a task needs, such as the surcharge of pricing step P2 |
| gate | the check that reads a task's keys and gives a verdict |
| verdict | PROCEED (build), QUALIFIED (build and state your assumptions) or BLOCKED (do not build) |
| store | the graph that holds the assertions: Neo4j, or an in-memory store for tests and a first try |
| projection | a copy of the register loaded into the store beside the assertions, so one query can cross both |

## 3. Try it on public content

Start the demo stack as [`demo/README.md`](../demo/README.md) describes ("Quick start on a Mac,
step by step"). It needs Docker. It works offline from the first start, and needs no model key.

1. Open `http://localhost:8080`. The page opens on CargoQuote's first scenario.
2. On the card **S2 missing, declared**, press **Replay**. The report shows the record's result:
   BLOCKED, the governed arm abstaining, the baseline arm's code failing the planted check.
3. Press **Deterministic** on the same card. The harness reloads the documents, runs the rules
   and the gate, and shows the fresh numbers.

In plain English: Replay shows what was recorded. Deterministic re-runs the part with no model and
compares it with the record. The last sentence of the plain-English block says whether they
match. For S2 it reads "identical on all 108 fields compared with results/S2, timestamps aside".

4. Replay **S6 invalidated by change** to see a change travel through the store.

Without Docker, you can run the deterministic half in memory:

```bash
cd harness && KG_STORE=rdflib python run.py --deterministic --out ../runs/try && cd .. && python demo/tools/compare_deterministic.py runs/try
```

In plain English: this loads all seven CargoQuote scenarios into an in-memory store, runs the
rules and the gate, and compares every result with the record. It needs Python and the pinned
packages the `harness.yml` workflow installs. It exits 0 when nothing differs.

To see what an instance of your own will look like, build one from the public content:

```bash
python tools/example_instance.py /tmp/example-instance
```

In plain English: this builds an instance from the public register and the CargoQuote documents,
sorted into their kinds, and checks it. It writes only into the folder you name. It ends with
"layout holds".

## 4. Your instance

An *instance* is a git repository of your own that holds your register, your documents and your
subjects. It is private and stays in your organisation's repositories. The platform reads it
read-only and never writes to it.

```
<your instance>/
  register/            your register, in ieam-register's layout
  artefacts/<kind>/    your documents, one folder per kind
  subjects/<id>/       one folder per subject; its documents are named by path
  record/<subject>/    your own results, kept as evidence
```

There is one register per organisation, shared by every subject in it.
[`instance/README.md`](../instance/README.md) describes each folder and the kinds.

Check the instance before you start the stack on it:

```bash
python tools/check_instance.py /path/to/your/instance
```

In plain English: the check confirms the register is there, that every subject loads, and that
every document a subject names exists. It lists your documents kind by kind with the mapper that
reads each one. *ABSENT* marks a document no mapper reads. *UNREAD* marks a file under
`artefacts/` that no subject names. It exits 0 when the layout holds, 1 when it does not and 2
when it cannot run.

Then start the stack on it, as [`instance/README.md`](../instance/README.md) shows ("Starting the
demo on your instance"). The page then lists your subjects and reads your register.

## 5. Adding a document

### What happens today

You add a file under `artefacts/<kind>/` and name it in a subject's `subject.toml`. At the next
load, a *mapper* reads it into assertions. A kind with no mapper is still loaded as a document:
the load reports it as `unmapped` and the store holds no assertion from it, so nothing is skipped
silently. A file a mapper cannot parse makes the run fail.

Before the load, `tools/preload_check.py` checks each document's form with its kind's linter
where one runs here: today pumllint, for PlantUML models (see "A check before the load" below).
For every other kind nothing checks the form yet: a malformed BPMN model, an OpenAPI file with
broken references or a Gherkin file with a syntax error reaches the mapper as it is, and the check
lists it as unchecked, naming the tool your instance would add.

### Which tool checks which kind

The Legible programme's table "Artefact by artefact: tools, practices, gaps"
([fdurieux.github.io](https://fdurieux.github.io/)) names a tool per kind. The table below sets it
beside the kinds of `instance/kinds.toml`, whose `lint` field holds the same two columns. "Gate-ready"
means the tool exits non-zero on a finding today.

| `artefacts/` folder | tool the programme names | gate-ready | knowgov mapper |
|---|---|---|---|
| `plantuml-models` | pumllint | yes | sequence, containers, plantuml_realises |
| `aris-epc` | aris2puml, then pumllint | through pumllint | none: convert first |
| `textual-requirements` | StrictDoc, Doorstop, Sphinx-Needs, OpenFastTrace (planned) | pass or fail | requirements, requirements_json |
| `user-stories` | none | no | none |
| `specification-prose` | Vale, markdownlint | yes | spec, contracts_markdown |
| `acceptance-scenarios` | gplint | partly | gherkin, gherkin_tagged |
| `bpmn-process-models` | bpmnlint (planned) | errors and warnings | bpmn |
| `decision-tables` | dmnlint, for `.dmn` files | no threshold | decision_table, dmn, dmn_decisions |
| `cross-artefact-links` | pumllint `trace` (planned) | yes | links |
| `architecture-decisions` | adr-guard, adrpy-ai (both before 1.0) | yes, young | none |
| `c4-models` | Structurizr CLI | yes | none |
| `archimate-models` | Archi's validator | no | none |
| `sysml-capella-models` | Capella's rules | partly | none |
| `api-contracts` | Spectral, vacuum, Redocly | yes | openapi |
| `schemas` | buf, graphql-eslint, sourcemeta jsonschema | yes | none |
| `data-models` | SQLFluff, dbt-checkpoint, dbt_project_evaluator | yes | none |
| `threat-models` | pytm, Threagile | write your own check | none |
| `event-logs` | process-mining conformance, such as PM4Py | write your own check | none |
| `glossary` | none | no | none |
| `property-invariants` | the test runner | yes | none |

Read it this way. Five kinds have a working tool and a mapper: PlantUML models, specification
prose, Gherkin, decision tables and API contracts. A check before the load is worth most there.
Three have a mapper and only a planned tool: requirements, BPMN and the cross-document links.
Five have a tool but no mapper, so they are checked and not read. Seven have no tool that can stop
a build.

Two cautions. A decision table written in Markdown (CargoQuote's `decision_table.md`) is not a DMN
file, so dmnlint does not read it: markdownlint checks its form and nothing checks its content.
A conceptual or logical data model has no tool at all. In knowgov, its only record is the
register's information nodes.

### A check before the load

```bash
python tools/preload_check.py /path/to/your/instance --since origin/main
```

1. A contributor opens a pull request in your instance that adds or changes a file under
   `artefacts/<kind>/`.
2. The instance's CI (copy `instance/ci/preload-check.yml`) runs `tools/preload_check.py` on the
   changed files, then `tools/check_instance.py`. Each file is linted by the tool its kind's
   `lint` field in `instance/kinds.toml` names, when that tool runs here: pumllint for
   `plantuml-models`, today the only one. A file of any other kind is listed as unchecked, with
   the tool the programme's table names, so the gap stays visible; it does not fail the check.
3. Your branch protection requires that job to pass, and a reviewer who is not the author.
4. The load reads only what was merged. Nothing loads from a branch.

The check keeps the exit codes of the programme's gate contract: 0 clean, 1 a finding at or above
the threshold you set (`--fail-on`, `major` by default), 2 could not run (a linter missing, a
folder that is not a kind, a file that does not exist). `-f json` writes the report under
`harness/schemas/preload-report.schema.json`.

Not built yet: a baseline per kind, so the check fails only on a regression over documents that
already exist (pumllint's own `score --baseline` does this for PlantUML meanwhile); running the
other kinds' tools, which your instance adds as steps of its own; and recording each document's
verdict on its `Version` node in the store.

### Why this is not the knowgov gate

The two checks answer different questions, and neither replaces the other.

| | check before the load (`tools/preload_check.py`) | knowgov gate (`harness/gate_cli.py`) |
|---|---|---|
| question | Is this document well formed for its kind? | Is the knowledge this task needs good enough to build on? |
| looks at | one file | one task's keys, across every document |
| runs | on the pull request, before the merge | after the load, before a build |
| finds | syntax, broken rules, a score | missing, declared-open, contradicting, unverified, invalidated knowledge |
| misses | two well-formed documents that disagree; a fact nobody wrote down | a malformed file the mapper still read; anything no mapper reads |

In S2 every document is well formed, and the gate still blocks: the rule is declared open. Both
checks pass documents that are consistently wrong (J-F D3).

## 6. Capturing what people know

Some knowledge is in nobody's documents. The gate then reports a key as *absent* or as a
*declared gap*, and blocks. The capture path turns a person's answer into a recorded assertion:
a questionnaire per owner, generated from the gate's gaps, and its answers read back in at
*proposed*. [`instance/README.md`](../instance/README.md) ("Capturing what people know") gives the
commands. `backlog/docs/doc-0007` walks through it on S2, S4 and S3, with one employee as the
example.

Know three limits before you rely on it:

- An answer reads *proposed*. The gate lists it as an assumption, so it moves a key from absent
  to QUALIFIED at most.
- A captured answer does not close a declared gap. Only the gap's owner can close it.
- Who may approve an answer, close a gap or settle a dispute is decided (`backlog/decisions/`,
  decision-0002) but not built yet (task-0037). Until then, no command takes S2 from BLOCKED to
  PROCEED.

## 7. Reading the dashboard

### The header

- **subject**: the subjects the stack serves. Picking one reloads the page on it.
- **store chip**: which store, whether it answers, and which scenario it holds. The store holds
  one scenario at a time, of whichever subject loaded it last.
- **arms chip**: amber "arms disabled: set …" means no model key is set. Replay and Deterministic
  still work.
- **register chip**: "register not projected" until you press *Project the register* (Neo4j
  only).

### The scenario cards

Each card shows the scenario's id and title, the record's verdict, what the store found and what
the arms did. Its three buttons re-run nothing (**Replay**), the part without a model
(**Deterministic**), or everything (**Arms**). CargoQuote's seven verdicts in the record: S1
PROCEED, S2 BLOCKED, S3 QUALIFIED, S4 BLOCKED, S5 BLOCKED, S6 PROCEED after BLOCKED, S7 BLOCKED.
The **Arms call** box above them picks the model and the effort. Any choice other than the
record's makes a run a *deviation*, shown in red, whose numbers are not comparable with the
record's.

### The report's head

- **verdict** and **source**: the gate's verdict, and which results you are reading: the record,
  or a run of your own stack.
- **Planted**: the defect, in the subject's words.
- **Gate**: why the verdict. For S2: two keys at a blocking level,
  `QuoteAPI|on_screening_outage` (declared gap) and `response|hold_presence` (absent).
- **Required keys**: how the task's keys stand. For S2: 36 keys, 33 approved, 1 validated,
  1 declared gap, 1 absent. *Validated* means two documents agree and nothing verified it.

### In plain English, and the glossary

A few sentences written from the results: how to read the page, what was planted, what the store
found, the verdict, what each arm did, what it shows. For a run of your own it ends with the
comparison with the record. The glossary card under it defines every word the page uses.

### The pipeline strip

One box per stage, coloured by its outcome; a click opens the stage's panel. For S2:

| box | S2 | how to read it |
|---|---|---|
| ingest | 89 fragments | pieces cut from the documents, each with a digest |
| extract | 137 assertions, 0 unresolved symbols | facts read by the mappers |
| load | 564 nodes, 1383 relationships; 6 of 9 constraints accepted | the free edition refuses three constraints; the platform checks those itself |
| rules | R-CORROBORATE 81, R-REQ 3, R-UNVERIFIED 35 | hits per rule: agreeing pairs, missing knowledge, assertions nobody verified |
| gaps | 38 gaps | opens the gaps view |
| gate | BLOCKED | the verdict and the keys behind it |
| register footprint | 3 keys below approved touch 7 nodes | opens the footprint |
| generate · G / B | G abstained 5 of 5; B wrote code 5 of 5 | what each arm decided |
| oracle · G / B | G nothing to grade; B 10 of 11, five times | the kit's acceptance scenarios run on the code |

### The gaps view

Every gap of the scenario, grouped by kind with a filter: for S2, declared missing 1, undeclared
missing 2, ambiguous 0, conflict 0, unverified 35. A *declared* gap is one the authors wrote down
as open; an *undeclared* one is a fact the task needs that nobody wrote. Both block. The **Source**
line says whether the rows also come from the live store, which is the case only when the store
holds the scenario on screen.

### The register footprint

The gate's keys set against the register, through the subject's `register_map.toml`. For S2,
three keys below approved touch seven nodes, all of them approved: QuoteAPI, ScreeningService,
the Quote information node, two journey elements and two processes. Read it as "these parts of the
architecture rest on knowledge the gate would not let you build on". Red would mean a touched node
that is not approved, or a gap no link cites.

### The systemic view

The Legible model's knowledge view, twice: the governed arm on the left, the baseline arm on the
right. Tags mark where the defect entered and where it was stopped. For S2 the gate stopped it for
the governed arm; for the baseline arm only the oracle did. Solid lines are measured, dashed lines
are a hypothesis.

### S6's second strip

S6 has a second row of boxes: the changed document read in again (2 fragments new, 16 reused),
the staleness rule (4 assertions invalidated, the S1 code marked suspect), the gate BLOCKED, the
re-verification of 3 replacements, the gate PROCEED.

### Runs

Each Deterministic or Arms press writes a dated folder under `runs/`. The **Demo runs** card lists
them, and the report's **source** drop-down offers each one beside the record.

### The register

The last entry of the scenario list opens the register: its tag and the digest check, the
checker's coverage lines (C1 7 of 8 covered, 1 excepted; C2 5 of 5; C3 5 of 5 on the public
register), the nodes by taxonomy, the relationship types with how many links of each are approved,
and the **Impact** box. Section 8 explains the impact box.

### The store card (Neo4j only)

What the store holds, whether the register is projected, the **Open Neo4j Browser** link, and the
**Saved Cypher** list. Each saved query carries a chip: *runs now*, or what it needs, such as
"needs S4 loaded". A query run against the wrong state returns no rows and a warning, and that is
correct. On the in-memory store this card shows only the counts: there is no Browser and no saved
Cypher.

## 8. Seeing what a change touches, in Neo4j

### Two kinds of impact

A change can travel two ways, and knowgov answers each with a different part of the store.

- **A change to the architecture.** You plan to retire, replace or rework one node of your
  register: a capability, a journey, a process, an application or one of its modules, or an
  information node. You want to know which other nodes rest on it. The *register* answers this.
- **A change to a document.** Someone edits a document the store has read, such as a decision
  table. You want to know which assertions no longer hold and which generated code was built on
  them. The *store's assertions* answer this.

Both live in one Neo4j store once you project the register into it, so one query can cross from
one to the other.

### Before you start

1. Start the stack and open the page.
2. On a scenario card, press **Deterministic** for the scenario you want in the store. For the
   document example below, that is **S6**.
3. In the store card, press **Project the register**.
4. Open **Open Neo4j Browser** from the store card and log in as `neo4j` with your password.

In plain English: the store holds one scenario at a time, and every run first empties it. So load
the scenario first and project the register second. The other way round, the run wipes the
register, and every query below returns no rows with a warning that the `RegNode` label is not in
the store. That warning means "project again", not "something is broken".

### The walk: what retiring a node touches

In the register view, type a node id in the **Impact** box and press **walk**.

In plain English: the walk starts at your node and follows links outwards. From an application or
module it follows `supports` to processes. From a process it follows `delivers` to products,
`realizes` to capabilities, and `is_supported_by` backwards to the journey steps the process
supports. From a journey it follows `concerns` to products. It follows **approved** links only. A
link that is not approved, or whose far node is deprecated or retired, is listed as *withdrawn*
and not followed. The walk does not climb to a node's parent.

Example: the QuoteAPI module, `APP-0002`.

| from | relationship | to | name | followed |
|---|---|---|---|---|
| APP-0002 | supports | PROC-0002 | Validate the request | yes |
| APP-0002 | supports | PROC-0001 | Quote process | yes |
| PROC-0002 | is_supported_by (inverse) | JRN-0002 | Submit a quote request | yes |
| PROC-0002 | realizes | CAP-0004 | Validate a quote request | yes |
| PROC-0001 | delivers | PRD-0002 | CargoQuote instant quote | yes |

Five links, none withdrawn: retiring QuoteAPI touches two processes, one capability, one journey
step and the product. The same walk runs from the command line, with no store:

```bash
python demo/register/tools/impact.py --from APP-0002
```

In plain English: this reads the register's files and prints one line per link with its state,
owner and evidence, then a summary: "5 edges walked, 0 withdrawn; products reached ['PRD-0002'];
journey elements reached ['JRN-0002']".

From a process, `PROC-0004` Price the quote reaches the journey step JRN-0003 and the capability
CAP-0002. From a journey, `JRN-0001` Get a freight quote reaches the product PRD-0002. From a
process with withdrawn links, J-F's `PROC-0006` Daily chain meets six links, two of them
withdrawn, and reaches the product PRD-0005 and three journey steps.

### Seeing the walk as a graph

Under the walk's table the panel shows **The walk in Cypher** in two forms: *rows*, one row per
link, and *paths*, which the Browser draws as a graph. Beside each are **copy** and **open in the
Browser**.

In plain English: **open in the Browser** opens Neo4j Browser on a small guide page. Click the
grey query block once and the query moves into the editor. Nothing runs until you press play. For
APP-0002 the graph shows 6 nodes and 8 relationships. Two of them, a `REG_PARENT` and a
`REG_REQUIRES`, are drawn because the Browser draws every relationship between the nodes it shows.
The walk did not follow them. The table on the page is the walk; the graph is a picture of its
neighbourhood.

### Starting from a capability or an information node

The walk does not start from a capability, an information node, a product or a journey step. From
`CAP-0002` or `ENT-0003` it meets no link, and the panel says "No link starts at this node in a
direction the walk follows". That is the walk's design: it answers "what would retiring this
application or process touch", going upwards. To ask "what rests on this capability" or "what
touches this entity", go the other way. Two saved queries in the store card do that.

**A capability.** The saved query *What rests on CAP-0002* lists what realises or requires the
capability, then steps on from each process that realises it over an approved link.

In plain English: the first part finds what points at the capability: the process that realises
it and the product that requires it. The second part steps from each such process, over approved
links only, to the applications that support it, the journey steps it supports and the products
it delivers. Each row names the link it came by and says whether it was followed. For CAP-0002
Price a shipment: PROC-0004 Price the quote (realizes) and PRD-0002 CargoQuote instant quote
(requires), and through PROC-0004 the TariffEngine module APP-0003 and the journey step JRN-0003.

**An information node, from your data model.** The register's information taxonomy holds the
business entities of your data model under `ENT-` ids. The saved query *What touches ENT-0002*
lists what creates, reads, updates or deletes the entity and which application manages it, then
steps on from each such process.

In plain English: for ENT-0002 Quote request, the process PROC-0002 Validate the request works on
it and the QuoteAPI module APP-0002 manages it. From PROC-0002 the query reaches QuoteAPI again
(it supports the process), the capability CAP-0004 and the journey step JRN-0002. Copy the query
and change the id to ask about another node. For ENT-0003 Quote it reaches PROC-0004 and APP-0002,
then APP-0003 TariffEngine, CAP-0002 and JRN-0003. For J-F's ENT-0010 Seam frame, the link from
the Daily chain is deprecated and shows as withdrawn; the approved one from PROC-0010 Seam frame
export leads on to the product PRD-0004. For ENT-0005 Screening result the only link is a draft,
so nothing is followed: a draft link is not yet knowledge you can act on.

Each query is listed from a start the page picks from your register: the node of that taxonomy,
in the subject's part of the register, that the most links point at. On J-F's page they start
from CAP-0007 and ENT-0008.

### From a module to its documents and its code

A module in your register, such as QuoteAPI (APP-0002), is a node. The code that implements it is
not in the register. The store reaches from one to the other only through the documents the
register's links cite as evidence. The saved query *From APP-0002 to the store* follows that path.

In plain English: start at the module, take each approved link it is part of, follow the link to
the documents it cites, then to every assertion the current version of each document supports,
and to any generated code that used them. With S6 loaded: two links cite `kit/links.toml`
(15 assertions each); REL-08001 cites `contract/openapi.yaml` (10 assertions, used by the S1 code,
listed as `derived:S1:G:run1 (suspect)`); REL-08002 cites `kit/requirements.md` (8). The query
works at the grain of a whole document: a link that cites one requirement still reaches every
assertion of the file. It needs the register projected and a scenario loaded.

What a module change cannot reach today is a change to the code itself. The store records code
only as a *derived output* that used certain assertions. It does not read code, so editing the
implementation invalidates nothing. The direction is always document, then assertion, then code.

### When a document changes: assertions invalidated, code marked suspect

Load **S6** deterministically. In S6 the decision table changes: the P2 surcharge goes from 316.00
to 341.00, and the file is read in again as version 2.

In plain English: the store compares the new version's fragments with the old ones by their
digests. Two fragments are new and 16 are reused. Every assertion supported by a fragment that
changed is *invalidated*, its verifications end, and any code built on it is marked *suspect*. The
gate blocks until the replacements are verified again.

The saved query *The invalidation traversal (S6)* lists it:

| changed fragment | invalidated | old value | verification ended | code | replacement |
|---|---|---|---|---|---|
| DT-P/row/P2 | A:dt:P2\|surcharge@v1 | 316.00 | yes | derived:S1:G:run1, suspect | 341.00, approved |
| DT-P/row/P2 | A:dt:P2\|threshold@v1 | 1244 | yes | derived:S1:G:run1, suspect | 1244, approved |
| DT-P/para/worked-example | A:dt:worked_example\|price@v1 | 8652.49 | none | none | 8682.24, proposed |
| DT-P/para/worked-example | A:dt:P3\|order@v1 | after P2 | yes | derived:S1:G:run1, suspect | after P2, approved |

Read it row by row: this fragment changed; this assertion no longer holds; this check no longer
counts; this code must be looked at again; this assertion replaces it, with its status. The worked
example's new price is only *proposed*: nobody has verified it yet. On the page, S6's second strip
shows the same story.

### What this section does not do

- The walk and these queries read the register as approved. A proposed or draft link is listed
  but never followed.
- Nothing here writes to the register or to the store. Projecting is a copy, and a run deletes it.
- The capability, information-node and module queries step one link past the start's first
  neighbours. They are not a full walk.

## 9. The gate in a pipeline

A build needs the gate's answer as a command that stops it:

```bash
python harness/gate_cli.py --scenario S2
```

In plain English: the command loads the scenario, asks the gate for the task's keys and lists each
finding on a five-step ladder: blocker, critical, major, minor, info. A key that is absent, a
declared gap, disputed or invalidated is a blocker. A key below verified is major. Then it exits:

- **0** when nothing is at or above the threshold. The default threshold is *blocker*: S1 exits 0,
  S2 exits 1.
- **1** when something is. `--fail-on major` also fails a QUALIFIED answer: S3 then exits 1, with
  4 major and 9 minor findings.
- **2** when it cannot run: no such subject, scenario or task, or no store.

`--baseline record` fails only on a regression against the record: S2 is BLOCKED in the record
too, so it exits 0 and still lists the blockers. `-f json` prints the report in the shape
`harness/schemas/gate-report.schema.json` pins. Outside the stack, add `KG_STORE=rdflib`.
[`demo/README.md`](../demo/README.md) ("The gate as a command") has the full options.

Two limits today. The command runs the first stage only, so it does not see a change like S6's
second stage. And invalidated assertions and suspect code appear in its JSON as counts, not as
findings, so they do not change the exit code (`backlog/docs/doc-0011`).

## 10. Choosing the model, or none

The Arms mode calls a model; nothing else does. The models it may call are rows in
`demo/models.toml`. Each row names the endpoint, the model and the *name* of the environment
variable that holds its key, never the key itself. A row whose variable is empty stays greyed, and
the server refuses it. With no key set, no document leaves your network. A private model behind a
gateway is a row like any other.

Any model or effort other than the record's makes a run a deviation: the page marks it in red and
its numbers are not comparable with the record's. [`demo/README.md`](../demo/README.md) ("Which
model the Arms mode calls") gives the rows and the gateway for a Claude row.

## 11. Keeping it current

The demo carries copies of the register, the Legible model and the public subjects, each at a tag,
each with a `SOURCE.md` that a test holds to its digest. Never edit a copy by hand.
[`demo/README.md`](../demo/README.md) ("Keeping the demo current") gives one command per copy. In
your own instance the register is your checkout, mounted read-only, and none of this applies to it.

## 12. Limits

- The store holds one scenario at a time, and every run first empties it, the projection included.
- The page has no login. Run it on your own network, and do not expose port 7474: it is a live
  console behind one password.
- The walk starts only from applications, processes and journeys. For a capability or an
  information node, use the saved queries of section 8.
- A module reaches its code only through whole documents, and a change to code reaches nothing.
- Before the load, only PlantUML models have their form checked (pumllint). Every other kind is
  listed as unchecked, naming the tool your instance would add (section 5).
- QUALIFIED is not safe. A defect present in every document passes the gate (J-F D3 and D5).
- A person's answer reaches *proposed* at most until the review record is built (section 6).
