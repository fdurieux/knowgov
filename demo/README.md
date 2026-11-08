# The governed-repository demo

A small web application and a Neo4j database, started together with one
command, that let you walk through the proof of concept recorded in
pumllint's [`docs/neo4j-governed-knowledge-evaluation.md`](https://github.com/fdurieux/pumllint/blob/main/docs/neo4j-governed-knowledge-evaluation.md)
(2026-10-30, pull requests #214 to #218): a specification kit loaded into
a graph database as *assertions* (one statement each, with where it came
from, how it was obtained and whether anyone has verified it), seven
checking rules, a *gate* that decides whether an AI coding assistant may
build from that knowledge, and a comparison of two assistants on seven
planted situations: one that receives the gate's verdict and evidence
(the *governed arm*, G), one that receives the documents only (the
*baseline arm*, B). Every result shown is already committed to this
repository; the demo works offline from the first start.

Trying knowgov on your own documents? Start with the adopter's guide,
[`docs/guide.md`](../docs/guide.md): what knowgov is for, the order of
work, the dashboard field by field, and impact in Neo4j. This file is
the reference it links to.

## What you see

**A menu** of the seven scenarios S1 to S7 (complete, missing, ambiguous,
contradictory, inferred, invalidated by a change, unverified), each with
three buttons.

**A report view** of the selected scenario. It opens with *In plain English*,
a few sentences written from the same result files that say what was
planted, what the store found, what the gate's verdict means, what each
arm did and what that shows, and, for a re-run, whether its numbers
match the record. Those sentences, the stage panels and the gap kinds use
one word per concept and keep to 20 words a sentence; the words are
defined in a *Glossary* card under the block and in
[`GLOSSARY.md`](GLOSSARY.md), and a test holds the page to both. Then two pictures, the first of them clickable, every
box of the pipeline opening a panel with that stage's full data (the
documents read, the constraint attempts, each rule's hits, the 36 keys
with their levels, each run's decision and grade). A *gaps* box beside the
rules opens every gap of the scenario grouped by kind, with a filter and a
plain-English sentence per kind; it reads the result files, and the
running Neo4j as well when the scenario on screen is the one loaded there.
A *register footprint* box ends the strip: which nodes and links of the
IEAM register (see below) this scenario touches, through its keys below
approved, its requirement gaps and, for S6, the changed decision table,
by a map the maintainer approved; red when a touched node is not
approved or a gap is cited by no link. In its panel every id is a
*reference*: click a requirement, a link, a node, a key or a document
and its own panel opens under the table, one level deep, and the
enumerations (kind, declared, level, state, type) explain themselves on
hover:

- the *pipeline*, from reading the files to grading the generated code,
  each stage coloured by its outcome and carrying its numbers: how many
  fragments and assertions were read, what the rules found, the gate's
  verdict and the keys that blocked it, and, for each arm, what the
  assistant decided, whether it wrote code, whether it raised the planted
  problem, and how its code scored on the kit's eleven acceptance
  scenarios;
- the *systemic model*, the reduced "knowledge view" of the Legible impact
  model (version 0.3, vendored under `model/`), with the scenario's defect
  placed where it entered and the path it travelled, side by side for the
  governed arm and the baseline, with the degradation test's numbers as
  the "no governance" reference. Each box of the model is clickable: the
  panel gives the model's definition of the node and its edges, what the
  record's reading placed there for each arm, and the evidence from the
  result files that bears on it (the gaps for an upstream defect, the
  arms' assumptions for an unresolved decision, the oracle's results for
  the code, the invalidated assertions for drift).

Below the pictures: the evidence bundle the governed arm received, the
generated code of every run, the oracle's verdict per acceptance scenario
and per run, and the questions and assumptions each run returned.

**The store itself.** A link opens Neo4j Browser on the running database
(user `neo4j`, the password you set), and a box of saved queries lets you
ask it directly: the three-valued answer (asserted, documented absent,
unknown), the chain from a changed fragment to the code built on it, the
contradiction pairs, the gap census. The free edition of Neo4j serves one
database, so the store holds the scenario loaded last; the header says
which.

**The projection.** The store card has a *Project the register* button:
it loads the register's nodes, links, types, exception and export
documents into the running Neo4j, in a namespace of their own (every
node labelled `Register` plus one of `RegNode`, `RegLink`, `RegType`,
`RegException`, `RegDocument`, `RegExternal`; every relationship
`REG_<NAME>`), stamped with the tag, the commit, the export date and
the digest of the TOML file each came from. It is derived, never the
record: a deterministic or arms run wipes the whole store, so the
projection vanishes with it and the chip says *register not projected*
until you load it again. Eight saved Cypher queries read it: which tag
is projected, the impact walk from the register's default start as rows
and as paths (the walk `tools/impact.py` makes, which the impact panel
also carries for the id you typed, with a copy button), coverage rule C1
with the exception joined, and the links that cite a kit document joined
to the harness's own `Artefact` by path, the one query that crosses the
two namespaces and the reason to share one database. Three more go where
the walk does not: what rests on a capability, what touches an
information node, and from an application or module to the documents its
approved links cite, their assertions and the code derived from them
(the adopter's guide, [`docs/guide.md`](../docs/guide.md), section 8,
explains each). The impact panel offers the register's two walks,
*dependants* (what rests on a node) and *realisers* (what implements a
capability), each with or without *children*, the walk also started from
every approved descendant by parent (`tools/impact.py --walk`,
`--children`); three saved queries carry the other three: the walk with
children, the realiser walk, and the realiser walk with children. Every saved query
carries a marker, *runs now* or *needs S6 loaded deterministically*,
*needs S4 loaded*, *needs the register projected*: the store holds one
scenario at a time, so a query run against the wrong state gets Neo4j's
"label not in the database" warnings and no rows, which is correct and
not a fault.

**The impact panel's Browser links.** Beside each form on the impact
panel, next to its copy button, a link opens Neo4j Browser connected to
the store (the `?connectURL=` the *Open Neo4j Browser* link carries) and
showing a guide the demo serves for that form, through the Browser's own
`?cmd=play&arg=<the guide's URL>`. A guide is a small HTML article the
Browser fetches from this page's address and shows in a frame; its query
block is marked runnable, so one click puts the query in the editor and
nothing runs until you press play. The Browser manual also documents
`?cmd=edit&arg=` to pre-fill the editor from a link, but Browser 5.26.0
sends that content before the editor listens, so the editor opened empty
in a scripted test; the guide route does not race, because the click
comes after the editor exists. A run wipes the projection first, so
project the register again before you press play, or the Browser warns
that the `RegNode` label is not in the database and returns no rows. The
Browser fetches the guide from its own origin, so the guide route answers
with the CORS headers that one route alone carries, and the Browser loads
guides only from hosts its allowlist names: `localhost` out of the box,
which is where you reach the demo on your own machine, and the compose
file adds `KG_DEMO_HOST` for an instance reached by address. The Browser
applies the server's allowlist once it is connected, so on such an
instance connect first; a frame that opened before that says *No guide by
that name* and runs again from its own ↻. The stack job proves the chain
short of the click: for every node of the register it follows each link
to its guide, as the Browser would, checks the block against the listed
query and runs it through the store, where the rows must be the walk's
edges and the paths the same relationships
(`demo/tools/check_impact_cypher.py`).

**The register.** The last entry of the Scenarios list is the IEAM
register, a separate public repository
([fdurieux/ieam-register](https://github.com/fdurieux/ieam-register))
that keeps the identities, typed relationships and approvals of an
organisation's architecture; its public content is the same CargoQuote
kit the scenarios use. Its card gives the commit the demo
carries (`register/SOURCE.md` says which, written by
`tools/vendor_register.py` from a checkout at the tag), the counts and the register's
own coverage figures; *Open* replaces the scenario report with the
register in the wide column: its exception and mapping matrix,
the nodes by taxonomy (clicking one opens a panel with its state, owner,
approval, source of record and the links in and out), the relationship
types with their ARIS and Archi status, and an *Impact* box that answers
the IEAM's own question: type a node id (the QuoteAPI module is the
default) and the register's walk shows every link it follows to the
processes, products and journey steps retiring that node would touch,
with each link's state, owner and evidence, and whether the walk
followed it. It starts from any kind something rests on (the register's
decision 0010): from an application to its processes, from a process to
its products, capabilities and journey steps, from a capability to the
products that require it, from an information entity to the processes and
applications that use it, from a product to its journeys and processes.
The walk follows approved links only (the register's
decision 0007): an edge whose link is not approved, or whose far node is
deprecated or retired, is listed as withdrawn and not followed, so only
what lies behind approved links counts as reached. It does not climb a
node's parent, and it says so when it reaches no product. Beside each
reached node it names the owning unit, the unit the node's owner field
names (an approved owns link naming another unit is said beside it; the
walk never follows one), and a *Who to inform* list groups what was
reached by unit. Below the walk, when the store holds the register's
projection and a loaded scenario, it lists the assertions the typed node's
approved links cite, at the grain of the cited anchor, across every
version, with the derived code that used each (the port's
`register_node_statements`); otherwise it says what the store lacks. A link runs the checker at today's date instead of the pinned
one, so you can see an exception expire. Clicking a scenario brings the
report back. Nothing on the page is written back to the register.

**One register per organisation.** A register belongs to an organisation
and holds every subject of it: each body of artefacts the stack loads is a
source of record in the register, with its own dated exports, and its nodes
sit beside the others' under ids minted across the whole register. A subject
joins the register through its own `register_map.toml`, which names the
nodes its keys concern, and through the export manifest it cites. The page
reads one register, the one `KG_REGISTER` names: `register/` in this
folder by default, the public register vendored at a tag. An organisation's
own instance mounts its register checkout read-only with
`docker-compose.instance.yml` (the comment at its top is the command); the
entry then says *this instance* instead of the public repository, the
checker runs at today's date, since a checkout has no pinned date, and no
digest is checked, since there is no `SOURCE.md` to check against.

To see what a register update withdrew, keep the register as it was before
the update beside it, for example a copy at `register-previous/` in the
instance folder, and set `KG_REGISTER_PREVIOUS` to it
(`KG_REGISTER_PREVIOUS=/instance/register-previous` with the overlay). The
Register view then lists the nodes the update deprecated or retired, the
links it withdrew, each with its reason, and the subject's keys that rest on
them, the same list the gate prints with `--register-previous`. The page reads
the setting once, at start, and never writes to either register. Without it,
the view says it shows the current register only; a path that is not there
is shown on the page, not as an error.

**Switching subject.** A *subject* is one kit with its documents,
scenarios and record: the CargoQuote demo and J-F's data load are the two
public ones. The **subject** drop-down at the top of the page lists every
subject the stack serves and switches the page to the one you pick; the
server keeps running. The page then shows that subject's scenarios, its
record, its runs and its own Arms call choice, which your browser
remembers per subject. The address carries the choice as
`?subject=jef_data_load`, so a link opens on the same subject.

In plain English: one stack, both subjects, one menu to move between
them. Which subjects are listed is configuration: `KG_SUBJECTS` names a
folder of subjects (by default the repository's `subjects/` folder) and
`KG_SUBJECT` the one the page opens on. A subject marked
`listed = false` in its manifest, such as the `minimal` test fixture, is
left out. An organisation's own instance, started with
`docker-compose.instance.yml`, lists only the subjects in its own
`subjects/` folder. How such an instance is laid out (its register, its
documents sorted by kind, its subjects and its own record), how to check
one, and how to build a public example to try first are in
[`instance/README.md`](../instance/README.md).

There is still one store. It holds the scenario loaded last, of whichever
subject loaded it, and the store chip names that scenario. Loading a J-F
scenario replaces a CargoQuote one, and the other way round.

**Two subjects side by side.** To keep both pages open at once, each with
its own store, start a second stack beside the first: give it its own
project name with `-p`, its own three ports, and the address your browser
reaches its Neo4j Browser by. With the default stack already running on
8080, 7474 and 7687, paste:

```bash
cd "$HOME/knowgov/demo" && KG_SUBJECT=/repo/subjects/jef_data_load KG_PORT_APP=8081 KG_PORT_BROWSER=7475 KG_PORT_BOLT=7688 KG_BROWSER_URL=http://localhost:7475 docker compose -p knowgov-jef up -d --build --wait && open http://localhost:8081
```

In plain English: the first three variables pick the subject the page
opens on and move the three ports by one so nothing collides; the fourth
tells the page where its Browser links should point; `-p knowgov-jef`
names the second stack so Docker keeps its containers and its database
apart from the first. The J-F page then opens on port 8081, its Browser
on 7475, and the default stack is untouched. Stop the second stack alone
with `docker compose -p knowgov-jef down`. Both stacks write their runs
into this checkout's `runs/` folder, each run under its subject's folder
and its own dated name.

## What Neo4j holds, who writes it and who reads it

The store is a graph: things as nodes, relationships between them as
edges. Written from the harness code and the record, for a reader who
knows software but none of this project's shorthand.

### What Neo4j holds

For one loaded scenario the store holds these kinds of things.

- **Documents and their versions.** Each input file of the CargoQuote kit
  (requirements, decision tables, BPMN process, DMN table, diagrams,
  Gherkin scenarios, OpenAPI file, link set) is a document node named by
  its path, with one version node per ingestion carrying the whole file's
  digest (a fingerprint of its bytes) and a pointer to the current version.
- **Fragments.** A version is cut into pieces (a table row, a note, a
  process step, a scenario), each stored with where it sits in the file,
  its own digest, and a copy of its text so evidence can be quoted later.
- **Entities.** The things the kit talks about (a decision-table row, a
  pricing step, a requirement, the API), each with a declared identifier.
- **Assertions.** One statement each: an entity, a property, a value (for
  example, the surcharge of pricing step P2 is 316.00). Each carries a
  *basis* (how it came to exist: authored by a human, extracted by a
  deterministic parser, or inferred by a model) and a *status* (where it
  is in its lifecycle: proposed, validated, verified, approved, disputed,
  invalidated), and points at the fragment that supports it.
- **Provenance.** The activity that produced each assertion (an extraction
  run, with a timestamp) and the agent behind it: the harness as a tool,
  the maintainer as a human, or the architecture assistant as a model.
- **Verification records.** Each says that one assertion was checked, by
  which method (running the kit's test suite, with the digest of the code
  it ran against, or a dated human review), with a scope and, once a later
  change ends it, a valid-until marker.
- **Approvals.** The maintainer's recorded acceptance of a verified
  assertion, naming the written record it rests on.
- **Gaps.** Things found wanting: knowledge declared missing in the
  documents, vague wording, a contradiction, or an assertion nobody
  verified.
- **Conflict edges** joining two assertions that give different values for
  the same property.
- **Derived outputs.** The identity and digest of a piece of generated
  code, with edges to every assertion it used, and a flag that turns on if
  any of those is later invalidated.

What is not there: the documents' content stays in git, and the model's
prompts, replies and generated code land in result files on disk. The
store keeps fragment copies for quoting and the digests that prove which
bytes they were; it is authoritative for status, provenance and links,
never for content.

### Who writes, and when

Only the harness writes, and always in the same order for each scenario.
It first deletes everything in the store. It then applies constraints
(uniqueness of identifiers; six are accepted, and three the free edition
cannot enforce are refused, which is itself a recorded measurement). It
loads the kit: documents, versions, fragments, entities, and every
assertion at status *proposed*, each tied to its extraction activity and
agent. It loads verifications and approvals, matching the kit's test
scenarios to the statements they exercise and the maintainer's dated
review to the rest, which moves matched assertions to *verified* and then
*approved*. Scenario S5 also adds one model-proposed assertion, attributed
to the model and linked to the open decision it claims to fill. Then the
seven rules run: one checks the graph's structure and only reports; the
others promote agreeing statements from different documents to
*validated*, mark contradicting pairs *disputed* and add conflict gaps,
and raise gaps for vague wording, for declared or undetectable missing
knowledge, and for unverified statements.

S6 has a second stage. The generated code from S1 is registered as a
derived output pointing at its assertions (the demo's runner copies the
record's S1 output into the run folder for S6 in both modes, and the
harness reads it in both modes, so a deterministic S6 has the same
object to invalidate as the record's full run; the record's own
deterministic-only run, `d3check/S6`, predates that and has none; the page
reads a run that registered the derived output against the scored record,
`results/S6`, with `valid_until` set aside as the timestamps are, since that
record holds the null a since-fixed loader defect wrote there, see
`scored_record_volatile` in the subject's `scenarios.toml`). The changed decision table is
re-ingested as version two; unchanged fragments are recognised by digest
and reused, so only the changed rows produce new assertions. The
staleness rule then invalidates every older assertion whose supporting
fragment changed, ends its verifications and flags the derived code
suspect. Finally a re-verification and re-approval are recorded for the
three new statements, and the other new assertions are re-verified
against the known-good values.

The model arms never write to the store; their output goes to files.

### Who reads, and what comes out

The gate reads for the coding task. For each of its 36 required pieces of
knowledge (such as the weight bounds, each screening row's behaviour, the
pricing steps, the response vocabulary) it fetches the live assertions
with their quoted fragment text, verifications, approvals, gaps and
originating agent, plus any declared gap on that key. It computes a level
per key (the weakest status among its assertions, or *absent* if there is
none, or *declared gap*), flags for ambiguity or model-inferred basis, and
a verdict: BLOCKED if any key is absent, a declared gap, disputed or
invalidated, or if more than a quarter are below verified; QUALIFIED if
some are below verified or flagged; otherwise PROCEED. It also reads the
conflict gaps, the invalidated assertions with their ended verifications
and successors, and suspect derived outputs. All of it is rendered as a
text bundle: verdict, policy, then key by key. The governed arm receives
that bundle; the baseline arm receives the documents themselves and never
sees the store.

The demo reads a small census: which scenario is loaded, assertions by
status, node and edge counts. Its saved queries, pasted into Neo4j
Browser, answer: which scenario is loaded; the three-valued answer; the
gate's view of one key; the chain from a changed fragment to invalidated
assertions, ended verifications, successors and the derived code; the
contradiction pairs; the gap census; the status census.

The three-valued answer is the thing a document search cannot give:
*asserted* (a value is stated), *documented absent* (every statement says
there is none), or *unknown* (no statement exists at all). A search
returning nothing cannot tell the last two apart.

### What the store adds that files alone cannot

Status and provenance become data you can query, not something a reader
infers from prose. A change to one fragment can be followed as a
traversal: fragment to the statements it supports, to their
verifications, to the code built on them, giving a deterministic list of
what must be re-checked. Two documents stating different values become an
explicit disputed pair rather than a discrepancy someone might notice.
The free Community edition serves one database, so the store holds one
scenario at a time, the demo runs one load at a time, and the header says
which scenario is loaded.

### What the store does not do

The governance is application logic: the seven rules and the gate are
Python issuing graph queries, and nothing in Neo4j would promote, block or
invalidate on its own. The store supplies storage, uniqueness of
identifiers and traversal; it cannot even require that every assertion
carries a status on this edition, so that check too falls to the
application.

## The three modes, and what each costs

| mode | what happens | needs | time | cost |
|---|---|---|---|---|
| **Replay** | shows the committed results of that scenario | nothing | instant | none |
| **Deterministic** | re-runs the loading, the rules and the gate (measures D1 to D6) against the demo's own Neo4j, then shows the fresh numbers next to the record's | the database container (started with the app) | about five seconds | none; no network |
| **Arms** | re-runs the two assistants once each (`--n 1`; the record used five runs) against the freshly loaded store, grades them with the kit's oracle, shows the result | an OpenAI API key in `OPENAI_API_KEY` | one to two minutes | two model calls of a few thousand tokens each, on your provider's bill; the page shows the tokens |

The Arms button stays greyed out until the key is set. A re-run of either
kind writes into a dated folder, `runs/<subject>/<date-time>/`,
and never into the vendored record under `subjects/cargo_quote/`, which is pumllint's.
The folder describes itself in `run.json`, written when the run starts and
again when it ends: the scenario, the mode, the model row, the as-of date,
who asked (`page`, or `mcp` for a run started through MCP), the start and
end, the status and the exit code. It never holds a key, a token or the
run's environment; `harness/schemas/run.schema.json` pins its shape. A
folder from before it has none, and the page reads it as before.
The report view lets you switch between the record and any demo run.

### The three modes, step by step

The three buttons on a scenario card differ in **how much of the pipeline
runs again**: nothing, the data half, or all of it. An *arm* is the
experiment's word for one side of a comparison, as in a clinical trial:
the governed arm (G) is the assistant that received the gate's bundle,
the baseline arm (B) the one that received the documents only.

**Replay runs nothing and shows the record.**

1. You click a scenario card.
2. The web server opens the committed result files of that scenario
   under the vendored record, `subjects/cargo_quote/kg_experiment/results/`.
3. It renders them as the report view: the plain-English block, the
   pipeline picture, the systemic model, the bundle, the generated code
   and the oracle's grades.

Nothing is computed, the store is not touched, no network is used. It is
instant and free, which is why the demo works offline from the first
start. Replay is the "what happened" view.

**Deterministic re-runs the data half, with no model.**

The server starts the harness (`harness/run.py --deterministic`) for
that one scenario. The harness then does, in order:

1. Wipes the demo's store completely; the free edition holds one
   scenario at a time.
2. Applies the uniqueness constraints and records which ones the free
   edition refuses (measure D1).
3. Loads the kit into the store: documents, versions, fragments,
   entities, and every assertion at status *proposed*.
4. Loads the verifications and approvals, which move the matched
   assertions to *verified* and then *approved*.
5. Runs the seven rules: agreeing assertions are promoted, contradicting
   pairs are marked *disputed*, and gaps are raised for vague, missing
   or unverified knowledge.
6. Takes the census of the store (D2), runs the shape checks (D4),
   computes the three-valued answer for three keys (D5), and runs the
   gate for its verdict (D6). For S6 it also runs the second stage: the
   changed decision table is re-ingested and the stale assertions are
   invalidated (D3).
7. Writes the fresh numbers into a dated folder under
   `runs/`, never into the record, and the page shows them
   beside the record's.

*Deterministic* means the same inputs always give the same output,
because every step is plain code and store queries; no model is called.
It needs the database container, takes about five seconds and costs
nothing. Deterministic is the "prove the store and the gate still behave
as recorded" view.

**Arms re-runs everything, the two assistants included.**

The server starts the harness with `--n 1` instead of `--deterministic`.
The harness then:

1. Does every step of the Deterministic mode first, so the store is
   freshly loaded and the verdict is fresh.
2. Builds arm B's prompt: the task plus the kit's documents themselves.
3. Builds arm G's prompt: the task plus the gate's bundle, that is the
   verdict, the policy and the 36 keys one by one with their evidence.
4. Calls the model once per arm. The record used five calls per arm;
   the demo uses one to keep the cost down.
5. Grades each reply with the oracle: the kit's eleven acceptance
   scenarios run against the code the arm wrote. It also records the
   arm's decision (generate, generate with assumptions, or abstain) and
   whether the arm flagged the planted problem.
6. Writes the run into a dated folder under `runs/`, with
   the model that answered named on every run.

This mode needs the OpenAI key in the environment; the button stays
greyed out without it. It takes one to two minutes and costs a few
cents. A run answered by a model other than the record's is marked in
red as a deviation, because its numbers are no longer comparable with
the record's (see the next section).

| mode | what runs again | needs | time |
|---|---|---|---|
| Replay | nothing; the committed files are read | nothing | instant |
| Deterministic | load, rules, gate | the Neo4j container | about five seconds |
| Arms | all of the above, then one call per arm and the oracle's grading | the OpenAI key | one to two minutes |

## Which model the Arms mode calls

**The models table, first.** The *Arms call* box at the top of the
scenario list has two drop-downs: a **model** and an **effort**. The
model list comes from a table you control, `demo/models.toml` (or the
file `KG_MODELS` names). Each row says who serves the model, the
endpoint's address, the model's name, which efforts it accepts, and the
*name* of the environment variable that holds its key. A row never holds
the key itself and never a price: a key in a file ends up in a
repository, a backup or a screenshot, and a price goes stale.

```toml
[[row]]
id = "openai-gpt-5.5"
label = "OpenAI gpt-5.5"
provider = "OpenAI"
base_url = "https://api.openai.com/v1"
model = "gpt-5.5"
efforts = ["", "low", "medium", "high", "xhigh"]
key_var = "OPENAI_API_KEY"
arms = ["reply", "agent"]
```

In plain English: this row offers OpenAI's gpt-5.5, at the API's default
effort (the empty string) or one of four named efforts, using the key
you exported as `OPENAI_API_KEY`, for both kinds of arm. The page lists
every row. A row whose key variable is empty stays in the list, greyed,
with "set OPENAI_API_KEY" beside it, and the server refuses it too. The
page sends only the row's id and the effort; the server looks up the
address and the key variable itself, so nothing typed in a browser can
point a run somewhere else. The header chip says how many rows are
available, and names the variables to set when none is.

**Each key is checked before you pick it.** When the page starts, it
asks every row's endpoint for its list of models, first with a placeholder
that is no key, then with your key. Those requests cost no tokens and send
no prompt and no document. Each row then shows one of four marks:

- *key accepted*: the endpoint refused the placeholder and answered your
  key with its list;
- *key refused*: the endpoint answered 401 or 403. The row is greyed with
  the status and the variable to fix, and a run on it is refused at once,
  before any call is made;
- *endpoint unreachable*: no answer. The row stays usable, since a run
  may still get through later;
- *key unchecked*: no key is set, the check is off, the endpoint does
  not serve a list (404, for instance), or it lists its models to anyone,
  placeholder included, as OpenRouter and Ollama do. None of these says
  anything about the key, and an open list is never sent your key.

Rows that share an endpoint and a key are checked once. After you fix a
key and restart, or to ask again, press *re-check keys* under the
drop-down. Like a run, it needs the page's token when one is set. The
page keeps only the mark, the HTTP status and the time. It never keeps,
logs or shows the key, nor the provider's error text, which for OpenAI
quotes part of the key. Set `KG_KEY_CHECK=off` for an endpoint that
should receive nothing but runs.

A row behind a gateway is marked `gateway = true` in the table, as the
Claude row is. There, the list proves only the gateway's own key
(`LITELLM_MASTER_KEY`), and the row reads *gateway key accepted,
upstream unchecked*. The Anthropic key behind the gateway is first tested
by a run: LiteLLM's own health check would send a real, paid request.

Two rows are not in the file. The **record's row** comes first: the
model and effort the record's arms ran at, so a run on it is
like-for-like. On a subject whose record ran no arm, it stays listed and
greyed with "the record ran no arm". The **instance's row** appears when
you set the three older variables, `KG_MODEL_BASE_URL`,
`KG_MODEL_API_KEY_VAR` and `KG_ARMS_MODEL`, to something other than the
defaults: a quick way to try one endpoint without editing the table.

To add a provider, add a row and pass its key variable through to the
app service in `docker-compose.yml` (it passes `OPENAI_API_KEY`,
`KG_MODEL_API_KEY` and `GEMINI_API_KEY` already). The file has a Gemini
row, Google's gemini-3.8-flash on Google's own OpenAI-compatible
endpoint: export your Google AI Studio key as `GEMINI_API_KEY` and the
row becomes available, for both kinds of arm, at the API's default
effort or low, medium or high. A Claude row needs a gateway in front
of Anthropic; see *A Claude row, through a gateway* below. A
private model behind a gateway (vLLM, Ollama, LiteLLM, an enterprise
proxy) is a row like any other, its `base_url` the gateway.

**A Claude row, through a gateway.** Anthropic's own OpenAI-compatible
endpoint ignores the effort setting and refuses the JSON-only replies the
one-reply arm asks for, so the Claude row reaches Anthropic through a
small gateway, LiteLLM, that the stack starts only when you ask for it.
The gateway translates the effort into Anthropic's thinking settings,
marks each prompt so Anthropic caches it, and records the real model
name, `claude-sonnet-5-5`, on every run. Two keys are involved, and
neither is ever written to a file:

```bash
export KG_ANTHROPIC_KEY=your-anthropic-api-key
```

```bash
export LITELLM_MASTER_KEY=sk-any-long-random-string-you-choose
```

```bash
cd "$HOME/knowgov/demo" && docker compose --profile claude up -d --build --wait && open http://localhost:8080
```

In plain English: the first variable is your Anthropic key, from the
Claude Console; only the gateway sees it. Do not use the name
`ANTHROPIC_API_KEY`, which Claude Code itself reads. The second is a key
you make up; the page uses it to talk to the gateway, and the gateway
refuses anyone without it. `--profile claude` starts the gateway beside
the app; without it the stack runs exactly as before and the Claude row
stays greyed with "set LITELLM_MASTER_KEY". Caching matters for the agent
arm: each turn resends the whole conversation, and with the cache mark
Anthropic charges the repeated part at its lower cached rate.

Whatever the row, a model, a host or an effort other than the record's
is a deviation: the page marks every such run in red, names the model
and the effort, and the numbers are not comparable with the record's.

The record's two arms were answered by `gpt-5.1-2025-11-13`, and the
record's row calls that model, so an Arms run on it is like-for-like
with the record. That model is a year old, and on a new OpenAI
organisation its rate limit can be as low as 10,000 tokens per minute,
while the governed arm's prompt alone is about 15,000 tokens: the call
is then refused with a 429 "request too large" before it runs, and the
page says so in red. Two ways out:

- **Raise the limit** on the OpenAI side (a higher usage tier, or a
  limit-increase request on your organisation's Limits page) and keep
  the record's row. Results stay comparable with the record.
- **Pick another row** in the *Arms call* box. The gate, the evidence
  bundle and the oracle are unchanged, but the arms' answers are another
  model's: the page marks every such run in red as a deviation, and the
  numbers are not comparable with the record's.

**The agent arm.** A subject whose manifest says `[arms] kind = "agent"`
(the J-F data load does) runs each arm as a loop of turns instead of one
reply: the model has four tools, read a document, write a file into the
run's sandbox, run the scenario's own feature files over the sandbox, and
finish with its decision. Model-written code runs only inside that
sandbox, a folder under the run's directory, and only through the suite
command the subject's oracle script names; nothing else executes it. Each
run is bounded by a ceiling in calls, tokens and seconds, instance
configuration read from `KG_AGENT_MAX_CALLS`, `KG_AGENT_MAX_TOKENS` and
`KG_AGENT_MAX_SECONDS` (defaults 30, 1,500,000 and 1500; tokens are the
prompt and reply tokens the API reports, added up); a run that reaches it
ends with decision abstain and the reason. Every turn and tool call is
written to a trace file beside the run, and the Generate box shows it.
The pristine suite, the oracle, grades the sandbox afterwards as it
grades a reply. With `context = "pull"` in the manifest the first message
is an index, not the whole bundle or every document: the governed arm reads
a key's knowledge through `read_knowledge(key)` and the baseline arm a
document through `read_document(path)`, every read logged, so the gate
box shows which keys below verified a run read and which it marked as
assumptions, and a turn resends far less. The page shows prompt, cached
and reply tokens per run and per turn, as the endpoint reports them.

**Tokens a thinking model spends.** A model that reasons before it
answers spends tokens on that thinking, and endpoints report them in
different places. Some count them in the reply tokens. Google's endpoint
counts them only in its total. The page therefore shows a third column,
*other tokens*: what the endpoint's total holds beyond the prompt and the
reply. The token ceilings count the total, so a run of a thinking model
stops where its bill says it should. One case cannot be seen from the
usage at all: a gateway may rebuild the total and drop the thinking, as
LiteLLM did in front of Gemini when we measured it. A model row that
declares `thinking_uncounted = true` makes the page say so beside every
run on it, *these token counts are low*, rather than show a number that
only looks complete.

A subject whose record ran no arm (the J-F data load: its record graded
whole rebuilds, so its `record_model` is empty) has no like-for-like
choice. The record's row is then greyed, the first available row is
picked, and the report says the record has no arm result to compare
with; nothing is marked as a deviation, since there is nothing to
deviate from.

The choice is remembered by your browser. Either way a re-run writes
into `runs/`, never into the record. The harness prints no cost: it
counts tokens (and stops the one-reply arms at `KG_ARMS_MAX_TOKENS` per
run, default 6,000,000), and your provider's bill is the record of what a
run cost, since any list price written here would go stale.

## The gate as a command

The page shows the gate's verdict. A build needs the same answer as a
command that stops it. `harness/gate_cli.py` loads a scenario, resolves the
task's required knowledge through the same gate the arms read, and exits
with a number a pipeline can act on:

```bash
docker compose exec -T app python harness/gate_cli.py --scenario S2
```

In plain English: the command answers one question. Is the knowledge this
task needs good enough to build on? It lists what is missing or weak, key
by key, on a five-step severity ladder (blocker, critical, major, minor,
info), and then exits:

- **0**: nothing at or above the threshold. By default the threshold is
  *blocker*, so PROCEED and QUALIFIED pass and BLOCKED fails.
- **1**: something at or above it. `--fail-on major` also fails a
  QUALIFIED answer that still has keys below verified; `--fail-on minor`
  also fails on a flagged key.
- **2**: the gate could not run: no such subject, scenario or task, or no
  store to answer.

A *key* below verified is a major finding: an assistant may use it only
as a stated assumption. A key that is absent, a declared gap, disputed or
invalidated is a blocker.

Two findings are not about a key's level. Code registered as derived
from statements that a later change invalidated is *suspect*: a blocker,
whatever the verdict, since it may not be reused as it is. An invalidated
statement on a required key is major while no verified or approved
statement replaces it, and info once one does: the record of the change.
After S6's change and the owner's re-verification the verdict is PROCEED,
and the command still exits 1 on `derived:S1:G:run1`.

**What a later version re-reads.** Stage 2 reads the whole later set of
documents, not only the changed file, so a symbol a diagram reads from the
decision table resolves as it would at a fresh load. Only a document whose
bytes changed gets a new version. A statement whose value or evidence
changed gets a v2 successor, and the one it replaces is invalidated, also
when only a symbol it reads changed. The rules then run across both
versions: a v2 statement that contradicts another document reads
*disputed*, as a fresh load of the same documents would. A review's acts
stand: a declared gap a review closed stays closed, and a declared gap whose
declaring statement the change invalidated is withdrawn.
`tools/check_stage2_reload.py` holds a stage-2 gate equal to a fresh load of
the later documents, plus the stale statements and suspect outputs the
change leaves (task-0197).

**A later version.** `--stage 2` brings in a scenario's changed artefact
after the first stage, as the record's stage 2 does: S6's decision table
as v2. Four statements are invalidated, and the gate is BLOCKED until the
owner re-verifies. `--stage 2 --reverify` adds that re-verification, and
the command exits 1 on the suspect derived output. The report names the
version loaded (`version`) and the change (`change`). CI runs all three
with `tools/check_gate_after_change.py` (task-0049):

```bash
docker compose exec -T app python harness/gate_cli.py --scenario S6 --stage 2
```

**A baseline instead of a threshold.** `--baseline record` compares the
answer with the subject's record for the same scenario and exits 1 only
on a regression: a worse verdict, or a key at a lower level than the
record's, or a derived output suspect that the record did not hold
suspect. S2 is BLOCKED in the record too, so
`--scenario S2 --baseline record` exits 0, and the report still lists the
blockers. `--baseline <file>` compares with an earlier report of the
command, written with `-o <file>`. The command never writes a baseline
itself: keeping one is your decision, made by committing the file.

**As of a date.** A review falls due after the review months of the kind
its key concerns, from the register's `metamodel/lifecycle.toml`
(decision-0005); past that, the statement reads validated and the report
lists a `lapsed` finding (major). `--as-of` is the date this is read on:
today by default, `record` for the subject's pinned record date, or
`YYYY-MM-DD`. `--scenario S1 --as-of 2027-08-07` is BLOCKED: CargoQuote's
ten review-only keys, reviewed on 2026-08-06, have lapsed. The
deterministic run and the comparator always read as of the record date.

The page shows the same (task-0076). The gate box and the gate panel
name the as-of date the run read; the panel's *Review currency* section
lists every lapsed review: the assertion, its key, the day its review
was current until, the day it lapsed, and the review months of the
register kind its key takes them from. A run reads as of the record
date unless the menu's *Reviews as of* date names another
(`POST /api/run` with `"as_of": "YYYY-MM-DD"`, which passes `--as-of`
to `harness/run.py`); such a run is not measured against the record.
On S6 the two stage-2 gates, after the change and after re-verification,
show the same in their boxes and panels (task-0086): re-verification
renews only the changed keys' reviews, so as of 2027-09-01 both are
BLOCKED on the same ten lapsed keys.

`-f json` prints the report as data, in the shape
`harness/schemas/gate-report.schema.json` pins; the command checks it
against that schema before printing. The report is at version 2: from
version 1, each finding names its `kind` (key, task, stale,
suspect_derived), the statement or derived output it is about (`ref`)
and what relates to it (`related`); `stale` and `suspect_derived` are
lists of ids, no longer counts; the baseline adds `new_suspect`. A
version-1 report still reads as a baseline.

**Which store it writes.** None, by default. The command loads the
scenario into a private copy in its own memory, answers from it, and
throws it away, so the page and the assistants go on reading the scenario
they were reading. You can run it on a stack anyone is using, and outside
the stack with no database at all. The report's `store` reads `rdflib`
(the private copy's kind) and `published` reads `false`. The copy needs
the harness's Python packages, which the image has; without them the
command says so and exits 2.

`--publish` loads into the stack's store instead, replacing what it holds,
as a run does. Use it only when a later step reads that store: a trace
check, the MCP server, or `--no-load`. The answer is the same either way.
`--no-load` reads the store as the page left it, and refuses when the
store holds another scenario; it cannot be combined with `--publish`.

## A proposal read before approval

A new product often reuses capabilities the register already has, needs
one it lacks, and comes with a customer journey partly copied from an
existing one. Before anyone approves it, `harness/proposal_impact.py`
reads it against the register *as if approved*, without approving it
(task-0130, task-0131, doc-0017). The proposal is a small JSON (or TOML)
file: the new nodes, with provisional ids, their kind, name, parent and
owner; the links that join them to what exists; the register nodes it
reuses, each `as_is` or `changed`; and any exception it asks for.
`tools/fixtures/proposal_contract_quote.json` is doc-0017's worked
example, synthetic: a *Contract freight quote* product that requires
three existing capabilities and a new one, *Check a shipper's credit*,
with a three-step journey whose first step copies the instant quote's.

```bash
docker compose exec -T app python harness/proposal_impact.py tools/fixtures/proposal_contract_quote.json
```

In plain English: the register's own checker and walks read the
proposal, and nothing else decides. The report says:

- **Coverage before and after.** C1 goes from 7 of 8 steps supported to
  8 of 11: the two new steps that nothing supports, *Negotiate the
  terms* and *Accept the contract*, are new gaps. C2 goes from 5 of 5 to
  5 of 6: nothing realises the new capability.
- **Reach before and after.** The walk from *Price a shipment*
  (CAP-0002) now also reaches the new product and its journey; the walk
  from the process *Validate the request* (PROC-0002) reaches the copied
  step too. A reused node marked `changed` is flagged, so its owner sees
  what the change touches.
- **What the new product rests on.** Each capability it requires, with
  the processes and applications that realise it; the new one rests on
  nothing yet.
- **Candidates.** D1, the register ids the proposal names (`authored`).
  D2, an external id such as an ARIS GUID, matched through a node's
  `[source]` or the newest export the connector landed (`authored`).
  D3, the same name as an approved node of the same kind: the copied
  step is "same step as JRN-0002", and that step's support is offered
  (`inferred`). D4, for a step with nothing, the processes realising the
  product's capabilities, listed and none chosen. A forbidden synonym in
  a name (D5) is a placement error. A candidate is only ever `proposed`:
  it closes no gap until the proposal states the link itself.
- **Keys.** Each reused node's knowledge keys, as `register_impact`
  reads them, with their levels when a scenario is loaded. The new
  nodes have none yet: they are listed *unmapped*, never *unknown*.
- **Approvals.** Which unit must approve each new node and link. A link
  that crosses from one owner to another needs both.

Every proposed element is marked `hypothetical`. Nothing is written to
the register, the store or any file, and knowgov mints no ids: the
proposal becomes record only through a pull request on the register.
`-f json` prints the report in the shape
`harness/schemas/proposal-impact.schema.json` pins. An assistant asks the
same through the MCP tool `proposal_impact`, with the proposal in its
call (see `instance/README.md`). Outside the stack, add `KG_STORE=rdflib`,
or `--no-store` to leave the keys without their levels.

### What exists, step by step

The same report reads a journey or a product that is already in the
register, with no proposal (task-0191, doc-0024). Name it with
`--scope`:

```bash
docker compose exec -T app python harness/proposal_impact.py --scope JRN-0001
```

In plain English: you get one slice per step of *Get a freight quote*.
Each slice is the register's own thread walk from the step: the process
behind it, the capability, the application and the data. Each slice also
lists its knowledge keys: the subject's register-map rows on those
nodes, with the total as the denominator. Here *Submit a quote request*
lands 22 of CargoQuote's 36.

With a scenario loaded, each key has its level under the task class and
date you name. The slice then says:
- how many keys are at each level;
- the lowest level;
- which keys are unknown (no statement) or a documented gap;
- which reviews have lapsed;
- which keys sit behind a link the walk does not follow, such as
  *Notify the shipper*, still `proposed`;
- where ownership changes hands along the thread.

These are facts with their denominators, never a score. A product's id
(`--scope PRD-0002`) gives its journeys' steps. An MCP client passes
`scope` instead of, or beside, `proposal`.

To see every step against every scenario at once, run the scenarios
deterministically into a folder, on a scratch store of their own, then
read the folder (task-0192):

```bash
docker compose exec -T -e KG_STORE=rdflib -e KG_RDFLIB_FILE=runs/sweep.ttl app sh -c 'python harness/run.py --deterministic --out runs/sweep && python harness/step_grid.py runs/sweep'
```

In plain English: the `-e` settings point the run at a scratch file
instead of the page's Neo4j, so the sweep loads its scenarios there.

`harness/step_grid.py` prints one row per step and one column per
scenario. Each cell is the step's keys as that scenario's gate report
has them: the lowest level, and how many keys are blocked, stale, lapsed
or unread. `--record` reads the subject's own record instead. The grid
itself reads only the folder's files and never opens a store. `-f json` prints
the shape `harness/schemas/step-grid.schema.json` pins.

## Quick start on a Mac, step by step

Six steps. Each block is ready to paste into Terminal (zsh) as a whole;
the line above each says what it does.

**1. Prerequisites.** Install
[Docker Desktop](https://www.docker.com/products/docker-desktop/) if you
do not have it, start it, and wait until its menu-bar icon says it is
running. `git` comes with macOS (it offers to install the command-line
tools the first time you type it). Then check the engine answers:

```bash
docker info >/dev/null 2>&1 && echo "docker engine running" || echo "docker engine NOT running: start Docker Desktop"
```

**2. Set the OpenAI key, only if you want the Arms mode.** Paste this
with your real key in place of the placeholder. The variable lives in
this Terminal window only; it is never written to disk and never baked
into the image. Skip this step and the Arms buttons simply stay greyed
out; Replay and Deterministic work without it.

An Arms run also needs the *worker*, the sealed container that runs the code
the model writes. It starts only when you add `--profile arms` to the
`docker compose up` command in step 3, and only on Linux with Landlock, a
kernel feature that stops that code writing outside its own folder (kernel
5.13 or later, enabled). Docker Desktop for Mac 4.48.0 has no Landlock, so
there the worker refuses to start and every Arms run is refused; the rest of
the demo works as usual. To run the Arms mode from a Mac, start the stack on a
Linux machine whose kernel has Landlock and open the page through an SSH
tunnel: *The Arms mode on an EC2 instance* under *Start it elsewhere* walks
through the one such machine recorded so far.

The page tells you which case you are in. With a key set and no worker, the
Arms chip reads **arms: no contained worker** and the Arms buttons stay
greyed; hover over either for the reason. To check the worker on your engine
in one command, from `~/knowgov/demo`:

```bash
docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only
```

It prints the worker's attestation and exits 0 when the worker is confined,
3 when it is not. `write_confined: false` in that output means this engine
has no Landlock, so the worker cannot stop model-written code writing outside
its own folder, and every Arms run is refused. Run the Arms mode on a Linux
host instead; Replay and Deterministic need no worker.

Beside the Arms chip, the **worker** chip says where Arms code would run, as
the worker itself reported it: for example **worker: attested · Docker ·
Linux 7.0.0-1014-aws (x86_64) · AWS (from the kernel release)**. The engine,
kernel and machine are what the worker reads inside its container. The cloud
is only a reading of the kernel's name (Ubuntu's cloud kernels end in `-aws`,
`-azure`, `-gcp` or `-oracle`), not a check: nothing asks the cloud provider.
**worker: not attested** means no confined worker is running; hover for the
reason. A script reads the same from `GET /api/scenarios` as `"worker"`.

```bash
export OPENAI_API_KEY=sk-your-real-key-here
```

Optionally choose a database password other than the default. The stack reads
`KG_STORE` too, the store adapter behind the harness's port (`neo4j`, the default, or
`rdflib`: an in-memory graph that needs no database container, no Browser link and no saved
Cypher; the deterministic mode still re-runs and compares), `KG_SUBJECT`: the subject root inside the container, `/repo/subjects/cargo_quote`
unless you set it ([`subjects/README.md`](../subjects/README.md) says what a subject holds),
and `KG_REGISTER`: the register the page reads, `/repo/demo/register` unless an instance
mounts its own (see *One register per organisation* above).

Optionally choose a database password other than the default
`kgpoc2026`:

```bash
export KG_NEO4J_PASSWORD=choose-a-password
```

**What changed in the bind (task-0090).** The stack now publishes the page (8080), Neo4j Browser
(7474) and bolt (7687) on `127.0.0.1` only, so they answer on this machine and nowhere else. On a
laptop nothing changes: `http://localhost:8080` works as before. To reach them from other machines,
set `KG_BIND` to the address to publish on (`0.0.0.0` for every interface, or one of the host's
addresses) and choose a password: with a wider bind the stack refuses to start while the Neo4j
password is the default, and `docker compose logs neo4j` says why. Neo4j takes its password when
its data volume is first created, so if the stack ran before with the default, run
`docker compose down -v` once before starting with the new password.

```bash
export KG_NEO4J_PASSWORD=choose-a-password KG_BIND=0.0.0.0
```

**What changed for runs (task-0096).** On your own machine nothing changes: the run buttons and
"Project the register" work as before, with no token. Once `KG_BIND` publishes the page beyond
this machine, the page refuses to start a run or project the register until you give it a token
of your own, because a run reloads the store and, with a key set, calls the model at your cost.
Choose one and export it with the bind:

```bash
export KG_PAGE_TOKEN=choose-a-long-random-token KG_NEO4J_PASSWORD=choose-a-password KG_BIND=0.0.0.0
```

The page then shows a **Page token** box above the scenarios. Each viewer who may start runs types
the token there once; the browser keeps it for that tab only and sends it with every run and
projection. Viewers without it still read every report, but the Deterministic, Arms and Project
buttons stay greyed with the reason. A script sends it as a header:
`curl -X POST -H "Authorization: Bearer $KG_PAGE_TOKEN" -H 'Content-Type: application/json' -d '{"scenario":"S1","mode":"deterministic"}' http://<host>:8080/api/run`.
Without a token on a wider bind, those requests answer `403` and say to set `KG_PAGE_TOKEN`. A script reads whether
an Arms run may start from `GET /api/scenarios`: `"arms_enabled"` says a model row has its key, and
`"execution": {"ok": true|false, "why": null|"<the reason>"}` says whether model output may run now (no
organisation's instance mounted beside the app, and the worker running and confined); an Arms run
starts only when both hold, and `why` is the refusal that run would get. Each of `"model_rows"`
carries `"key_check"`: `"state"` (`accepted`, `refused`, `unreachable` or `unchecked`), the HTTP
`"status"`, `"checked_at"`, `"scope"` (`gateway` when the listing proves a gateway's own key only) and
`"why"`; a refused row reads `"available": false`. `POST /api/models/check` checks every key again
and answers with the rows. The
token takes effect with an image built from this checkout (`docker compose up --build`) or a
release after 0.2.0. A run or a projection is also refused when it comes from a page on another
web address, so a site open in the same browser cannot start one.

The page's reports have no login: anyone who reaches it reads everything it shows, excerpts
included. So widen the bind only behind a firewall that admits the people who should see it, and,
beyond a network you trust, behind a proxy that serves HTTPS, since the page sends the token in
clear over plain HTTP.

**3. Clone and start the stack.** Paste the whole block at once. It
checks the tools and says what to install if one is missing, clones the
repository into your home folder (or updates it if it is already there),
sets the two variables the stack reads, builds the application image,
pulls the Neo4j image, waits until both containers are healthy, prints
the two addresses, and opens the demo in your browser.

```bash
set -e
command -v git >/dev/null 2>&1 || { echo "git is not installed. Run: xcode-select --install"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"; exit 1; }
docker info >/dev/null 2>&1 || { echo "the docker engine is not running. Start Docker Desktop and wait for it to say it is running, then paste again"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "docker compose is missing. Update Docker Desktop"; exit 1; }
cd "$HOME"
if [ -d knowgov/.git ]; then cd knowgov && git pull --ff-only; else git clone https://github.com/fdurieux/knowgov.git && cd knowgov; fi
export KG_NEO4J_PASSWORD="${KG_NEO4J_PASSWORD:-kgpoc2026}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
cd demo
for p in 8080 7474 7687; do docker ps --filter "publish=$p" --format '{{.Names}}' | grep -q . && { echo "port $p is in use by container $(docker ps --filter "publish=$p" --format '{{.Names}}'): stop that stack first, with docker compose down in its folder, then paste again"; exit 1; }; done
docker compose up -d --build --wait --wait-timeout 300
echo "demo:          http://localhost:8080"
echo "Neo4j Browser: http://localhost:7474  user neo4j, password $KG_NEO4J_PASSWORD"
open http://localhost:8080
```

The first start takes a minute or two (the image build plus the Neo4j
pull). Later starts take seconds. The stack needs ports 8080, 7474 and 7687
free: the block stops with the name of the container holding one, which is
pumllint's demo stack if you ran it before (`docker compose down` in
`~/pumllint/kg_experiment/demo` frees them).

**4. Use it.** In the browser at `http://localhost:8080`:

- the two chips in the header say whether the store is reachable and
  whether the Arms mode is enabled;
- click a scenario card to **Replay** its recorded results;
- click **Deterministic** to re-run D1 to D6 against the container's
  Neo4j (about five seconds); the run's log appears on the left, and the
  view switches to the new demo run when it finishes;
- click **Arms** (needs the key) to re-run both model arms once; one to
  two minutes, a few cents;
- use the **source** dropdown in the report header to switch between the
  record, S6's re-run, and any demo run;
- **Open Neo4j Browser** opens `http://localhost:7474` on the scenario
  loaded last; log in as `neo4j` with your password and paste any saved
  query from the left panel.

Re-runs land in `~/knowgov/runs/<subject>/<date-time>/`,
which git ignores.

**5. Stop it.**

```bash
cd "$HOME/knowgov/demo" && docker compose down
```

Add `-v` to that command to delete the Neo4j data volume as well; the
demo runs stay, because they are in your checkout.

**6. Restart later.** A new Terminal window has forgotten the key, so
export it again first if you want the Arms mode:

```bash
export OPENAI_API_KEY=sk-your-real-key-here
```

```bash
cd "$HOME/knowgov/demo" && git pull --ff-only && docker compose up -d --build --wait && open http://localhost:8080
```

To update from any directory, without changing into the checkout, tell
git and Docker where it is instead (`-C` for git, `--project-directory`
for Docker Compose):

```bash
git -C "$HOME/knowgov" pull --ff-only && docker compose --project-directory "$HOME/knowgov/demo" up -d --build --wait
```

If you do this often, put it in your shell profile once as an alias
(`~/.zshrc` on a Mac) and type `kgdemo` afterwards:

```bash
alias knowgov='git -C "$HOME/knowgov" pull --ff-only && docker compose --project-directory "$HOME/knowgov/demo" up -d --build --wait'
```

Two cautions. Never commit the key or put it in a `.env` file you might
push. And if you ever run this on a server (see the EC2 route below),
`KG_BIND` must widen the bind for you to reach it at all; restrict the firewall to your own
address on ports 8080, 7474 and 7687: the demo page's reports have no login, and 7474 is a live
database console. Set `KG_PAGE_TOKEN` too, or the page refuses runs on a wider bind.

### What the start block does, in plain English

The first four lines check that `git`, `docker` and `docker compose` are
present and that the Docker engine is running; each stops with a message
naming the fix. The port line stops when another container already holds
one of the stack's three ports and names it. The next two lines go to your home folder and clone the
repository, or update it if it is already there. The two `export` lines
set the two variables the stack reads: the database password (the
harness's default if you have not chosen one) and the OpenAI key (kept
empty when you have not exported one, which disables the Arms mode). The
last lines start both containers, wait for their health checks, print the
two addresses, and open the demo.

## Start it elsewhere

**Another laptop, without building.** The compose file names a released
image, `ghcr.io/fdurieux/knowgov:<version>`, pinned by its digest
(task-0092); the repository also publishes every merge as `:latest` and
as the commit's short SHA, which you can name in its place. So the two
ways to start differ: `docker compose up --build` in this directory builds
the checkout you have (main, or whatever you checked out), while a plain
pull with `-f docker-compose.yml` runs the named release. Each release
moves the pin. From the `demo` directory of a checkout:

```bash
docker compose -f docker-compose.yml pull
```

```bash
docker compose -f docker-compose.yml up -d --wait
```

Naming the compose file explicitly skips the development override, which
would otherwise build the image locally. If the pull is refused, the
package is private on GitHub: log in with `docker login ghcr.io` using a
token that can read packages, or ask the repository owner to make the
package public. Demo runs then live in a Docker volume named
`knowgov_demo-runs`; `docker compose down -v` deletes them.

**An EC2 instance.** A `t3.medium` (two vCPUs, 4 GB) is enough: Neo4j is
configured for 1 GB of heap and 512 MB of page cache, the app needs little.
Use an Ubuntu image with Docker installed, clone the repository, and start
the stack as above with `KG_BIND=0.0.0.0`, a `KG_NEO4J_PASSWORD` of your own (the stack refuses
the default on a wider bind), a `KG_PAGE_TOKEN` of your own (without it the page refuses runs on a
wider bind), and `KG_BROWSER_URL=http://<the instance's public address>:7474`
exported so the demo's "Open Neo4j Browser" link and the impact panel's
Browser links point at the instance rather than at your own machine, and
`KG_DEMO_HOST=<the instance's public address>` so the Browser is allowed
to fetch the impact panel's guides from the page. **Restrict the security group to your own
IP address** for ports 8080, 7474 and 7687: the demo page's reports have no
login (only its runs ask for the token), and port 7474 is a live database console protected
only by the password you set. Do not leave the instance reachable from the
internet; stop or terminate it after the session.

**The Arms mode on an EC2 instance.** This is the route to use when your own
machine cannot run the worker, a Mac with Docker Desktop for instance. The
stack keeps its default bind, `127.0.0.1`, so nothing but SSH is open, and you
reach the page through a tunnel. It was recorded on a real machine on
2026-11-06 (task-0162): a `t3.large` (two vCPUs, 8 GiB) on Ubuntu Server
24.04 LTS, x86_64, with Ubuntu's own `docker.io` 29.1.3 and
`docker-compose-v2` 2.40.3, kernel `7.0.0-1014-aws`, where the worker's
self-check came back with every check true. Another image or engine may
differ; the self-check in step 3 is what decides.

1. *Launch.* In the EC2 console, launch an instance from **Ubuntu Server
   24.04 LTS**, 64-bit (x86); the console may offer a newer release first,
   which has not been recorded. Choose `t3.large`, create a key pair and keep
   its `.pem` file on your own machine (`chmod 400` it), raise the root
   volume to 30 GiB gp3 (the default 8 GiB fills with the images, and Neo4j
   then exits at start with an out-of-disk error in its log), and let the security group allow **SSH from My IP
   only**. Open no other port.

2. *Install and clone.* Connect with
   `ssh -i ~/.ssh/<key>.pem ubuntu@<public address>`, then:

   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker ubuntu
   git clone https://github.com/fdurieux/knowgov ~/knowgov
   ```

   Log out and back in, so that `docker` works without `sudo`.

3. *Check the worker can serve.* This needs no key. Every check must read
   `true`, `write_confined` (Landlock) among them; if one does not, the Arms
   mode is refused on this machine, and nothing weakens that.

   ```bash
   cat /sys/kernel/security/lsm    # should list landlock
   cd ~/knowgov/demo && docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only
   ```

4. *Start the stack.* Set only the keys you use. `read -rs` takes each from
   a silent prompt, so it stays in this shell, out of the history and off
   the disk:

   ```bash
   read -rs OPENAI_API_KEY && export OPENAI_API_KEY
   docker compose --profile arms up -d --build --wait
   ```

   For the Claude row, set `KG_ANTHROPIC_KEY` and `LITELLM_MASTER_KEY` the
   same way and add `--profile claude`.

5. *Open the page.* On your own machine, in a terminal you leave open:

   ```bash
   ssh -i ~/.ssh/<key>.pem -N -L 8080:localhost:8080 ubuntu@<public address>
   ```

   and browse to `http://localhost:8080`. Neo4j Browser comes the same way,
   with `-L 7474:localhost:7474 -L 7687:localhost:7687` added.
   The assistants' MCP servers need no tunnel: they start over SSH itself,
   as `instance/README.md` shows under *The MCP servers when the stack runs
   on another machine*.

6. *Stop.* On the instance, `docker compose --profile claude --profile arms
   down`, then stop the instance in the console; a stopped instance costs
   only its disk.

**Looking after the stack on the instance.** Every command below runs in
`~/knowgov/demo` on the instance and names the same profiles you started
with, so that it reaches the worker and the gateway too. Shorten the typing
once per shell with `export COMPOSE_PROFILES=claude,arms`; then a plain
`docker compose …` means both.

- *See what runs.* `docker compose ps` lists each service and its health:
  `app`, `neo4j` and `worker` read *healthy*; `litellm` has no health check
  and reads *Up*. A service that keeps restarting or is missing:
  `docker compose logs --tail 40 <service>`.
- *Check the worker again.* `docker compose exec worker python
  harness/worker.py --attest-only` prints the running worker's self-check;
  every check must read `true`.
- *After you reconnect.* A new SSH session has forgotten the keys. The
  running containers keep theirs, so the page goes on working; set the
  keys again (`read -rs …`, as in step 4) only before a command that
  creates containers, such as `up` after a `down`, or they start without
  them.
- *Change a key.* Containers read the keys when they are created, so set
  the new value and recreate the one that uses it: `docker compose up -d
  --force-recreate --wait app` for `OPENAI_API_KEY` or `GEMINI_API_KEY`,
  `litellm` for `KG_ANTHROPIC_KEY` or `LITELLM_MASTER_KEY` (a new master
  key needs `app` recreated too). Before a paid run, the OpenAI key can be
  tried for nothing: `curl -s -o /dev/null -w '%{http_code}\n'
  https://api.openai.com/v1/models -H "Authorization: Bearer
  $OPENAI_API_KEY"` answers 200 when OpenAI accepts it and 401 when not.
  OpenAI's dashboard shows a secret key in full only once, when it is
  created; its list shows a name and a shortened form, which do not work as
  the key.
- *Update to the latest knowgov.* `git -C ~/knowgov pull --ff-only`, then
  `docker compose up -d --build --wait`, with the keys set. Run the
  self-check again after an update.
- *Stop and start again.* `docker compose down` removes the containers and
  keeps the Neo4j data and the demo runs; `up -d --wait` brings them back.
  `down -v` deletes those volumes as well. The stack has no restart policy,
  so after the instance is stopped and started, it is down until you run
  `up` again.
- *Disk.* `df -h /` shows what is left; `docker system df` what the images
  and the build cache take; `docker builder prune` frees the build cache.
  When the disk fills, Neo4j exits at start with an out-of-disk error in
  its log: grow the volume in the console (Storage, the volume, *Modify
  volume*), then `sudo growpart /dev/nvme0n1 1 && sudo resize2fs
  /dev/nvme0n1p1` (check the disk's name with `lsblk` first), remove the
  half-made store with `docker compose down && docker volume rm
  knowgov_neo4j-data`, and `up` again.
- *The instance's address.* A stopped and started instance gets a new
  public address: take it from the console for `ssh` and the tunnel. When
  SSH hangs, your own address has probably changed (another network, a
  VPN): set the security group's SSH rule to *My IP* again.
- *The tunnel on your own machine.* `bind [127.0.0.1]:8080: Address already
  in use` means something on your machine holds port 8080, often your local
  stack: `lsof -nP -iTCP:8080 -sTCP:LISTEN` names it; stop it
  (`docker compose -p knowgov down` from any folder for the local stack)
  and stop any earlier `ssh` that half-bound the port, then open the tunnel
  again. Do not tunnel another local port to the instance's 8080: the page
  answers only for the address it is published on, and would show but
  refuse runs. To use another port, start the instance's stack with
  `KG_PORT_APP=<port>` and tunnel that port to the same one.

**The OpenAI key.** It is read from the environment of the shell that
starts the stack and passed into the application container only. It is
never written to disk, never baked into the image, and never sent
anywhere but to the OpenAI API by the harness's own calls. Without it the
Arms mode is simply disabled; everything else works.

## API keys: questions and answers

**Which keys does the page use?** One per model row in the Arms call
drop-down (`demo/models.toml`). Set only the ones for the rows you want; a
row without its key is not offered, and the header chip counts the rows
that are ("arms enabled (4 of 5 model rows)").

| row | variable | where the key comes from |
|---|---|---|
| OpenAI (the record's model and `gpt-5.5`) | `OPENAI_API_KEY` | your OpenAI account |
| Google Gemini | `GEMINI_API_KEY` | Google AI Studio |
| Anthropic Claude, through the gateway | `KG_ANTHROPIC_KEY` | your Anthropic account |
| (the same row) | `LITELLM_MASTER_KEY` | none: a string you make up |
| a row of your own (`KG_MODEL_BASE_URL`, `KG_ARMS_MODEL`) | the variable `KG_MODEL_API_KEY_VAR` names | that endpoint's provider |

**How do I set a key without leaving it lying around?** Type it at a silent
prompt in the shell that starts the stack:

```bash
read -rs OPENAI_API_KEY && export OPENAI_API_KEY
```

Paste the key, press Enter; nothing is shown, and the key stays out of the
shell's history and off the disk. It lives in that shell only: a new
terminal or SSH session has forgotten it. Never put a key in a file you
might commit, in a `.env` beside the checkout, or in a chat. To see which
key a shell holds without showing it, print its first characters only:
`echo "${OPENAI_API_KEY:0:8}"`.

**I changed a key and nothing changed.** Containers read the keys when they
are created. Recreate the one that uses the key: `app` for OpenAI and
Gemini, `litellm` for Anthropic (and `app` too for a new master key):

```bash
docker compose --profile claude --profile arms up -d --force-recreate --wait app litellm
```

**How do I know a key works before a run?** Ask the provider for its list
of models. It costs no tokens and answers 200 for a key it accepts, 401 or
403 for one it refuses:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
curl -s -o /dev/null -w '%{http_code}\n' https://api.anthropic.com/v1/models -H "x-api-key: $KG_ANTHROPIC_KEY" -H "anthropic-version: 2023-06-01"
curl -s -o /dev/null -w '%{http_code}\n' https://generativelanguage.googleapis.com/v1beta/models -H "x-goog-api-key: $GEMINI_API_KEY"
```

**A run failed with "401 Incorrect API key".** The provider refused the
value it was sent. The error shows the key's first characters, masked:
`sk-ant-…` in an OpenAI error means an Anthropic key went into
`OPENAI_API_KEY`; a value that does not start as the table below says is
probably not a secret key at all, often a key's name or id copied from a dashboard.
Set the right value, try it with the check above, and recreate the
container.

| provider | a secret key usually starts with |
|---|---|
| OpenAI | `sk-proj-` (project keys), or `sk-` |
| Anthropic | `sk-ant-` |
| Google Gemini | `AIza` |

A prefix is a hint, not a test: providers change their keys' shapes, and only
the provider's answer to the check above says whether a key works.

**How do I get and manage a key?**

- *OpenAI.* At platform.openai.com, *API keys*, choose the project and
  *Create new secret key*. The full key is shown once, in that dialog: copy
  it then, into your password manager. The list afterwards shows only the
  key's name and a shortened form, which do not work as the key; a lost key
  cannot be shown again, so create a new one and revoke the old. Set a
  monthly budget under the organisation's or the project's *Limits*, and
  give the demo its own project and key so that revoking it touches
  nothing else.
- *Anthropic.* In the Claude Console (console.anthropic.com), *Settings*,
  *API Keys*, *Create Key*, in a workspace of its own for the demo. As with
  OpenAI, the key is shown once; copy it then. Set the workspace's spend
  limit under its *Limits*. Put it in `KG_ANTHROPIC_KEY`, not
  `ANTHROPIC_API_KEY`, which Claude Code itself reads.
- *Google Gemini.* In Google AI Studio (aistudio.google.com), *Get API
  key*, *Create API key*, in a Google Cloud project of its own for the
  demo. Restrict the key to the Generative Language API in the Cloud
  console's *Credentials*, and set a budget alert on the project's billing.
- *The gateway's master key.* Nobody issues it; make one up each time if
  you like: `export LITELLM_MASTER_KEY="sk-$(openssl rand -hex 24)"`. The
  page presents it to the gateway, which refuses any caller without it.

**What does a run cost, and how do I keep it bounded?** An S1 arms run on
the record's model makes two calls, about 33,000 tokens in all, a few
cents. Bound what a leaked or misused key could spend with the provider's
own limits above, one key per purpose, and revoke a key you no longer
use. On a shared or public machine, set `KG_PAGE_TOKEN` too, so that only
people who have it can start a run.

**Where does the key go?** From the shell's environment into the container
that calls the provider (`app`, or `litellm` for Anthropic) and from there
only to that provider. It is never written to disk or baked into an image,
and the worker that runs the model's code has no key and no network: its
self-check fails if a key-shaped variable reaches it.

## Files

| path | what |
|---|---|
| `docker-compose.yml` | the two services, with the registry image for the app |
| `docker-compose.override.yml` | local build of the app image from this checkout, and demo runs written into the checkout |
| `Dockerfile`, `Dockerfile.dockerignore` | the app image: Python 3.12, this repository installed, the harness's dependencies at the record's versions |
| `app/server.py` | the web server (standard library only): the menu, the report view, starting a re-run, the store's status |
| `app/views.py` | builds the report view of a scenario from its result files |
| `app/cascade.py` | draws the systemic-model view with the deck generator's layout |
| `app/index.html` | the one page |
| `model/model.json`, `model/SOURCE.md` | the vendored Legible model v0.3 and where it came from; written by `tools/vendor_legible_model.py` at the repository root |
| `model/cascade_layout.py` | the layout tables of the systemic-model view, carried from pumllint's deck generator; its digest is in `model/SOURCE.md` |
| `register/`, `register/SOURCE.md` | the vendored IEAM register at its tag and where it came from; written by `tools/vendor_register.py` at the repository root |
| `tools/compare_deterministic.py` | compares a deterministic run against the record, field by field; the CI job and the pull request's proof use it |

## Keeping the demo current

Four things in this folder and under `subjects/` are copies of something that
lives elsewhere, and one check guards the harness. Each has one command. All
of them run from the top of the knowgov checkout, and all of them end the
same way: run the tests, open a pull request.

**The register, when a new tag is published.** The demo carries a copy of
the IEAM register (`register/`) at a tag, so the page works offline and the
image carries it. Check `fdurieux/ieam-register` out at the new tag, in a
folder beside this checkout, and run:

```bash
python tools/vendor_register.py ../ieam-register
```

It copies the register's files byte for byte and rewrites
`register/SOURCE.md` from what git reports: the tag, the commit, a
checksum per file, and the earlier copies as a table. It refuses a
checkout with uncommitted changes, and a commit without a tag unless you
pass `--allow-untagged`. Add `--dry-run` to see what would change without
writing anything. Never edit `SOURCE.md` by hand: a test holds it to the
tool's output, and another checks every copied file against its checksum
and runs the register's own checker on the copy.

**The Legible model, when the site publishes a new version.** The
systemic-model view draws `model/model.json`, generated in
`fdurieux/fdurieux.github.io`. Check that repository out at the commit you
want and run:

```bash
python tools/vendor_legible_model.py ../fdurieux.github.io
```

The model's version is read from the file itself; a tag is recorded when
the commit carries one and is not required, since that repository has
none today. The note also carries the checksum of `model/cascade_layout.py`,
the layout tables beside it; a test holds both.

**The CargoQuote subject and the record, when pumllint tags a release
that carries them.** The kit, the documents, the oracle and the record live
in pumllint and are copied under `subjects/cargo_quote/vendor/`. Check
pumllint out at the tag and run:

```bash
python tools/vendor_subject.py ../pumllint
```

Until a pumllint tag carries the experiment, `--allow-untagged` copies a
commit and the note says so.

**The harness, after any change to it.** Run one scenario
deterministically from the page, then compare the run folder with the
record, leaf for leaf:

```bash
python demo/tools/compare_deterministic.py runs/<the run's folder> --scenarios S1
```

Name the scenarios the run holds with `--scenarios`; without it, the
command compares every scenario of the record, and one the run does not
hold counts as a difference. It exits 0 when nothing differs and prints
every differing leaf either way. A scenario whose record also holds a deterministic-mode run (S6,
`results/d3check/S6`) is compared against that by default; pass
`--record-for S6=subjects/cargo_quote/vendor/kg_experiment/results/S6` to
compare a run that registered the derived output with the scored record,
which the page does on its own, setting the record's `valid_until` aside as
its scenario data says. Without a database, `KG_STORE=rdflib` runs the same
check in memory.

**The published image.** Nothing to do by hand. Every merge to `main`
that touches the demo rebuilds `ghcr.io/fdurieux/knowgov` and publishes it;
another machine picks it up with `docker compose pull`.

| what | when | command |
|---|---|---|
| the register copy | a new register tag | `python tools/vendor_register.py <checkout at the tag>` |
| the model copy | a new model version on the site | `python tools/vendor_legible_model.py <checkout>` |
| a subject's copy (the kit, its code, its record) | a pumllint tag that carries them | `python tools/vendor_subject.py <checkout at the tag> --subject <id>` |
| the harness | after a harness change | a deterministic run, then `compare_deterministic.py` on its folder |
| the image | never by hand | the merge to `main` publishes it |
| everything above | before the pull request | `python tests/run_tests.py` |
