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
until you load it again. Five saved Cypher queries read it: which tag
is projected, the impact walk from the register's default start as rows
and as paths (the walk `tools/impact.py` makes, which the impact panel
also carries for the id you typed, with a copy button), coverage rule C1
with the exception joined, and the links that cite a kit document joined
to the harness's own `Artefact` by path, the one query that crosses the
two namespaces and the reason to share one database. Every saved query
carries a marker, *runs now* or *needs S6 loaded deterministically*,
*needs S4 loaded*, *needs the register projected*: the store holds one
scenario at a time, so a query run against the wrong state gets Neo4j's
"label not in the database" warnings and no rows, which is correct and
not a fault.

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
with each link's state, owner and evidence. The walk follows links only
and does not climb a node's parent, so it says so when it reaches no
product. A link runs the checker at today's date instead of the pinned
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
| **Arms** | re-runs the two assistants once each (`--n 1`; the record used five runs) against the freshly loaded store, grades them with the kit's oracle, shows the result | an OpenAI API key in `OPENAI_API_KEY` | one to two minutes | a few cents per scenario at the recorded model's list price |

The Arms button stays greyed out until the key is set. A re-run of either
kind writes into a dated folder, `runs/<date-time>/`,
and never into the vendored record under `subjects/cargo_quote/`, which is pumllint's.
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

**Which endpoint, first.** The arms call one OpenAI-compatible endpoint, named by
three settings the stack reads from your shell (never written to disk, never baked
into the image):

| setting | meaning | default |
|---|---|---|
| `KG_MODEL_BASE_URL` | the endpoint's base URL | OpenAI's own, `api.openai.com` |
| `KG_MODEL_API_KEY_VAR` | the *name* of the variable that holds the key | `OPENAI_API_KEY` |
| `KG_ARMS_MODEL` | the model name | the record's model |

The arms are enabled only when the named key variable holds a value. Set none and
the Arms buttons stay greyed out, the header chip says which variable to set, and
nothing is sent anywhere: that is the state a private instance starts in. Three cases:

- **OpenAI**: export `OPENAI_API_KEY` and nothing else.
- **Google's OpenAI-compatible endpoint**: export `KG_MODEL_BASE_URL` to Google's
  compatible base URL, `KG_MODEL_API_KEY_VAR=KG_MODEL_API_KEY`, `KG_MODEL_API_KEY` to
  your Google key, and `KG_ARMS_MODEL` to a Gemini model name.
- **A private model behind a gateway** (vLLM, Ollama, LiteLLM, an enterprise proxy):
  export `KG_MODEL_BASE_URL` to the gateway, the key the same way, and the model name
  the gateway serves.

Whatever the endpoint, a model other than the record's is a deviation: the page marks
every such run in red and names the model, and the numbers are not comparable with
the record's. The header chip names the endpoint's host and the key variable, never
the key.

The record's two arms were answered by `gpt-5.1-2025-11-13`, and the
demo calls that model by default, so an Arms run is like-for-like with
the record. That model is a year old, and on a new OpenAI organisation
its rate limit can be as low as 10,000 tokens per minute, while the
governed arm's prompt alone is about 15,000 tokens: the call is then
refused with a 429 "request too large" before it runs, and the page says
so in red. Two ways out, and the page lets you switch between them at
any time:

- **Raise the limit** on the OpenAI side (a higher usage tier, or a
  limit-increase request on your organisation's Limits page) and keep
  the record's model. Results stay comparable with the record.
- **Call another model**, chosen in the *Arms call* toggle at the top of
  the scenario list (default `gpt-5.5`). The gate, the evidence bundle
  and the oracle are unchanged, but the arms' answers are another
  model's: the page marks every such run in red as a deviation, names
  the model on each run, and the numbers are not comparable with the
  record's. Setting `KG_ARMS_MODEL` in the environment before
  `docker compose up` preselects this choice.

**The agent arm.** A subject whose manifest says `[arms] kind = "agent"`
(the J-F data load does) runs each arm as a loop of turns instead of one
reply: the model has four tools, read a document, write a file into the
run's sandbox, run the scenario's own feature files over the sandbox, and
finish with its decision. Model-written code runs only inside that
sandbox, a folder under the run's directory, and only through the suite
command the subject's oracle script names; nothing else executes it. Each
run is bounded by a ceiling in calls, dollars and seconds, instance
configuration read from `KG_AGENT_MAX_CALLS`, `KG_AGENT_MAX_USD` and
`KG_AGENT_MAX_SECONDS` (defaults 30, 5 and 1500); a run that reaches it
ends with decision abstain and the reason. Every turn and tool call is
written to a trace file beside the run, and the Generate box shows it.
The pristine suite, the oracle, grades the sandbox afterwards as it
grades a reply. With `context = "pull"` in the manifest the first message
is an index, not the whole bundle or every document: the governed arm reads
a key's knowledge through `read_knowledge(key)` and the baseline arm a
document through `read_document(path)`, every read logged, so the gate
box shows which keys below verified a run read and which it marked as
assumptions, and a turn resends far less. The cost estimate prices the
prompt tokens the endpoint reports as cached at a tenth of the input rate.

A subject whose record ran no arm (the J-F data load: its record graded
whole rebuilds, so its `record_model` is empty) has no like-for-like
choice. The toggle then offers only *another model*, the run calls that
model, and the report says the record has no arm result to compare with;
nothing is marked as a deviation, since there is nothing to deviate from.

The choice is remembered by your browser. Either way a re-run writes
into `runs/`, never into the record, and the cost estimate
the harness prints uses the record model's list price.

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

Re-runs land in `~/knowgov/runs/<date-time>/`,
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
restrict the firewall to your own address on ports 8080, 7474 and 7687:
the demo page has no login, and 7474 is a live database console.

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

**Another laptop, without building.** The compose file names the image
the repository publishes on every merge, `ghcr.io/fdurieux/knowgov:latest`
(also tagged with the commit's short SHA). From the `demo`
directory of a checkout:

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
the stack as above with `KG_BROWSER_URL=http://<the instance's public address>:7474`
exported so the demo's "Open Neo4j Browser" link points at the instance
rather than at your own machine. **Restrict the security group to your own
IP address** for ports 8080, 7474 and 7687: the demo page has no
authentication at all, and port 7474 is a live database console protected
only by the password you set. Do not leave the instance reachable from the
internet; stop or terminate it after the session.

**The OpenAI key.** It is read from the environment of the shell that
starts the stack and passed into the application container only. It is
never written to disk, never baked into the image, and never sent
anywhere but to the OpenAI API by the harness's own calls. Without it the
Arms mode is simply disabled; everything else works.

## Files

| path | what |
|---|---|
| `docker-compose.yml` | the two services, with the registry image for the app |
| `docker-compose.override.yml` | local build of the app image from this checkout, and demo runs written into the checkout |
| `Dockerfile`, `Dockerfile.dockerignore` | the app image: Python 3.13, this repository installed, the harness's dependencies at the record's versions |
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
python demo/tools/compare_deterministic.py runs/<the run's folder>
```

It exits 0 when nothing differs and prints every differing leaf either
way. A scenario whose record also holds a deterministic-mode run (S6,
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
