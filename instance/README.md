# An organisation's own instance

This folder describes how an organisation keeps its *own* content for knowgov: its register,
its documents and its subjects, in a git repository of its own that never comes back here. The
public demo runs on synthetic content (CargoQuote and J-F's data load). An *instance* is the
same platform pointed at your content instead.

Two words first. A **register** is the list of your architecture's building blocks and how they
connect: capabilities, products, journeys, processes, applications, information, organisation
units, with typed, approved links between them. It has its own repository layout,
[ieam-register](https://github.com/fdurieux/ieam-register), which you copy to start yours. A
**subject** is one body of documents the platform loads and checks: a manifest
(`subject.toml`) that lists the documents, the task the gate answers, and the keys that task
needs. The [subjects guide](../subjects/README.md) describes it field by field.

## The layout

```
<your instance>/
  register/            your register: a copy of ieam-register's layout with your content
                       (its exports/<system>/<date>/ folders live inside it, as ieam-register has them)
  artefacts/<kind>/    your documents, one folder per kind (the table below)
  subjects/<id>/       one folder per subject: subject.toml and its companions; its documents are
                       named by path, ../../artefacts/<kind>/<file>; its captures/ holds the
                       answered questionnaires (see "Capturing what people know")
  record/<subject>/    your own results, kept as evidence: a subject's [record] dir points here
```

The platform reads this folder and never writes to it: the compose file mounts it read-only,
and every run lands in the platform's own `runs/` folder.

## Kinds of document, and which ones the platform reads

A *kind* is one row of the programme's table *Artefact by artefact* on
[fdurieux.github.io](https://fdurieux.github.io/). A *mapper* is the part of the platform that
turns one kind of document into statements the store holds. A kind with no mapper can still be
in your instance; the platform then says, for each such file, that it holds **no statement**
from it, instead of skipping it quietly. `instance/kinds.toml` is the same table in machine form.

| folder under `artefacts/` | the table's row | mappers that read it |
|---|---|---|
| `plantuml-models` | PlantUML models | `sequence`, `containers`, `plantuml_realises` |
| `aris-epc` | ARIS process models (EPC) | none: convert them with aris2puml, then they are PlantUML models |
| `textual-requirements` | Textual requirements | `requirements`, `requirements_json` |
| `user-stories` | User stories | none |
| `specification-prose` | Specification prose | `spec`, `contracts_markdown` |
| `acceptance-scenarios` | Acceptance scenarios (Gherkin) | `gherkin`, `gherkin_tagged` |
| `bpmn-process-models` | BPMN process models | `bpmn` |
| `decision-tables` | Decision tables (DMN) | `decision_table`, `dmn`, `dmn_decisions` |
| `cross-artefact-links` | Cross-artefact consistency | `links` |
| `architecture-decisions` | Architecture decisions (ADR) | none |
| `c4-models` | C4 architecture models | none: a C4 diagram drawn in PlantUML goes under `plantuml-models` |
| `archimate-models` | ArchiMate enterprise models | none |
| `sysml-capella-models` | SysML v2 and Capella | none |
| `api-contracts` | API contracts (OpenAPI, AsyncAPI) | `openapi` |
| `schemas` | Schemas (Protobuf, GraphQL, JSON Schema) | none |
| `data-models` | Data models | none |
| `threat-models` | Threat models | none |
| `event-logs` | Process design against reality | none |
| `glossary` | Vocabulary (glossary) | none |
| `property-invariants` | Property-based invariants | none |

## Checking an instance

```bash
python tools/check_instance.py /path/to/your/instance
```

In plain English: the check looks at the folder and reports what it found. It confirms the
register is there, loads every subject, and confirms every document a subject names exists.
Then it lists your documents kind by kind, with the mapper that reads each one. It also lists
two kinds of file worth a look. *ABSENT* is a file no mapper reads, so the store holds nothing
from it. *UNREAD* is a file under `artefacts/` that no subject names. It exits 0 when the
layout holds and 1 when it does not, for example with no register, a folder that is not a kind,
or a subject that does not load. It exits 2 when it cannot run at all. Add `--json` for the
report as data.

## Checking a document before the load

```bash
python tools/preload_check.py /path/to/your/instance
python tools/preload_check.py /path/to/your/instance --changed artefacts/plantuml-models/quote_flow.puml
python tools/preload_check.py /path/to/your/instance --since origin/main
```

In plain English: this runs, for each document under `artefacts/<kind>/`, the linter the
programme's table names for its kind (the `lint` field of `instance/kinds.toml`), when that
linter can run here. Today one can: pumllint, for `plantuml-models`. Every other kind's files are
listed as *UNCHECKED*, with the tool the table names (or "names no linter"), so the gap stays in
sight; an unchecked file does not fail the check, and it is never passed quietly. Without
`--changed` or `--since` it checks every file; with them, only the files named, or changed since
that git reference. It exits 0 when every checked file is clean, 1 when one has a finding at or
above `--fail-on` (default `major`, pumllint's own), and 2 when it cannot run: a linter not
installed, a folder that is not a kind, a named file that does not exist. `-f json` prints the
report under `harness/schemas/preload-report.schema.json`. The linter runs with your instance as
its working directory, so your own pumllint configuration applies.

To run it on every pull request, copy `instance/ci/preload-check.yml` into your instance's
`.github/workflows/`, pin `KNOWGOV_REF` to a knowgov tag, and make the job a required check with
a reviewer who is not the author. It lints the documents the pull request changes, then runs
`tools/check_instance.py`; the script it calls, `instance/ci/preload-check.sh`, is the one this
repository's CI runs on the example instance. Your other linters (Spectral, Vale, bpmnlint...) go
in as steps of their own before it. The load reads only what was merged.

**What it does not do.** It checks *form*, one file at a time: is this a well-formed document
of its kind? It does not check *knowledge*. Two well-formed documents that disagree, or a fact
nobody wrote down, pass it. That is the knowgov gate's question, `harness/gate_cli.py`, after the
load; neither replaces the other. And both pass documents that are consistently wrong. The check
does not record its verdict in the store, and keeps no baseline of its own yet.

## Trying it with public content first

```bash
python tools/example_instance.py /tmp/example-instance
```

In plain English: this builds an instance from the public test case, ieam-register's register
plus CargoQuote's documents, sorted into their kinds. It then runs the check on it. It writes
only into the folder you name. The demo's CI mounts that folder read-only, replays a scenario,
runs one deterministically, and confirms afterwards that not one byte of the folder changed.

## Capturing what people know

Some knowledge is in nobody's documents, only in people's heads. The gate then reports a key as
*absent* or as a *declared gap*, and it blocks. The capture path turns that into a recorded
statement, without anyone having to write a document first.

```bash
python harness/capture.py questionnaire --scenario S2 --out questionnaires/
```

In plain English: this loads the scenario, asks the gate which keys are missing or weak, and
writes one questionnaire per *owner*: the organisation unit your register names as owner of the
building blocks each key concerns. Each questionnaire says how many keys the owner has and how
many need an answer. For each one it shows what the store holds now and asks one question. A key
no register row covers goes to a questionnaire named `unassigned`, so nothing is dropped.

The owner fills it in: a value in `answer`, or `nobody_knows = true` when no one can say. They
add their *handle* and the date under `[answered]`. A handle is a short lower-case label such
as `steward-1`, never a name or an e-mail address. Then:

```bash
python harness/capture.py ingest questionnaires/questionnaire-cargo_quote-S2-ORG-0002.toml
```

In plain English: this checks the answers and refuses a name in place of a handle, a date in the
future, or an item that has both an answer and "nobody knows". It then saves them in the
subject's `captures/` folder, which you commit like any other change. From then on, every
load reads that folder. An answer becomes a statement *proposed* by that person on that date,
and a "nobody knows" becomes a declared gap with their handle and the date. Neither goes further
on its own. A proposed statement is still below verified, so the gate lists it as an assumption
an assistant must state. Nothing the harness does verifies a person's answer, nor a model's
guess. Review is a person's act.

**Reviewing what people said.** A captured answer stays *proposed* until a second person rules
on it. That ruling is a *review*: a short file, written once and never edited, that says who
reviewed, on what date, and where the reasons are kept (minutes, a decision record). It lists one
*ruling* per statement, `approved`, `rejected` or `referred`, and may close a declared gap:

```toml
[review]
by = "employee-2"        # an issued handle, never a name
on = 2026-11-09
record = "minutes/2026-11-09-outage-rule.md"
scenario = "S2"

[[ruling]]
assertion = "A:cap:2026-11-02-ORG-0002-employee-1:1@capture"   # the id the gate's bundle shows
outcome = "approved"
```

```bash
python harness/capture.py review review.toml
```

In plain English: this loads the scenario, checks the review against what the store holds, and
saves it in `captures/reviews/`. Every later load of that scenario applies it. An approved
statement counts as *approved*; a rejected one, whether a person's answer or a document's
sentence, stops counting but stays on record; a closed declared gap stops blocking. With every
key approved or verified, the gate says PROCEED.

Who may do what comes from your register's list of issued handles (`people/handles.toml`), never
from the review itself, and the command refuses a review that breaks a rule, naming it:

- **Approving an answer** needs the role `approves`, in a unit that owns the key, and never the
  handle that gave the answer.
- **Overruling a document**, rejecting or approving one of its statements, needs the role
  `closes`. So does **settling a dispute**: the review must rule on *every* side, approving what
  is kept and rejecting the rest, and what it keeps must agree. Approving one side alone is refused,
  and the key stays disputed.
- **Closing a declared gap** needs `closes`, in the unit the declaration names as its owner (or,
  when it names none, a unit that owns the key). If the declaration names an owner your register
  has no unit for, nobody can close it until the register has that unit and a handle of it.
- **An approved answer lapses** six months after it was given: the statement reads *proposed*
  again until someone re-asks and a reviewer approves again. Set `KG_TODAY=YYYY-MM-DD` for a
  reproducible date.

A review copied into `captures/reviews/` by hand is checked again on every load: one that breaks
a rule is skipped, and the load prints why. The rules are knowgov's decision-0002; the handles
and roles are ieam-register's decision 0009. `tools/check_review_walkthrough.py` runs the
whole path on the example instance.

**The register's capture fields.** The three fields a capture carries are `from` (the handle),
`on` (the date) and `record` (where the answer is kept). They are the fields ieam-register's
[decision 0008](https://github.com/fdurieux/ieam-register/blob/main/decisions/0008-knowledge-a-person-gave.md)
adds to the register for a link that rests on what a person said, with a review due within six
months. The register's other required capture fields were there before: a link's `rationale`,
an exception's `rationale` and expiry, and the decision record every approval names.

## Starting the demo on your instance

```bash
cd demo && KG_INSTANCE=/path/to/your/instance docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.instance.yml up -d --build --wait
```

In plain English: the same stack as the demo, with your folder mounted read-only at `/instance`.
The page reads your register (`/instance/register`) and lists your subjects
(`/instance/subjects`), and none of the public ones. Leave `-f docker-compose.override.yml` out
to pull the published image instead of building it. One stack serves one instance.

## Letting an AI assistant ask the gate

An AI coding assistant can ask knowgov the gate's question itself, before it writes anything:
*may I build on this?* It does so through MCP, the Model Context Protocol, a standard way for an
assistant to call tools a local program offers. `harness/mcp_server.py` is that program. It offers
three tools, and all of them only read:

| Tool | What the assistant asks | What it gets back |
|---|---|---|
| `store_status` | What does the store hold? | the subject, the scenario loaded, the task classes and their required keys |
| `gate_verdict` | May I build on the knowledge this task needs, or on these keys? | PROCEED, QUALIFIED or BLOCKED with the findings: the same report `gate_cli.py --no-load -f json` prints |
| `three_valued_answer` | What is known about this one key? | asserted, documented absent, or unknown, with where each statement came from and who verified it |

The server reads the store as the page or a run left it. It never loads a scenario and never
writes to the store, the register or your instance; a change to the record is still a pull
request. Load what the assistant should see first, on the page or with a run.

**With the stack running** (above), the simplest connection needs no extra port: the assistant
starts the server inside the container and talks to it over the connection it opened. For Claude
Code:

```bash
claude mcp add knowgov -- docker compose -f /path/to/knowgov/demo/docker-compose.yml exec -T app python harness/mcp_server.py
```

In plain English: `claude mcp add knowgov` registers a tool server named knowgov, and everything
after `--` is the command that starts it. Here that command runs `harness/mcp_server.py` in the
`app` container. Other assistants take the same command in their MCP settings, usually as
`"command": "docker"` with the rest as `"args"`.

**Over HTTP**, for an assistant that connects to a URL:

```bash
python harness/mcp_server.py --http            # http://127.0.0.1:8765/mcp
```

It listens on this computer only (`127.0.0.1`), so nothing else on the network can reach it.
`--host` and `--port` change that, or `KG_MCP_HOST` and `KG_MCP_PORT`. An address other than this
computer's is refused unless `KG_MCP_TOKEN` holds a secret; every request must then carry it as
`Authorization: Bearer <secret>`. A request sent from a web page on another site is refused
whatever the address. The tools return your documents' text, so keep the server private: the
token is a lock, not a reason to put it on the internet.

Outside the container, the server needs the same Python packages as the harness and the same
store settings (`KG_STORE`, and for rdflib `KG_RDFLIB_FILE`, the file a run left). For a store
with nothing loaded, every tool says so instead of answering.
