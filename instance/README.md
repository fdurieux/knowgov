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
  code_map.toml        optional: which register application or module each code path implements
                       (see "Mapping code to the register")
  connectors.toml      optional: the systems of record whose exports you mirror into register/exports/
                       (see "Mirroring an export from a system of record")
```

The stack reads this folder and never writes to it: the compose file mounts it read-only, and
every run lands in the platform's own `runs/` folder. Only commands you run yourself, in your own
checkout, write to it. The connector adds an export to your register. `harness/capture.py ingest`
and `review`, and `harness/transcript.py`, add answers, reviews and suggestions to a subject's
`captures/`. You commit what they write like any other change.

Keys are compared in Unicode NFC: two keys that are canonically equivalent are one key, and
knowgov stores and reports the NFC form, so `société|adresse` typed composed and a document that
spells it decomposed name the same key. On a macOS checkout, run
`git config core.precomposeunicode true` once, so file names reach git composed.

## Kinds of document, and which ones the platform reads

A *kind* is one row of the programme's table *Artefact by artefact* on
[fdurieux.github.io](https://fdurieux.github.io/). A *mapper* is the part of the platform that
turns one kind of document into statements the store holds. A kind with no mapper can still be
in your instance; the platform then says, for each such file, that it holds **no statement**
from it, instead of skipping it quietly. `instance/kinds.toml` is the same table in machine form.
`instance/mappers.toml` says, for each mapper, what a document must look like for it to read anything
(most follow the public demo's own conventions, such as requirement rows `| REQ-nn | text |`).

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

Across your subjects it refuses three things, each exit 1:

- an empty `subjects/` folder. An instance holds at least one subject;
- two subject folders whose `subject.toml` declare the same `id`. A subject is named by its id
  (the page's `?subject=`, the assistants' `subject` argument), so each must be unique;
- a scenario id that two subjects declare, such as `S0` in both. The store your page and
  assistants share records the scenario it holds by its id alone, so one subject's gate would
  answer from the other subject's load. Give each subject its own scenario ids: `billing-S0`,
  not `S0`.

It also reads each subject's own files, the way the gate would, and says what the gate would only
show you later, or not at all:

- a table or field in `subject.toml` that knowgov does not read, such as `[task.codegen]` for
  `[tasks.codegen]`. It would otherwise be ignored without a word. The check names the nearest
  real name;
- a task's missing or malformed settings: its `keys`, its `block_levels` and its
  `max_unverified_share`. A key is written `<entity>|<predicate>`, for example `REQ-01|text`: one `|`, each
  side non-empty, of characters up to U+FFFF with no space, no control and no format character (task-0297).
  `block_levels` is a list, such as `["absent"]`, never a bare `"absent"`. A task class's name is
  lower case, such as `codegen` or `design`: a letter first, then letters, digits, `_` or `-`, at
  most 32 characters. It is never `keys`, which is the name a report gives a set of keys an
  assistant chose. A subject with a malformed task class, or a class name outside that rule, does not
  load: every gate call exits 2 naming the class or the field;
- a subject with a task and no scenario. The gate runs on a scenario, so it cannot run on such a
  subject. Copy the pristine scenario `S0` from `subjects/minimal/scenarios.toml` and rename it
  `<id>-S0`;
- a row of `register_map.toml` that names a node your register does not hold, or whose `owner`
  owns none of the row's nodes. Without the check, the questionnaire would quietly go to someone
  else;
- a required key that no document yields when a document yields one very close to it. For
  example, the task asks for `REQ-02|txt` and your requirements give `REQ-02|text`. This shows as
  a *WARNING* with the key the documents do yield. Without it, the gate would report the key absent
  and send its owner a question that a spelling fix answers. A document's yield is offered once, to the
  required key it is closest to; and when that key is about another entity (`REQ-04|text` beside a
  yielded `REQ-03|text`), it is not a misspelling but a requirement no document states, so the
  check lists it as a *NOTE* for its owner, with no suggestion;
- a document its mapper reads and yields nothing from. That almost always means the document is not
  in the convention the mapper reads (a requirements file whose ids start `RNW-` rather than `REQ-`,
  say), not that it holds no knowledge. The *WARNING* says what the mapper reads and names the kind's
  other mappers; if none fits, leave the mapper out and the document is reported ABSENT. Never
  rewrite your documents' ids to suit a mapper;
- an artefact with a mapper and no `short`. The mappers name every statement after it, so the load
  would fail with an error that seems to blame the document. The check asks for `short`, from the
  file's name.

To read what your documents yield, the check runs the same mappers the load runs, on your files.
It needs the same Python packages the load needs: PyYAML, and pumllint for PlantUML. Where they are
not installed, the check says the yield was not checked; it never passes it quietly. A key that no
document yields, and that has no close match, is a *NOTE*. The gate will report it absent unless a
person's answer supplies it, which can be right. The first four problems in the list, and the last
(a document with a mapper and no `short`), are layout errors: the check exits 1, as it does for a
missing document. Warnings and notes do not change the
exit code. The check opens no store and writes nothing.

To check one subject on its own:

```bash
python tools/check_subject.py /path/to/your/instance/subjects/<id> --register /path/to/your/instance/register
```

It prints the same findings, each with its fix, and exits 0, 1 or 2 like the layout check. Add
`--json` for the report as data, pinned by `harness/schemas/subject-check.schema.json`.

The register map's rows are checked against the register you name, with `--register` or with
`KG_REGISTER`. If the register you name cannot be read (a typo in the path, or a folder that is not
a register), the check stops with exit 2 and names the path; it never skips the register check
without saying so. A folder counts as a register when its `metamodel/types.toml` lists its
taxonomies and it holds the register's own loader, `register.py` in its tools folder, the same test
every command uses.
Only when you name no register, and the public register this copy of knowgov carries cannot be read
either, are the rows reported as unchecked.

Every other command that reads a register follows the same rule: a register named, by a flag or by
`KG_REGISTER`, that cannot be read stops it with exit 2, naming the path, before it reads or writes
anything. That covers `harness/gate_cli.py` (and its `--register-previous`), `harness/run.py`,
`harness/trace.py`, `harness/capture.py`, `harness/transcript.py`, `harness/register_nodes.py`,
`harness/upward.py`, `harness/proposal_impact.py` and `harness/step_grid.py`. The MCP reader and the
page refuse to start.

### Format versions

Each file you keep in your instance says which version of its format it is written in, so a
knowgov never misreads a file written for a newer one. The number goes in five places:

- **A subject**: `subject.toml` carries one number for the whole subject root. It covers
  `subject.toml` itself, `scenarios.toml`, `plants.toml`, `queries.toml` and the register map it
  names:

  ```toml
  [format]
  version = 1
  ```

- **`code_map.toml` and `connectors.toml`**: each carries its own number, at the top of the file,
  before any table:

  ```toml
  format = 1
  ```

- **Captures and review files**: each carries its own `format = 1` at the top. `harness/capture.py`
  writes it when it stores an answer or a review. These files are records that are never edited,
  so each keeps the version it was written in, whatever happens to the subject's number later.

- **The trace ledger** (`KG_LEDGER`, `--ledger`): its `schema_version` is its format. `harness/trace.py
  register` writes it; `trace check` and the MCP tool `code_path` refuse a newer one.
- **A proposal** (`harness/proposal_impact.py`, the MCP tool `proposal_impact`): an optional top-level
  `format = 1`, as `instance/templates/proposal.toml` has it.

In plain English:

- **A file with no number is read as version 1, in every release.** Nothing you wrote before
  0.9.0 breaks, and when a format later moves to version 2, such a file is still read as the
  version 1 it was written in, never as the newer one.
- **A file at the current version, or an older one, is read.**
- **A file with a newer number is refused.** Every reader stops with exit 2, "cannot run", and
  names the file, the version it carries and the version this knowgov reads. That covers the gate,
  the trace, the capture and review commands, the connector, `proposal_impact`, the MCP server's `subject_check`,
  `code_path` and `proposal_impact` (as an error answer), and
  the two checks above. For example:

  ```text
  cannot run: subjects/billing/subject.toml: [format] version = 2, and this knowgov reads subject format 1 and earlier
  ```

  Upgrade knowgov to a release that reads that version, or keep the file at the version yours
  reads. A number that is not a whole number of 1 or more is refused the same way.

The wizard (`instance/ci/claude/skills/knowgov-onboard/`), `tools/example_instance.py` and
`subjects/minimal/subject.toml`, which every new subject is copied from, all write the current
numbers. `tools/check_instance.py` lists each subject's version beside its name, and
`check_subject.py --json` reports it as `format`.

The first time a number moves, the CHANGELOG says what changed and how to bring an older file up to
date. Adding `[format]` or `format = 1` to a file attests nothing, so the attestation hook below lets
it through.

## Mapping code to the register

Your register lists applications and their modules (`APP-` ids under `register/applications/`);
your code lives in files. Nothing else in the layout says which file implements which
application, so a change to the code cannot be traced to the knowledge it rests on.
`code_map.toml`, at the top of the instance, says it:

```toml
[code]
root = "../src"              # where the code is, relative to the instance; default "."
include = ["**/*.py"]        # what counts as code under root; default every file

[[map]]
glob = "quote/**"            # relative to root: ** any number of folders, * and ? within one name
app = "APP-0001"             # an application or module of your register
note = "the quoting service" # optional
```

In plain English: each `[[map]]` row says "the files this glob matches implement that application
or module". `tools/check_instance.py` reads the file when it is there and refuses (exit 1) a row
whose `APP-` id your register does not hold, and two rows that overlap: one file matched by both,
or one glob that covers the other (`quote/**` and `quote/api.py`), so every file maps to one id.
It lists as *UNMAPPED* each code file no row matches, and as *UNMATCHED* each row that matches no
file; neither fails the check. Without the file the check says nothing about code. The example
instance carries one: CargoQuote's reference code, mapped to `APP-0001`. A later register link
(`implemented_by`) may carry the same fact in the register itself; that is the register's
decision, and the file would then yield to it.

### Hand-written code: citing the keys it rests on

Generated code is registered with the statements it was built from. Code written by hand has
no such record unless it says what it rests on. A comment line near the top of the file (within
its first 30 lines) names the keys, comma-separated:

```python
# knowgov-keys: P2|surcharge, P2|threshold
```

```java
// knowgov-keys: P2|surcharge, P2|threshold
```

Python files use `#`, Java files `//`; other languages are not read yet. On merge,
`python harness/trace.py register --cited --file PATH ...` (or `--keys K1,K2` to name them on the
command line) records the file on the keys' current statements. When a later change to your
documents invalidates one of them, `trace.py check` reports the file as *suspect*, as it does for
generated code. A key your subject does not know is refused.

The missing-citation check is off unless you turn it on:

```toml
[citations]
require = true               # a code file of a governed application must cite its keys
apps = ["APP-0001"]          # optional: the governed applications; default every one a row names
```

With it on, `trace.py check` reports each such file without a citation (*uncited*, major), and a
file in a language the convention does not cover (*uncitable*, information).

## Mirroring an export from a system of record

Your processes may be authored in a modelling tool (the register's `metamodel/sources.toml` names
it as a system of record). The register never copies that tool's content; it keeps each export as
a dated folder under `register/exports/<system>/<date>/` and checks itself against the newest one.
The connector puts an export there:

```toml
# connectors.toml, at the top of the instance
[system.aris]                # the name your register's sources.toml gives the system
id_attribute = "AT_ID"       # the AML attribute your modellers fill with the register id; AT_ID by default
```

```bash
python tools/connector.py /path/to/your/instance --system aris /path/to/the/export/
```

In plain English: the connector reads the export's AML and BPMN 2.0 files (BPMN as any tool
writes it, ARIS's own dialect included) and finds the register ids in them in three places only:
the attribute you configured, a BPMN process's `id`, and an element's `<documentation>` text.
Element ids and diagram positions are never identity, because a tool may rewrite them on import.
It copies the files, byte for byte, into a new dated folder. The folder name is the date in the
AML header, or the one you give with `--exported-on`. Beside the files go two more:
- `MANIFEST.toml`, in your register's own export format: the export time, the source and its
  version, the tool, the previous folder, and a sha256 per file. Its `[ids]` lists every object
  in the AML, keyed by the object's GUID (the `id_field` your register's `sources.toml` gives the
  system, `aris_guid` for ARIS), with its name. That includes objects that carry no register id.
  Two more tables hold the register ids, kept apart so that `[ids]` has only one kind of key:
  - `[register_ids]` gives, for each object that carries a register id, that id, by GUID.
  - `[bpmn_ids]` gives each register id a BPMN file carries, with its name. A BPMN file has no
    GUID, so it adds nothing to `[ids]`.
- `RECONCILE.json`, written by your register's own `tools/reconcile.py`: what changed since the
  previous folder. Files are added, updated or deleted. Objects, compared by GUID, are added,
  renamed (same GUID, new name) or deleted. It also lists these:
  - `stale_nodes`: the register nodes whose object is gone. The register finds a node whose
    `[source]` names this system and a GUID the export no longer holds. The connector adds a
    node whose register id the previous export carried and this one does not. Once your nodes
    record their object's GUID in `[source]`, the register's rule finds them all and the
    connector's addition finds nothing more.
  - `unknown_ids`: register ids your modellers typed in the tool that your register does not
    hold, such as a mistyped id or a node removed from the register. Fix each one in the tool,
    or register the node.
  - `unregistered`: the register's own list (its decision 0017). It holds the objects no node
    names in its `[source]`. Until your nodes record their GUID, every object is listed. Events,
    rules and step functions that no node stands for are listed too. Leave them, or register
    them; the register has not yet decided how to excuse such an object (decision 0017, "Not
    decided here"). Read the list as a finding to triage, never as an error.

A folder landed by an earlier version keeps its bytes. The first export landed after an upgrade
reads every object as added and every earlier id as deleted in `ids`. Its `stale_nodes` and
`unknown_ids` read the register ids of both folders, so they are not affected.

A stale node is a finding for its owner. The connector never deletes or edits a node. It never
lands an export over an existing folder, or with a date before the newest one; it refuses (exit 1)
instead. Exit 0 when the export landed, 2 when it cannot run (for example, no `connectors.toml`).
Commit the new folder to your register like any other change. `tools/check_instance.py` checks
`connectors.toml` with the rest of the layout. Each `[system.<name>]` must be a system your
register's `metamodel/sources.toml` names, and `id_attribute`, when you give it, must be a
non-empty string.

## Tracing a code change to the knowledge

```bash
python harness/trace.py register --instance /path/to/your/instance --ledger trace/ledger.json \
    --commit "$SHA" --file quote/api.py --subject /path/to/your/instance/subjects/<id>
python harness/trace.py check --instance /path/to/your/instance --ledger trace/ledger.json \
    --changed quote/api.py --subject /path/to/your/instance/subjects/<id>
```

In plain English: `register` runs in your code's pipeline after a merge and a build. It records each
file you name (relative to `code_map.toml`'s root) as an output built from the statements the
task's gate serves now, or the ones you name with `--assertion`. It also records the file's digest and
the application `code_map.toml` gives it. The record goes into the store and into the *ledger*, a JSON
file you keep with your code. A load wipes the store, so the ledger is what survives the next one.
`--as-of` (today by default, `record` or a `YYYY-MM-DD` date) is the date the gate is read on, and each
ledger entry records it as `as_of`, so a registration made while rehearsing a later date says so.
`check` runs on every pull request into the code. It reads the ledger against the store as your
instance's last load left it, and against your files:

- **suspect** (blocker): a registered file was built from a statement that has since been
  invalidated, because a document changed. The finding names the application, the statements and
  their successors. Rebuild the file from the current statements and register it again.
- **missing** (major): a registered file no longer exists. **unmapped** (major): a changed code file
  that no row of `code_map.toml` maps.
- **drift** (minor): a registered file changed since its registration. The edit is legitimate, so
  the finding lists what the registered version rested on and asks for a new registration.
- the task's gate on the store as it is: its blockers and other findings, as `harness/gate_cli.py`
  reports them.

A finding that rests on knowledge keys (suspect, missing, drift, and the gate's own key findings) says
who answers for them and how, as the gate's findings do. `owner` is the organisation unit your
`register_map.toml` names for every one of those keys. It is empty when several units own them. `route`
is that owner's questionnaire for the scenario the store holds, or each owning unit's when there are
several. A finding that rests on no key, such as *unmapped*, names neither. The report's gate block
also names what the gate decided on, as the gate's own report does: `task_profile`, the digest of the
task's table in `subject.toml`; `register`, your register's tag and commit; and `knowgov`, the build
that judged.

With `--changed`, it looks only at the registered files that changed and the applications a
changed file belongs to. Without it, it looks at every registered file. It exits 0, 1 or 2 like the
gate: 1 on a finding at or above `--fail-on` (default `blocker`), 2 when it cannot run (no
`code_map.toml`, one that does not hold, no ledger, an unreachable store). `-f json` prints the
report under `harness/schemas/trace-report.schema.json`. Every input is a flag. Nothing reads a CI
platform's variables, so a wrapper for your platform maps its commit and changed files to the
flags. `tools/check_trace_walkthrough.py` runs it on the example instance: S6's change to the decision
table turns the registered reference code suspect, and `check` exits 1 naming `APP-0001`.

What it does not do: it does not read code. It cannot tell whether a file does what its statements
say (that is your tests' job), and hand-written code that cites nothing maps to an application,
not to statements.

## Running the gates in your pipeline

The three gates (the pre-load check, the knowledge gate `harness/gate_cli.py`, and the trace's
`check` and `register`) take explicit flags and read no CI platform's variables. A thin wrapper
per platform maps the platform's commit and base to those flags. All three wrappers call one script,
`instance/ci/knowgov-gate.sh`, so every platform runs the same command line:

```bash
sh knowgov/instance/ci/knowgov-gate.sh knowgov instance trace-check   # or preload, gate, trace-register
```

In plain English: the script reads `KG_*` variables (the list is at its top: `KG_BASE`, `KG_COMMIT`,
`KG_FAIL_ON`, `KG_SCENARIO`, `KG_AS_OF`, `KG_LEDGER`, `KG_FILES`, `KG_REPORT`...). It works out the changed code
from git against `KG_BASE`, in the folder `code_map.toml` names, and calls the core command. Its exit
code is the command's: 0, 1 or 2.

`PYTHON` names the interpreter (default `python3` as `PATH` finds it). The script checks it once, before
anything else, and runs every step, the pre-load check's included, with that interpreter's absolute
path, so another `python3` earlier on `PATH` never runs a step. An interpreter that is missing or older
than Python 3.12 cannot run: exit 2 with the reason, and no report is written or annotated. The same holds
for `preload-check.sh` and `proposal-impact.sh`; the Claude Code hook passes its own interpreter unless
`PYTHON` is set (task-0141.01).

`KG_AS_OF` is the date the gate, `trace-check` and `trace-register` read review currency on (`--as-of`, decision-0005):
a `YYYY-MM-DD` date, `record` (the subject's pinned record date) or `today`, the default. Set it to
check a release as of its cut date, or to rehearse a lapse before it falls due: S1 as of 2027-08-08
is BLOCKED, with a `lapsed` finding for each review past its months. The action takes it as the
input `as-of`; the GitLab include as the variable `KG_AS_OF` (task-0089; `trace-register`, task-0093).

The `gate` step computes on a private copy of the store and leaves the one `KG_STORE` names as it
was (decision-0017). When a later step of the same pipeline reads that store, `trace-check` or
`trace-register` after `gate`, set `KG_PUBLISH=1` on the gate step: it then loads into that store and
publishes the load for the steps after it. The action takes it as the input `publish: "true"`; the
GitLab include as the variable `KG_PUBLISH`. A pipeline that runs only the gate needs neither.

- **GitHub Actions**: a composite action. It runs the knowgov tag you name in `uses:`, and maps the
  commit and the pull request's base for you:

  ```yaml
  - uses: fdurieux/knowgov/instance/ci/github@<tag>
    with: { gate: trace-check, instance: instance, ledger: trace/ledger.json }
  ```

- **GitLab CI**: an include, `instance/ci/gitlab/knowgov.gitlab-ci.yml`, with a hidden job
  `.knowgov-gate` your jobs extend. It maps `CI_COMMIT_SHA` and `CI_MERGE_REQUEST_DIFF_BASE_SHA`.
  Its job clones knowgov at `KNOWGOV_REF`, which defaults to the include's own release tag, so the
  include you take from a tag runs that tag's harness. To move to a later release, change the tag in
  the include's URL; the default follows it. Setting `KNOWGOV_REF` on its own would run another
  release's harness under this release's job, so move the two together. `KNOWGOV_PIP` installs what an
  rdflib store needs. Against Neo4j, add the driver at `demo/Dockerfile`'s pin, `neo4j==6.4.1`: the gate
  with `KG_PUBLISH=1` and the trace jobs after it connect to that store.
- **Anything else** (Jenkins, Azure DevOps, Bitbucket): set the `KG_*` variables from your platform's
  own and call the script.

Installing Python, the pins and the store's connection details are your pipeline's own steps,
taken from its secrets and variables. Make the job a required check: branch protection on GitHub,
approval rules on GitLab. `KG_REPORT` writes the JSON report, to keep as an artefact.

The findings also reach your platform's own surface (`KG_ANNOTATE`, `harness/annotate.py`). On
GitHub the action does this by default (input `annotate`): each finding is an annotation on the run
and the pull request, and the job summary carries a table of them. On GitLab the include writes
`gl-code-quality-report.json`, which the merge request's code-quality widget shows. Any other
platform names the formats it reads, for example `KG_ANNOTATE=sarif:knowgov.sarif`. A finding at or
above the threshold is an error. A finding on code points at the file, and a pre-load finding at its
document's line. A finding on a key or a statement points at the subject's `subject.toml`, since the
report names statements, not lines in a document. A finding that names its keys' owner and route ends
its message with them (`Owner: ORG-0001. Route: ...`), so the annotation says who answers. A pre-load finding your baseline holds is at most a
warning, since it did not fail the check. The layout check's problems are annotated too, since the
pre-load gate's report carries them (its `layout` block). A layout error is an error, at the file it
names, or at a subject's `subject.toml`. A document no subject names, or one that no mapper reads, is a
notice or a warning at that document. A subject's warnings and notes are at its `subject.toml`.
Annotations never change the exit code.

On GitHub the action can also send the findings to code scanning, so they stay in the repository's
Security tab between runs. It is off by default: set the input `sarif: true` (and, optionally,
`sarif-category`; the default is `knowgov-<gate>`). The action writes the report as SARIF 2.1.0 and
uploads it with `github/codeql-action/upload-sarif`, pinned by commit, even when the gate fails; a
run that cannot run (exit 2) writes no report and uploads nothing. Your instance needs two things:

- the job's token may write security events: `permissions: { contents: read, security-events: write }`
  on the job that runs the action, not on the whole workflow;
- code scanning available on the repository: any public repository, or a private one with GitHub
  Advanced Security (Code Security). A pull request from a fork gets a read-only token, so pass
  `sarif: false` for it, as this repository's CI does.

The upload's id is the action's output `sarif-id`. The exit code stays the gate's.

knowgov's own CI exercises the upload on its same-repository pull requests only, never on `main` or
the nightly run: its findings are the example instance's, a fixture, and a default branch's upload
would keep them as standing alerts in the Security tab. A pull request's upload is analysed against
its merge ref and leaves no alert on the default branch. Your instance's findings are real, so upload
wherever your team reads them.

This repository's CI runs the GitHub action on
the example instance, and runs the GitLab job's own script lines in a shell
(`tools/check_ci_wrappers.py`). Both use S6: the change turns the registered code suspect, and the
check fails naming `APP-0001`.

## A register pull request read before approval

A proposed product, capability or journey reaches your register as a pull request: new node files
and links, in state `draft` or `proposed`. Read as they are, the register's walks and coverage rules
do not see them until someone approves them, and by then it is late to change the design.
`instance/ci/proposal-impact.sh` is an optional step for that pull request. It reads the branch's
additions *as if approved*, with your register's own checker and walks, and prints what they would
mean (task-0132):

```sh
sh instance/ci/proposal-impact.sh <knowgov checkout> <register checkout> origin/main
```

It runs `harness/proposal_impact.py --register-branch <register checkout> --base origin/main`. The
proposal is what the branch adds since its merge base with `origin/main`: every node file added,
every link whose id is new, every exception file added. The ids are the branch's own. A node file the
branch changes counts as a reused node `changed`, so its owner sees what the change reaches. Anything
else, such as a deleted file or a link changed in place, is listed under `branch.not_read` and not
read. The report is the one the MCP tool `proposal_impact` gives, described in "Letting an AI
assistant ask the gate" below:

- every coverage rule your register's checker defines (C1 to C4 at ieam-register v0.2.13) before and after, with the new gaps;
- the link candidates;
- what each reused node reaches, before and after;
- what each new node rests on;
- which unit must approve what.

Every proposed element is marked `hypothetical`.

The step is advisory. It exits 0 with a report and 2 when it cannot run. A gap is reported, never a
failure, because your register's own checker decides at approval. It posts nothing. With
`KG_PROPOSAL_REPORT=<file>` it also writes the JSON report, in the shape
`harness/schemas/proposal-impact.schema.json` pins, for your platform to attach. The checkout is
read, never written; the base register is taken from git into a temporary directory and removed. It
does not open the store, so the reused nodes' keys carry no level here. Ask the MCP tool for those.

### Writing a proposal before the pull request

You can read a proposal before anyone has written a register file for it.
`instance/templates/proposal.toml` is an annotated template: the new nodes, the links that join them
to what exists, the register nodes the proposal reuses, and any exception it asks for, each field
explained in plain English. Copy it, replace every `{{PLACEHOLDER}}` with an id from your register,
delete what you do not need, and run:

```bash
python harness/proposal_impact.py my-proposal.toml --no-store
```

New things get a provisional id of your choosing, such as `new-contract-quote`, so nothing collides
with an id your register already holds. knowgov never mints a register id: your register's own pull
request gives the real one. To find the ids to reuse, ask an assistant to call the MCP tool
`register_nodes`, or run `python harness/register_nodes.py` with a kind, a taxonomy or an owner.

## Feeding your prioritisation, and planning refinement

knowgov does not rank your work. Your team already has a way to choose what comes next, such as WSJF,
cost of delay or RICE. knowgov supplies some of the facts that method asks for, each with its
denominator, and never a score. It also tells a team, slice by slice, what stands between a slice
and your definition of ready.

The commands below run on the public example instance (`python tools/example_instance.py <folder>`),
with its subject at `KG_SUBJECT`. On your own instance, name your subject, your journeys and your
dates instead.

### The inputs knowgov gives your method

**Time criticality: what lapses, and what a change reaches.**

- Reviews that lapse before a date. Read the gate as of that date, such as the end of the next
  sprint. Every review whose currency runs out by then is a `lapsed` finding, with its key, its
  owner and the day it lapses:

  ```bash
  python harness/gate_cli.py --task codegen --as-of 2027-01-31 -f json -o gate-2027-01-31.json
  ```

  `python harness/capture.py due --on 2027-01-31 --out due/` writes the questionnaires that would
  renew the people's answers falling due by then.
- What a change reaches. For a proposal, the report's "reach" says which products and journeys each
  reused node reaches, before and after. For a node that already exists, ask an assistant to call the
  MCP tool `register_impact`, or run your register's own walk:
  `python register/tools/impact.py --from CAP-0002`.

**Risk: what is not known yet.**

- Keys the gate reads as absent (nobody has stated them), as a declared gap (someone said nobody
  knows), or as disputed (two sources disagree). Each is a finding in the gate report, with the unit
  that owns the key.
- For a product, the capabilities it requires that its journeys' steps do not reach. The proposal's
  slice map lists them as `required_not_reached`: enablers that nothing in the slices delivers yet.

**A job-size proxy: how much is new.**

For each slice of a proposal or a journey, the slice map counts:

- the new elements against the reused ones;
- the gaps;
- the owners;
- the handoffs, where ownership changes along the thread.

```bash
python harness/proposal_impact.py --scope JRN-0001 --task design --as-of 2027-01-31
```

These hint at size. They are not an estimate of effort.

**Dependencies: what must happen first.**

- What each new node rests on, through the register's `realisers` chain. A capability that nothing
  realises yet is shown as a gap.
- Approval order. Your register's checker refuses an approved link whose ends are not approved, so a
  node is approved before the links that name it.
- Owners. The report lists which unit must approve each new node and link. A link whose two ends
  have different owners needs both of them, which is often the cross-team dependency.

**What knowgov does not supply.**

Business value, user reach, confidence in that value, and effort all come from your team. A key's
level is confidence in the *knowledge*, how well what the documents say is checked, not confidence
in the *value* of the work. A slice whose keys are all approved can still be the wrong thing to
build.

### Planning refinement: getting slices to ready

Before refinement, read each slice under the task classes your definition of ready asks for: first
`design`, then `codegen`. Read them as of the refinement date:

```bash
python harness/proposal_impact.py --scope JRN-0001 --task design --as-of 2026-12-01
python harness/proposal_impact.py --scope JRN-0001 --task codegen --as-of 2026-12-01
```

Until task-0252 lands (in flight, for 0.9.0), the per-slice `design` reading counts the keys the register map puts on the slice, not the `design` task's own keys; for `design`, read the subject's gate instead: `python harness/gate_cli.py --task design --as-of 2026-12-01`.

Every key below the task's bar becomes a refinement item for the person who can move it. What the
item is depends on the key's level:

| The key reads | The work | Owner | Route |
|---|---|---|---|
| absent | elicit it | the key's owner unit | the owner's questionnaire: `harness/capture.py questionnaire`, then `ingest` |
| declared gap | a decision that closes the gap | the unit named as `closer` in the gate report | a review file that closes the gap: `harness/capture.py review` |
| disputed | a ruling on which source is right | a reviewer who is not the author | a review file: `harness/capture.py review` |
| invalidated | reconfirm it against the changed document | the key's owner unit | the owner's questionnaire, then a review |
| proposed | a four-eyes review | a reviewer who is not the author | a review file: `harness/capture.py review` |
| validated, but the task asks for more | verify it (a test) or approve it (a review) | the key's owner unit and a reviewer | a suite scenario in the subject's `[verification] map`, or a review file |
| lapsed by the end of the sprint | renew the review | the person who answered, or the owner unit | `harness/capture.py due`, then `ingest` |

Two more items come from the slice map, not from a key:

- **A step that reads "0 of N" keys.** No register-map row lands on the slice, so nothing says what
  knowledge it needs. The item is to define that knowledge: rows in `register_map.toml`, and the
  keys in the task class.
- **A coverage gap.** The report's coverage lists a step nothing supports, or a capability nothing
  realises. The architecture owner models the missing link in the register.

To track progress, read again as of a later date and compare. Keep a report with `-o`, then read
with `--baseline`: the gate exits 1 only on a key that got worse, so the comparison shows what moved:

```bash
python harness/gate_cli.py --task codegen --as-of 2026-12-15 --baseline gate-2026-12-01.json
```

The report names what the gate decided on: the task table (`task_profile`), the register (`register`:
its tag, its commit and `files`, a digest of the register files a load reads: those its own loader opens
and the issued-handles list, never a README or a stray file), the knowgov build (`knowgov`), the
documents loaded (`corpus`, a digest of every document version's bytes), the subject's `[verification]`,
`[provenance]` and `[capture]` as the load read them (`attestations`), the answers and reviews the load
applied (`captures`) and the date (`as_of`). The load records `attestations` and `captures` in the store,
so a read of the store, the MCP reader's included, names the load's own. Under `--baseline`, each one
that differs from the baseline's is listed in the report's `baseline.differs` and named on stderr, one
line each, so the comparison above names its `as_of`, and an edited document names `corpus`. The MCP
reader's `gate_verdict` carries the same `baseline.differs`. Naming one never changes the exit. A
baseline kept before a field existed says nothing about that field, and none is named; a part of the
register or build that either side does not know is never named either.

To see every step against every scenario at once, run the scenarios into a folder and read it with
`python harness/step_grid.py <folder>`: one row per step, one column per scenario, the lowest level
and the counts in each cell (`demo/README.md`, "What exists, step by step").

## Checking a document before the load

```bash
python tools/preload_check.py /path/to/your/instance
python tools/preload_check.py /path/to/your/instance --changed artefacts/plantuml-models/quote_flow.puml
python tools/preload_check.py /path/to/your/instance --since origin/main
```

In plain English: this runs, for each document under `artefacts/<kind>/`, the linter the
programme's table names for its kind (the `lint` field of `instance/kinds.toml`), when that
linter can run here. Six kinds are checked today (each kind's `lint.runs`):

| kind | linter | its configuration, unless your instance root has its own |
|---|---|---|
| `plantuml-models` | pumllint | pumllint's own |
| `api-contracts` | Spectral | `instance/ci/spectral.yaml`: the built-in OpenAPI and AsyncAPI rules; yours: `.spectral.yaml` |
| `specification-prose` | markdownlint (markdownlint-cli2) | `instance/ci/markdownlint.jsonc`: the defaults less line length and table column style; yours: `.markdownlint.jsonc` or `.markdownlint-cli2.jsonc` |
| `acceptance-scenarios` | gplint | `instance/ci/gplintrc`: the structural rules only; yours: `.gplintrc` |
| `bpmn-process-models` | bpmnlint | `instance/ci/bpmnlintrc`: `bpmnlint:recommended`; yours: `.bpmnlintrc` |
| `decision-tables` | dmnlint, `.dmn` files only | `instance/ci/dmnlintrc`: `dmnlint:recommended`; yours: `.dmnlintrc` |

Every other kind's files, a decision table that is not a `.dmn` file (CargoQuote's
`decision_table.md`), and a kind whose linter is not installed where the check runs, are listed
as *UNCHECKED*, with the tool (or "names no linter"), so the gap stays in sight; an unchecked file
does not fail the check, and it is never passed quietly. Each linter's errors count as `major`,
its warnings as `minor`; bpmnlint and dmnlint name the model element, not a line. The Node
linters are found on `PATH`, or at `KG_SPECTRAL`, `KG_MARKDOWNLINT`, `KG_GPLINT`, `KG_BPMNLINT`,
`KG_DMNLINT`. Not added: Vale, which the table names beside markdownlint, because it ships no
rules of its own (a style is an organisation's choice, fetched by `vale sync`); add it as a step
of your own with your styles. Without
`--changed` or `--since` it checks every file; with them, only the files named, or changed since
that git reference. It exits 0 when every checked file is clean, 1 when one has a finding at or
above `--fail-on` (default `major`, pumllint's own), and 2 when it cannot run: a linter that is
installed but fails, a folder that is not a kind, a named file that does not exist. `-f json` prints the
report under `harness/schemas/preload-report.schema.json`. The linter runs with your instance as
its working directory, so your own configuration applies.

**Checks across documents.** After each kind's own linter, the check runs three checks that read
several documents together. They are step 4 of reverse engineering (decision-0018). Each finding
names its check as its `tool`, and the report's `checks` block says whether each check ran.

| check | reads | finds |
|---|---|---|
| `pumllint trace` | `plantuml-models`, `acceptance-scenarios` (`.feature`), `textual-requirements` | a requirement no diagram realises; one modelled that no feature references; a diagram or feature citing an id no requirement holds (`major`); a diagram, feature or scenario citing none |
| `glossary` | `textual-requirements`, `glossary` | a term (a code span or a bold phrase) in three or more requirements with no glossary row |
| `dmn gaps` | `decision-tables` (`.dmn`) | input values no rule matches; rules that overlap under hit policy `UNIQUE` (`major`), or under `ANY` with different outputs; an output with no type, or a rule leaving one empty |

- **What the trace needs.** It runs the same pumllint as the `plantuml-models` check, the version
  the harness pins. That must be **0.35.0 or later**, the first release whose `trace` reads
  `--features`. It also needs the requirement-id pattern in a `pumllint.toml` at your instance's
  root: `[rules.requirement-link]` with `pattern = "REQ-\\d+"`, say.
- **When it cannot run.** With an older pumllint, or without a pattern, the trace is listed as
  *unchecked* and says which of the two is missing. A check whose documents your instance lacks is
  unchecked too: the glossary check with no glossary, say.
- **Documents no linter reads.** A document whose kind has no linter here, but which a check read,
  is judged by that check alone: your requirements under the trace and the glossary check, a
  `.dmn` file when dmnlint is not installed. Its row says so.
- **Through the load.** Each finding reaches the load as any linter's does, and becomes a gap
  with an owner and a route (task-0216).

The example instance shows what a first run finds. Its prose and Gherkin are clean under the
shipped configurations. Its BPMN model (`quote_process.bpmn`) has no diagram interchange and no
`incoming`/`outgoing` references on its nodes, so `bpmnlint:recommended` reports 97 errors on it.
Its screening table is clean under dmnlint, but the DMN check finds two gaps in it, both `minor`.
Its `risk_index` is a `number`, and the rules stop at 41 and resume at 42, and again at 66 and 67,
so a value such as 41.5 matches no rule. These are real findings about the documents, not faults
of the check: adopt over them with a baseline (below), or fix the documents.

To run it on every pull request, copy `instance/ci/preload-check.yml` into your instance's
`.github/workflows/` from the knowgov tag you run (its `KNOWGOV_REF` defaults to that tag), and make the job a required check with
a reviewer who is not the author. It lints the documents the pull request changes, then runs
`tools/check_instance.py`; the script it calls, `instance/ci/preload-check.sh`, is the one this
repository's CI runs on the example instance (`tools/check_preload_linters.py` for the Node
linters: a clean file of each kind exits 0, a broken one exits 1). It installs the linters the
check runs, pinned (`PUMLLINT`, `SPECTRAL`, `MARKDOWNLINT`, `GPLINT`, `BPMNLINT`, `DMNLINT`); drop
the install of a kind you do not hold. Your other linters (Vale, StrictDoc, buf...) go in as steps
of their own before it. The load reads only what was merged.

**What it does not do.** It checks *form*, one file at a time: is this a well-formed document
of its kind? It does not check *knowledge*. Two well-formed documents that disagree, or a fact
nobody wrote down, pass it. That is the knowgov gate's question, `harness/gate_cli.py`, after the
load; neither replaces the other. And both pass documents that are consistently wrong.

**Keeping the verdict with the documents.** Commit the report of the merged tree as
`preload-report.json` at the root of your instance (or set `KG_PRELOAD_REPORT` to its path).
Every load then records on each document version what the report said about those exact bytes:
tool, version, state and digest. A document the report does not cover, or one edited since it
was checked, is recorded as *unchecked*, never as clean. The page's ingest panel shows the verdict
per document. The gate lists the documents behind a task's keys whose form was unchecked as `info`
findings, which change the exit only under `--fail-on info`. Each finding the report holds on such a
document is listed too, as a `lint` finding at the linter's own severity, at most `major`. It drops
to `info` when your baseline holds it or a review has resolved it. So a document with a major
finding changes the exit under `--fail-on major`, though never at the default `blocker`. Without a
report, nothing is recorded.

**Starting from documents that already have findings.** Run the check once with
`-o preload-baseline.json`. Committing that report is your decision. From then on,
`--baseline preload-baseline.json` (set `KG_PRELOAD_BASELINE` in the CI template) lists every
finding the baseline holds as *HELD* and fails only on a new one, or on the same one at a worse
severity. A finding is the same when its file, rule and message are, wherever its line moves. The
check never writes the baseline and refuses `-o` naming it: you move it on with a reviewed commit
after a clean-up, never from inside the check.

## Trying it with public content first

```bash
python tools/example_instance.py /tmp/example-instance
```

In plain English: this builds an instance from the public test case, ieam-register's register
plus CargoQuote's documents, sorted into their kinds. It then runs the check on it. It writes
only into the folder you name. The demo's CI mounts that folder read-only, replays a scenario,
runs one deterministically, and confirms afterwards that not one byte of the folder changed.

## Who vouches for a document

Each statement knowgov holds has a *status*: proposed, then validated, verified and approved, the
last being the highest. For a statement taken from a document, the status says who has vouched
for it, and the gate relies on it to decide whether an assistant may build.

Some documents hold statements a person wrote down as fact: requirement text, the links between
documents, a decision table's rules. A mapper reads them as *authored*. knowgov treats them as
reviewed and approved only when your subject says who vouches for them (decision-0009). The
declaration goes in `subject.toml`:

```toml
[provenance]
human = { id = "agent:employee-2", name = "employee-2" }   # who attests: an issued handle, never a name

[verification]
authored = { at = "2026-11-04", scope = "reviewed by employee-2 against the process owner's notes" }
approval = { at = "2026-11-04", record = "minutes/2026-11-04-requirements.md" }
```

In plain English: `[provenance] human` says who attests, `authored` says when they reviewed the
documents and what they read them against, and `approval` says where the approval is recorded.
Declare them only for documents that person has in fact read. Put them in a pull request that
someone other than its author reviews.

Without `authored`, those statements load as *proposed*, and the gate lists them below verified.
Without `approval`, nothing is approved, not even statements a test has verified. A new subject
whose documents nobody has vouched for is therefore blocked, or at best qualified, until a person
does. That is on purpose: a requirements file drafted with an assistant and read by nobody must not
reach the gate as approved. The layout check notes such a subject (*NOTE [verification]*), naming
its documents with authored statements. One limit remains. A declaration covers the documents as
they are at each load, so after an edit, re-read the documents before the next load, or remove the
declaration until someone has.

Since 0.9.0 a declaration can name the versions it covers (decision-0019). List in `versions` the
digest of each document version the person read: a file's SHA-256 over its bytes, and for a folder,
the SHA-256 of each file in it.

```toml
authored = { at = "2026-11-04", scope = "...", versions = ["3f2a...", "9c41..."] }
approval = { at = "2026-11-04", record = "...", versions = ["3f2a...", "9c41..."] }
```

In plain English: once a document changes, its new version is no longer listed. Its statements load
as *proposed* again, and nothing in it is approved by the declaration. The gate names the document
and the keys resting on it, and the route back: the person reads it and adds its new digest. The layout
check refuses a digest that matches none of your documents. A declaration without `versions` keeps the
old meaning, covering whatever the documents hold at each load; the gate lists it at info and the
layout check notes it.

A test's result and a review are bound the same way, with no old meaning to fall back on (decision-0036,
0.9.0). No suite runs when the documents load. A verification by execution is the result your subject
attests, and it holds only for the document versions listed under `execution`. The verification's `at` is when the load recorded the attestation, not when a run happened; the run is identified by its digests (the document Versions, the implementation and the suite). A review holds only for
those listed under `review`:

```toml
execution = { versions = ["3f2a...", "9c41..."] }   # the versions the suite's result was attested on
review = { at = "2026-11-04", scope = "...", versions = ["3f2a...", "9c41..."] }
```

A test's result also depends on the code it ran and on the tests that judged it. `execution` lists
the raw-byte digest of each file of the reference implementation (`[reference] code`, its `*.py`
files for a folder) under `implementation`, and of the suite (`[oracle] script`) under `suite`
(decision-0038):

```toml
execution = { versions = ["3f2a...", "9c41..."], implementation = ["5b0e..."], suite = ["77d1..."] }
```

If your suite's script reads its expectations from other files, name them in `[oracle] suite`
(decision-0039). Each file's digest then belongs in `suite` beside the script's. A folder counts
as all of its files. Without the field, `suite` binds the script alone, and a change to the
expectations moves no digest:

```toml
[oracle]
script = "tests/run_suite.py"
suite = ["tests/expectations.py"]

[verification]
execution = { versions = ["3f2a..."], implementation = ["5b0e..."], suite = ["77d1...", "a4c8..."] }
```

Change a helper, weaken a test or edit an expectation `[oracle] suite` lists, and nothing is verified
by execution until the suite has run again and the new digest is listed. The gate names the changed file at `major`, and the layout check names
it as an error. A subject that declares the code but lists no digests verifies nothing by execution;
the layout check warns and prints the list to add.

In plain English: edit a document and its statements fall below *verified*, and out of approval, until
you run the suite or the review again on the new version and add its digest. An `execution` or a
`review` that lists nothing verifies nothing, and the layout check notes it, as it notes a subject
whose verification map names suite scenarios but declares no `execution`.

Each declaration needs its own `at`, and `[provenance] human` needs an `id`. A stage-2
re-verification in `scenarios.toml` needs its `at` too. The layout check refuses a declaration
without them (*ERROR attestation*). A load applies none of them and says so. Before 0.9.0, a
missing `at` was dated by each load's own day, so the review never lapsed, and a missing attester
was recorded as `agent:maintainer`.

## Capturing what people know

Some knowledge is in nobody's documents, only in people's heads. The gate then reports a key as
*absent* or as a *declared gap*, and it blocks. The capture path turns that into a recorded
statement, without anyone having to write a document first.

```bash
python harness/capture.py questionnaire --scenario S2 --out questionnaires/
```

In plain English: this loads the scenario into a private copy in memory, asks the gate which keys
are missing or weak, and writes one questionnaire per *owner*: the organisation unit your register names as owner of the
building blocks each key concerns. When several units own those building blocks, give the key's
row in `register_map.toml` an `owner`, one of them, and only that unit is asked; otherwise each
of them is, and two people may answer the same key. Each questionnaire says how many keys the owner has and how
many need an answer. For each one it shows what the store holds now and asks one question. A key
no register row covers goes to a questionnaire named `unassigned`, so nothing is dropped.

The private copy is the point: the store your page and your assistants read (Neo4j in the stack)
keeps the scenario it holds, so an owner can run this while others are reading, and nothing they
see changes. The copy needs the harness's Python packages (`pip install -r demo/requirements.txt`;
inside the stack's container they are there already); without them the command says so and exits 2.
`capture.py review` and `harness/transcript.py` load the same way.

The owner fills it in: a value in `answer`, or `nobody_knows = true` when no one can say. They
add their *handle* and the date under `[answered]`. A handle is a short lower-case label such
as `employee-1`, never a name or an e-mail address, and one your register has issued (its
`people/handles.toml`, ieam-register decision 0009). A `note` must not identify them either: no
name, no role only they hold, nothing like "as the author of the 2025 memo". The note travels with
the answer into everything that reads it, and no check can tell an identifying note from a harmless
one; only the reviewer reads it (below). Then:

```bash
python harness/capture.py ingest questionnaires/questionnaire-cargo_quote-S2-ORG-0002.toml
```

In plain English: this checks the answers and refuses a name in place of a handle, a handle the
register has not issued (or issued only after the answer's date, or withdrawn by then), a handle
issued without the role `gives` (one that may only approve or close cannot answer), a date in the
future, or an item that has both an answer and "nobody knows". It then saves them in the
subject's `captures/` folder, which you commit like any other change. From then on, every
load reads that folder. An answer becomes a statement *proposed* by that person on that date,
and a "nobody knows" becomes a declared gap with their handle and the date. Neither goes further
on its own. A proposed statement is still below verified, so the gate lists it as an assumption
an assistant must state. If the key already holds a validated (or better) statement from your
documents, an answer nobody has reviewed yet does not lower it: the gate leaves it out of the key's
level and marks it *pending review* in what the assistant reads (knowgov decision-0004). So a
pipeline that runs `gate_cli.py --baseline record` stays green after a capture that agrees with the
documents or fills an absent key, and fails after one that contradicts them, since the key is then
disputed until a reviewer settles it. Nothing the harness does verifies a person's answer, nor a model's
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

The file the command saves records what each ruling ruled on, as the store held it: the
statement's `key`, its `value`, and `sha256`, a digest of the document text it was read from. A
close records the `sha256` of the gap's declaration. Every later load binds each ruling to the
statement that still holds that content, whatever its id is now. If a table's rows were reordered
or answers were renumbered, the ruling follows its content. If the statement was edited, or is no
longer in the documents, the ruling is not applied. The rest of the review still is. The gate then
lists an `act` finding, `major`: it names the review, the person who ruled, the value they ruled
on, what the documents say now, the key's owner and the route to a new ruling. For a ruling on a
captured answer the file also records `giver`, the handle that gave the answer, read from the capture
file's own content (its `from`), never from its file name. The ruling binds only to that person's
answer. So two issued handles such as `ops` and `ops-2` never stand in for each other, even when
`ops`'s second capture of a day and `ops-2`'s first have the same file name. A review saved without
`giver` binds as before, and a ruling whose answer's file name could be either person's is set aside
(decision-0038). A review saved
before 0.9.0 has no `key`, `value` or `sha256`. It still binds by id, as it did, and the gate lists
it at `info` as bound by id only. A new review binds it to content.

Two reviewers who rule on one statement the same day, one approving it and the other rejecting or
referring it, cancel each other: within a day there is no "later", so neither ruling is applied and
the statement keeps the status it had. The gate lists an `act` finding, `major`, on each of those
rulings; every one names every file of the set. `capture.py review` says so on stderr before it
writes such a ruling (it still writes it). To clear it, the owners rule again in one review, on a
later day. When that ruling approves or rejects, the findings read `info`, "settled by" that file, and
the key reads from it; a referral decides nothing and leaves them `major`.

Before ruling, read what you rule on:

```bash
python harness/capture.py review review.toml --show
```

In plain English: this prints each answer the review rules on, with the note that came with it,
and writes nothing. Check that no note names or points at the person who gave it. If one does,
reject that statement and ask for the answer again without the note: a capture is never edited,
so the corrected answer is a new capture. Nothing else looks at a note.

Then rule:

```bash
python harness/capture.py review review.toml
```

In plain English: this loads the scenario into a private copy, as the questionnaire does, checks
the review against what that copy holds, and
saves it in `captures/reviews/`. Every later load of that scenario applies it. An approved
statement counts as *approved*; a rejected one, whether a person's answer or a document's
sentence, stops counting but stays on record; a closed declared gap stops blocking. With every
key approved or verified, and none flagged, the gate says PROCEED. A task class that sets
`require_approved = true` (the [subjects guide](../subjects/README.md)) needs every key approved.

Who may do what comes from your register's list of issued handles (`people/handles.toml`), never
from the review itself, and the command refuses a review that breaks a rule, naming it:

- **Approving an answer** needs the role `approves`, in a unit that owns the key, and never the
  handle that gave the answer.
- **A model's statement** (basis inferred, assumed or hypothesised) may be rejected or referred,
  never approved: whoever reviews it, it is not promoted.
- **Overruling a document**, rejecting or approving one of its statements, needs the role
  `closes`. So does **settling a dispute**: the review must rule on *every* side, approving what
  is kept and rejecting the rest, and what it keeps must agree. Approving one side alone is refused,
  and the key stays disputed.
- **Closing a declared gap** needs `closes`, in the unit the declaration names as its owner (or,
  when it names none, a unit that owns the key). If the declaration names an owner your register
  has no unit for, nobody can close it until the register has that unit and a handle of it.
  The example register has one since its v0.2.6: CargoQuote's OD-1 names compliance, which is
  ORG-0004 there (a stand-in, its decision 0011), and only `employee-4` of that unit closes it.
- **An approved answer lapses** six months after it was given: the statement reads *proposed*
  again until someone re-asks and a reviewer approves again. The gate decides this on the date it
  reads (`--as-of`, today by default), never on the day the store was loaded, so one `--as-of` gives
  one answer whatever day you run it (task-0198). Set `KG_TODAY=YYYY-MM-DD` for a reproducible today,
  and `KG_CLOCK=pinned` in a pipeline so a command that would read the wall clock fails instead
  (task-0075).

**When a document's review falls due.** A statement a document's review verified is current for
the review months of the kind its key concerns, from your register's `metamodel/lifecycle.toml`:
`[review.kinds]` (the example register: capability 12, product 6), the shortest among the nodes
the key's row in your subject's `register_map.toml` names, else `[review] default_months` (knowgov
decision-0005). The load writes that date as the verification's `valid_until`. From the next day the
statement reads *validated*, its approval with it, and `gate_cli.py` lists a *lapsed* finding (major).
Read as of today, which is the default, your `--baseline` pipeline then reports the key as
`verified -> validated`, a regression. Renew it by a review: a reviewer of an owning unit approves the
statement in a review file, as above (a document's statement needs the role `closes`), and it is
current again for the key's months from the review's `on`. A statement a review file approved with no
verification at all lapses the same way, the key's months after the review's `on`. A verification by
execution does not lapse by date. `--as-of YYYY-MM-DD` reads as of another
date, to see what falls due when; `--as-of record` reads as of your subject's `[record] as_of`, if you
pinned one. What is dated after the date read does not count yet: read as of a day before a review, the
statement reads as it did before it, and the *lapsed* finding says why.

A review copied into `captures/reviews/` by hand is checked again on every load: one that breaks
a rule is skipped, and the load prints why. The rules are knowgov's decision-0002; the handles
and roles are ieam-register's decision 0009. `tools/check_review_walkthrough.py` runs the
whole path on the example instance.

**Asking again when an answer falls due.** What a person said is due for review six months after
they said it (ieam-register decision 0008). To ask again:

```bash
python harness/capture.py due --out questionnaires/
```

In plain English: this finds every captured answer given six months ago or more, the latest per
person and key (one a review rejected is not asked again), and writes one questionnaire per handle,
each answer pre-filled with what they said and when. The person keeps an answer to confirm it,
changes it to correct it, or empties it to skip it, then fills `[answered]` and you ingest it as
before. A confirmation is a new capture on the new date, which restarts the six months; a change
is a new statement beside the old one, for a reviewer. The earlier capture is never edited. If a
handle has been withdrawn (the person left), its answers go to the owner unit instead. The command
also lists any register link carrying an `elicited` block whose `review_due` has come: those are
reviewed in the register, not here. `--on YYYY-MM-DD` (or `KG_TODAY`) sets the date it counts to.

**Starting from a conversation.** If someone has talked through what they know (a recorded
interview, meeting minutes), a model can read the transcript and suggest answers:

```bash
python harness/transcript.py interview.txt --scenario S2
```

In plain English: this asks the model your instance names (the same endpoint and key variable as
the arms) what the transcript says about each required key the store holds nothing on. Its
suggestions are saved in `captures/inferred/` and load as the model's *proposed* statements:
never more, since nothing verifies or approves a model's statement. The next questionnaire shows
them under `known`, and only the person's own answer, ingested as above, becomes what they said.
The transcript itself is never kept: the file records its fingerprint (SHA-256), the model and the
date, not its text. A key your documents already state is not offered to the model, so a guess
never lowers it. Without a model key the command refuses to run (exit 2).

**The register's capture fields.** The three fields a capture carries are `from` (the handle),
`on` (the date) and `record` (where the answer is kept). They are the fields ieam-register's
[decision 0008](https://github.com/fdurieux/ieam-register/blob/main/decisions/0008-knowledge-a-person-gave.md)
adds to the register for a link that rests on what a person said, with a review due within six
months. The register's other required capture fields were there before: a link's `rationale`,
an exception's `rationale` and expiry, and the decision record every approval names.

## Sizing the Neo4j heap

On Neo4j, a load runs as one transaction: everything it writes, and everything it deletes when it
clears the previous load, stays in the server's memory until it commits. So the server's
*transaction memory* has to hold your largest load. The platform checks this before it loads.

**What a load needs.** Measured on Neo4j 5.26 (`docs/load-memory.json`), each statement a load writes
costs about 9.4 KiB, and each one it deletes about the same. A *statement* here is an assertion
or a fragment, the units the documents are read into. With a 25% margin, the transaction memory
a load needs is about

    1.25 × (24.4 MiB + 9.4 KiB × statements written + 9.4 KiB × statements deleted)

- A published gate load (`harness/gate_cli.py --publish`, or `KG_PUBLISH=1` for the CI script)
  replaces the previous load, so for a scenario of *N* statements it writes *N* and deletes about
  *N*: roughly 30.5 MiB + 23.4 KiB × *N*. Without `--publish` the gate loads into a private copy in
  memory, which never touches Neo4j.
- A full run (`harness/run.py --deterministic`, or the page's Deterministic and Arms buttons) loads
  every scenario in one transaction, so it needs the sum over the scenarios.

To get your subject's figures, run this from your knowgov checkout:

```bash
KG_SUBJECT=/path/to/your/instance/subjects/<id> python harness/load_memory.py
```

It prints each scenario's statement count, what a gate load and a full run need, and the heap that
holds them. It reads only the documents; it needs no database.

**Which settings.** Neo4j limits transaction memory three ways, and the smallest one that is set wins:

| Setting | Default | What it bounds |
|---|---|---|
| `dbms.memory.transaction.total.max` | 70% of the heap | all transactions on the server |
| `db.memory.transaction.total.max` | unset (`0B`) | all transactions on one database |
| `db.memory.transaction.max` | unset (`0B`) | one transaction |

With the defaults, only the first applies, so the heap is what you size: at least the transaction
memory your largest load needs, divided by 0.7. In the stack that is `NEO4J_server_memory_heap_max__size`
in `demo/docker-compose.yml` (1 GiB, so about 717 MiB of transaction memory). Some examples:

| Statements in your largest scenario | A gate load needs | Heap (defaults) |
|---|---|---|
| 1,500 (the public J-F subject) | 65 MiB | 1 GiB is ample |
| 10,000 | 260 MiB | 512 MiB |
| 50,000 | 1.2 GiB | 2 GiB |
| 100,000 | 2.3 GiB | 4 GiB |

A full run of several scenarios needs more, as `harness/load_memory.py` prints.

**When a load would not fit.** It is refused before it writes anything, so the store keeps what it
held. A run, and a gate with `--publish`, exit 2, and the message names the setting and both figures, for
example: *the server allows 717.0 MiB (dbms.memory.transaction.total.max = 717.00MiB)*. Raise the
heap, or the setting it names.

- The forecast is deliberately on the high side. A full run in particular can be forecast at up
  to about twice what it uses.
- If a load is refused that you believe fits, set `KG_LOAD_MEMORY_CHECK=off` to load anyway. A
  load that then does not fit fails inside its transaction, and the store still keeps what it held.
- `KG_LOAD_MEMORY_MARGIN` (0 to 4, default 0.25) sets the margin.
- The rdflib store has no transaction memory, and is never refused.

## Starting the demo on your instance

```bash
cd demo && KG_INSTANCE=/path/to/your/instance docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.instance.yml up -d --build --wait
```

In plain English: the same stack as the demo, with your folder mounted read-only at `/instance`.
The page reads your register (`/instance/register`) and lists your subjects
(`/instance/subjects`), and none of the public ones. Leave `-f docker-compose.override.yml` out
to pull the published image instead of building it. One stack serves one instance.

The page keeps its list of subjects current while it runs. A subject merged into your instance's
`subjects/` folder appears in the page's subject menu the next time anyone opens or uses the page,
with no restart; a subject you delete disappears the same way. A subject whose `subject.toml` cannot
be read is left out of the list, and the page's log says why, while the others stay available.

## Letting an AI assistant ask the gate

An AI coding assistant can ask knowgov the gate's question itself, before it writes anything:
*may I build on this?* It does so through MCP, the Model Context Protocol, a standard way for an
assistant to call tools a local program offers. `harness/mcp_server.py` is that program. It offers
seventeen tools, and all of them only read:

| Tool | What the assistant asks | What it gets back |
|---|---|---|
| `store_status` | What does the store hold? | the subject, the scenario loaded and when it was loaded (`loaded_at`), the task classes and their required keys, the date the server reads reviews on, and which knowgov the server runs (`knowgov`: its version, commit and distance from the release); one store serves every subject, so a scenario another subject loaded reads as none loaded, named in `held_by_other_subject`, and every tool that reads a scenario refuses until your subject's is loaded |
| `gate_verdict` | May I build on the knowledge this task needs, or on these keys? | PROCEED, QUALIFIED or BLOCKED with the findings: the same report `gate_cli.py --no-load -f json` prints |
| `three_valued_answer` | What is known about this one key? | asserted, documented absent, or unknown, with where each statement came from and who verified it; and any statement a document change invalidated, with `superseded_by` naming the verified or approved statement that replaced it (none: the old value no longer holds and nothing does yet) |
| `evidence_bundle` | What exactly may I build on, and on what evidence? | the evidence bundle the governed arm reads, as text: the verdict and the policy, every required key's statements with their evidence, verifications, approvals and gaps, lapsed reviews, invalidated statements and what supersedes them, unchecked or flawed documents behind the keys, suspect derived outputs, and the documents the task names verbatim; for a task or for your own keys |
| `register_impact` | What does retiring or changing this register node touch? | your register's own impact walk from the node (the register's tag and commit, the node, its children listed but not walked unless the assistant asks with `children`, which walks every approved descendant as the register's decision 0014 does, every edge with whether it was followed, what it reaches with each node's owning unit), and the keys your subject's `register_map.toml` places on the node or on what it reaches, each with its owner, its anchor and the node it came through; with `children`, the keys resting only on a descendant not followed are listed last, flagged `not_followed`; with a scenario loaded, each key's level, stale statements and suspect derived outputs as `gate_verdict` reports them for the task class the assistant names with `task` (`codegen` by default); while a run loads the store, refused where it would read those levels |
| `proposal_impact` | What would this proposed product, capability or journey touch, and what does it lack, before anyone approves it? | the proposal (new nodes with provisional ids, links, the register nodes it reuses as they are or changed, proposed exceptions) read by your register's own checker and walks as if approved, every proposed element marked `hypothetical` and nothing stored: placement findings (a forbidden synonym; a node in no tool yet), link candidates D1 to D4 each `authored` or `inferred` and never more than `proposed`, coverage by every rule the register's checker defines (C1 to C4 at v0.2.13) before and after with the new gaps, what each reused node reaches before and after, what each new node rests on, each reused node's keys as `register_impact` reads them, the new nodes left unmapped, and which unit must approve what; while a run loads the store, refused where it would read the reused nodes' levels. Its walkthrough is in `demo/README.md` |
| `register_nodes` | Which register nodes are there, and what does this one sit under? | your register listed from its files, with no store: every node with its kind, name, state, owner and parent, filtered by taxonomy, kind, state, owning unit or parent (`null` for the top-level nodes), with the total and a limit; "what does ORG-x own" is this listing, since ownership is shown and never walked. With `node`, that node's lineage: every ancestor up to the root and its children with their states, named and never walked; for what rests on or implements a node, `register_impact` |
| `key_nodes` | Which register nodes does this knowledge key concern? | the rows of your subject's `register_map.toml` on the key, each with the register nodes it names (kind, name, state, owner), the row's owner, anchor and note; a key your subject knows with no row reads `mapped: false`, one it does not know is refused. Read from files, no store |
| `code_path` | Which application is this code file, which keys does it cite, and what was it built from? | for a path under your `code_map.toml` root: the application or module the map assigns, the keys the file's `knowgov-keys:` header cites (an unknown one flagged), and the trace ledger's entry for it (derived id, commit, digest, its statement ids and keys, sorted, and its `state`: `current`, `drift` when the file changed since it was registered, or `missing`, as `trace.py check` reads it), and whether it is `suspect`, read from the store while the store holds your subject's scenario, else `unchecked`. Each part says `read` or `unchecked` with why: unchecked means not read, never empty. Read from files, and from the store for the ledger entry's `suspect` when it holds your subject |
| `document_links` | Which register links cite this document? | the links of your register whose evidence cites the document (a path of your export manifest), each with the evidence anchor, the link's type, state and owner, and the nodes at both ends with their owning units: what the Browser's `register-cites` query shows, read from the register's files, no store |
| `held_keys` | Which keys does the loaded scenario hold, and how sure is each? | every key a statement of the loaded scenario names, with how many statements it has in each status, its level as `gate_verdict` reads it under the task class the assistant names (`codegen` by default), the task classes that require it (none, for a key no class asks for: `store_status` lists declared keys only, so these were invisible before), whether your register map places it, and the required keys the store holds nothing on; refused while a run loads the store |
| `derived_outputs` | What was built on this key, or what is this output built on? | with `key`, every derived output (code registered by `trace.py register`, a governed run's output) that used a statement on the key, in any state; with `derived`, that one output; each with the statements it used, each read `live`, `stale` (invalidated and nothing settled replaces it), `superseded` (with the verified or approved statements that replace it) or `rejected`; refused while a run loads the store |
| `document_statements` | What does this document say, and what was built on it? | the statements the loaded scenario holds from a document (an artefact path; a folder by its path ending in `/`), each with its key, value, status, version and the document's fragments it rests on, and the derived outputs that used it; the versions held, and with `version` only that one's; refused while a run loads the store |
| `scenario_runs` | Which scenarios have been run, in which mode, and what did they show? | every scenario of your subject with its title and card line; what the record holds for it (deterministic results and the gate's verdict, the arms with how many runs and which model, the extra sources the subject declares); its runs newest first, each as its folder's `run.json` describes it (mode, model, as-of date, who started it, `page` or `mcp`, start, end, status, and the verdict of its results), or inferred, flagged `inferred`, for a folder from before `run.json`; the scenario the store holds and when it was loaded; and the run loading the store now, if any. Replay is not a run: it is the record shown, and nothing records it |
| `scenario_result` | What did this record or this run show? | what the page's Replay shows for one source that `scenario_runs` lists (the record, an extra source, or a run): the gate's verdict and why, the date it read reviews on, every required key's level, and each arm's runs with its decision and oracle result. It reads that source's files, never the store, and says so: it is not what the store holds now |
| `list_subjects` | Which subjects can I ask about? | every subject under `KG_SUBJECTS` by its id, the scenario the shared store holds for each, and which tools are store-backed; the one tool that takes no `subject` |
| `subject_check` | Would this subject I am scaffolding load, and do its keys match what its documents say? | the report `tools/check_subject.py` prints for the same files, made by that tool's own functions against your register: unknown tables and fields, a task with no scenario, a key that is not `entity\|predicate`, a `register_map.toml` row naming a node your register does not hold or an owner of none of its nodes, and what each document yields, with a *did you mean* for a required key no document yields. The assistant passes the proposed `subject.toml`, `register_map.toml`, `scenarios.toml` and the text of every document the manifest names (by the path the manifest gives, at most `../../` up from the subject folder). A proposed manifest that names a file outside that, by an absolute path or by climbing further, is refused before anything is read. The files exist only for the call, in a temporary folder removed afterwards; nothing is stored. A call carries at most 64 documents and 1 MB of text. It is for an assistant with no shell, such as Claude Desktop; in Claude Code, `tools/check_subject.py` on the branch does the same |

While a run of your subject is loading the store (its `run.json` reads `running` and the page has
rewritten it in the last 120 seconds; it does so every 30), `gate_verdict`, `three_valued_answer` and
`evidence_bundle` refuse and name the run, since a read then sees part of a graph; so do
`register_impact` and `proposal_impact` when they would read key levels from the store (with no
scenario loaded they answer from the register alone, as before). Ask again when it
has ended. A page that stops mid-run leaves a `running` file whose heartbeat goes stale; it no longer
blocks, and the page closes it as failed (`page restarted`) when it starts again.

A call that names an argument the tool does not take is refused with an error naming it, and nothing runs: a misspelt `senario` never reads as no scenario named.

The server reads the store as the page or a run left it. It never loads a scenario and never
writes to the store, the register or your instance; a change to the record is still a pull
request. Load what the assistant should see first, on the page or with a run.

Every tool is offered over stdio and HTTP alike, and the managed allowlist under
`instance/ci/claude/` admits the server by its name, `knowgov`, so a new tool needs no client change.

`code_path` reads two files the server is told about when it starts: your instance, with
`--instance` or `KG_INSTANCE` (its `code_map.toml` and the code under its root), and the trace ledger
`trace.py register` writes, with `--ledger` or `KG_LEDGER`, the same variables the CI wrappers take.
Without one, that part of the answer reads `unchecked`. A path outside the code map's root is refused.
The ledger entry's keys are the ones `key_nodes` takes, so a code file climbs to the register's nodes
in two calls: `code_path`, then `key_nodes` on each key. Whether the entry is suspect is the one part
read from the store, by the rule `trace.py check` applies; `python harness/upward.py code` opens no
store, so there it reads `unchecked`, and so it does from the server when the store holds another
subject's scenario or none.

The tools compose into the whole chain, one named step at a time and never one walk both ways. Down,
from a capability to what it rests on: `register_impact` with `walk: realisers`, then `evidence_bundle`
with the keys it lands on. Up, from a code file to the business: `code_path`, `key_nodes` for a cited
key, `register_impact` with `walk: dependants` from the application (with `children` when its modules
carry the links), then `register_nodes` with `node` for the capability's ancestors. From a document,
`document_links` names the register links that cite it, and `document_statements` what it says and
what was built on it; `derived_outputs` with a key goes on from the knowledge to what was built on it.
The server's own instructions tell the
assistant the same.

The server reads review currency on one date for as long as it runs: `KG_AS_OF` (or `--as-of`), a
date as `YYYY-MM-DD`, `record` (the subject's pinned record date) or `today`, which is the default.
It reads that date once, when it starts, so a session that runs past midnight never sees two days.
`gate_verdict`, `evidence_bundle`, `register_impact` and `proposal_impact` use it unless the assistant names another
date in its call, and `store_status` reports it.

It speaks both versions of the protocol in use: the current stateless one (2026-07-28), where a
client asks `server/discover` and every request is self-contained, and the older handshake
(`initialize`), so an assistant built on either connects without a fallback.

**Which subject it answers for.** The server answers for one subject, the one `KG_SUBJECT` names.
`KG_SUBJECT` is the *path* to the subject's folder (its root, the folder holding `subject.toml`),
not the subject's id: `subjects/cargo_quote` from a knowgov checkout, `/repo/subjects/cargo_quote`
inside the container, never the bare `cargo_quote`. On the public stack it is already set to the
subject the page opens on. On your instance's stack it still names the public CargoQuote subject,
which your page does not list. Start the stack with `KG_SUBJECT=/instance/subjects/<id>` or name
your subject's id in each call (`subject`).

**Which scenario it reads.** The server reads whatever scenario the store holds: the one the page
or a run loaded last. Have the assistant pass `scenario` (for example `"S1"`) in every call to
`gate_verdict`, `three_valued_answer` and `evidence_bundle`: a call that names a scenario the store
does not hold is refused, so an answer about the wrong load never comes back looking right. After
you load another scenario on the page, restart the assistant's connection to the server (quit and
reopen Claude Desktop; `/mcp` and reconnect in Claude Code, or a new session): the server fixes its
review date when it starts, and may keep its connection to the store for as long as it runs.

### Connecting Claude Code, the command-line assistant

**With the stack running** (above), the simplest connection needs no extra port: the assistant
starts the server inside the `app` container and talks to it over standard input and output
("stdio"), the connection it opened. Run this once, replacing `/path/to/knowgov` with the absolute
path of your knowgov checkout (for example `/Users/you/src/knowgov`):

```bash
claude mcp add knowgov -s user -- docker compose -f /path/to/knowgov/demo/docker-compose.yml exec -T app python harness/mcp_server.py
```

In plain English: `claude mcp add knowgov` registers a tool server named knowgov, and everything
after `--` is the command that starts it. Here that command runs `harness/mcp_server.py` in the
`app` container; `-T` gives it plain input and output rather than a terminal, which the protocol
needs. `-s user` registers it for you in every folder; without it, Claude Code registers it only for
the folder you ran the command in, and a session started anywhere else does not see it. `claude mcp
list` then shows `knowgov` as connected, and inside a session `/mcp` lists its tools.

The compose file publishes the page and Neo4j, not the server's HTTP port (8765), so this stdio
route is the one that works with the stack as it stands. For a stack on another machine, see *The MCP servers when the stack runs on another
machine*, below. For a stack started under another project
name (`docker compose -p knowgov-jef`, as the compose file's notes show), add the same `-p` after
`docker compose`. To ask about another subject than the one the server started on, name it on the
call: every tool but `list_subjects` takes `subject`, an id `list_subjects` names (below).

### One registration for every subject

One registration of each server answers for every subject under `KG_SUBJECTS` (task-0157,
decision-0013). Every tool of the reader but `list_subjects`, and every tool of `knowgov-runs`, takes an optional `subject`: the id
in a subject's `subject.toml`, never a path, resolved under `KG_SUBJECTS` as the page resolves
`?subject=`. A call that names none answers as before, for `KG_SUBJECT`. `list_subjects` names
every subject, the scenario the shared store holds for each, and which tools are store-backed.

- **Files-only tools** (`register_nodes`, `key_nodes`, `code_path`, `document_links`,
  `subject_check`, `scenario_runs`, `scenario_result`) answer for any subject at once.
- **Store-backed tools** (`gate_verdict`, `three_valued_answer`, `evidence_bundle`, `store_status`,
  `held_keys`, `derived_outputs`, `document_statements`, and `register_impact` and
  `proposal_impact` for their keys' levels) answer only for the subject and scenario the store
  holds. The store holds one scenario of one subject at a time. For any other subject they
  refuse, naming the held subject and scenario and the `start_run` that would load the one you
  asked about. The reader never loads it for you. Each tool says which it is in its `_meta`
  (`io.knowgov/storeBacked`).
- A call naming another subject runs in a short-lived child process for that subject, with the
  server's date: about 0.4 s a call on Neo4j, more on a file-backed rdflib store, which parses
  the file in each child.

### Connecting Claude Desktop

Claude Desktop starts the same command, but it reads it from a file, and it starts it without your
shell: no `PATH`, no `~`, no `$HOME`. Every path in the file must therefore be absolute, and the
command must be the full path to `docker`. Find it with `which docker` in a terminal (Docker
Desktop on a Mac usually gives `/usr/local/bin/docker`).

1. Open the configuration file. On macOS it is
   `~/Library/Application Support/Claude/claude_desktop_config.json`; on Windows,
   `%APPDATA%\Claude\claude_desktop_config.json`. Claude Desktop's Settings, under Developer, has an
   *Edit Config* button that opens it; some builds show no Developer section, and editing the file
   directly works the same.
2. Add the knowgov entry under `mcpServers`, with your own paths in place of `/usr/local/bin/docker`
   and `/Users/you/src/knowgov`. If the file already has an `mcpServers` object, add `"knowgov"`
   inside it beside the servers already there; do not replace the file.

   ```json
   {
     "mcpServers": {
       "knowgov": {
         "command": "/usr/local/bin/docker",
         "args": ["compose", "-f", "/Users/you/src/knowgov/demo/docker-compose.yml",
                  "exec", "-T", "app", "python", "harness/mcp_server.py"]
       }
     }
   }
   ```

3. Quit Claude Desktop completely (on a Mac, Claude › Quit, not only closing the window) and reopen
   it. It reads the file only when it starts.
4. Ask in a Chat conversation. The first time the assistant calls a knowgov tool, Claude Desktop
   asks your permission; allow it. Chat in Claude Desktop runs on your computer and reaches the
   stack there. A Claude Code session running in the cloud (claude.ai/code, or the Code tab when it
   runs a cloud session) runs on a remote machine and cannot reach a stack on your computer.

If the tools do not appear, the server's own messages are in
`~/Library/Logs/Claude/mcp-server-knowgov.log` on macOS (`%APPDATA%\Claude\logs\` on Windows). A
`docker: not found` there means the command is not the full path; `no such service: app` or a
connection error means the stack is not running.

### Asking from your phone

To ask from the Claude app on your phone, keep the server where it is and reach the computer, not
the server: start Claude Code on the computer that runs the stack with Remote Control
(`claude remote-control`, or `/remote-control` inside a session), then open that session from the
phone. The session runs on your computer, so it starts the server there as above, and nothing is
published. Never put the server on a public address to reach it from a phone: its tools return your
documents' text.

### Over HTTP, for an assistant that connects to a URL

Run the server on your computer, from your knowgov checkout:

```bash
KG_SUBJECT=subjects/cargo_quote python harness/mcp_server.py --http --as-of record   # http://127.0.0.1:8765/mcp
```

It listens on this computer only (`127.0.0.1`), so nothing else on the network can reach it.
`--host` and `--port` change that, or `KG_MCP_HOST` and `KG_MCP_PORT`. An address other than this
computer's is refused unless `KG_MCP_TOKEN` holds a secret; every request must then carry it as
`Authorization: Bearer <secret>`. A request sent from a web page on another site is refused
whatever the address. The tools return your documents' text, so keep the server private: the
token is a lock, not a reason to put it on the internet. `--as-of record` reads reviews on the
subject's pinned record date; leave it out to read them on today's.

Outside the container, the server needs the same Python packages as the harness and the same
store settings (`KG_STORE`, and for rdflib `KG_RDFLIB_FILE`, the file a run left). With the stack
running, its defaults already reach the stack's Neo4j on `bolt://localhost:7687`. For a store
with nothing loaded, every tool says so instead of answering.

A client of the current stateless revision sends every request self-contained: the protocol
version and the client's capabilities in the request's `_meta`, and the same version and method in
headers. This asks for the gate's verdict on S1 for code generation, and gets back the gate's report
as `structuredContent`:

```bash
curl -s http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: gate_verdict' \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
       "params": {"name": "gate_verdict", "arguments": {"scenario": "S1", "task": "codegen"},
                  "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                            "io.modelcontextprotocol/clientCapabilities": {}}}}'
```

Both `_meta` entries are required: a request with the version and no
`io.modelcontextprotocol/clientCapabilities` (an empty object is enough) is answered with error
`-32602`, and headers that do not match the body with `-32020`. A client of the older handshake
sends `initialize` first and needs neither.

### What to ask

Once connected, ask in your own words; the assistant picks the tool. For example:

- "What does the knowgov store hold right now?" (`store_status`)
- "Which version of knowgov am I using?" (`store_status`: its `knowgov` field names the version, the
  commit and, when known, how many commits it is past the release, for example `v0.8.0-277-g7e113f0`. A
  part the server cannot know is `null`. Compare with `git -C ~/knowgov describe --tags --always`.
  `knowgov-runs`' `run_options` reports the same for itself.)
- "On scenario S1, may I build the codegen task? Which keys block it, and who owns each?" (`gate_verdict`)
- "On S1, what is known about `weight_kg|max`, and who verified it?" (`three_valued_answer`)
- "Give me the evidence bundle for codegen on S1 before you write any code." (`evidence_bundle`)
- "Read the gate on S1 as of 2027-06-01: which reviews will have lapsed?" (`gate_verdict` with `as_of`)
- "Which scenarios have been run, and what did the last run of S6 show?" (`scenario_runs`)

### Letting an assistant run a scenario: knowgov-runs

The server above only reads. If you want an assistant to load a scenario itself, without a person
clicking on the page, add a second server, `knowgov-runs` (`harness/mcp_runs.py`). It starts runs
through the page's own run button, so it needs the page running; it starts no process of its own.
It offers three tools:

| Tool | What the assistant asks | What it does |
|---|---|---|
| `run_options` | What may I run? | lists the modes you allow, whether the page can run each now, the model rows with their availability (never a key), the subject's scenarios and the run under way; it changes nothing |
| `start_run` | Run this scenario | starts one run through the page, always once (`n = 1`), marked as started over MCP; refused while another run is under way, with the page's own message |
| `run_status` | How is the run going? | the run's status, elapsed time and the end of its log; once it has ended, its exit code and where its results are read |

A run is never one long call: the assistant starts it, then asks for its status until it is done
or failed.

**The modes.** `KG_MCP_RUN_MODES` names what `start_run` accepts. It is `deterministic` unless you
say otherwise: the load, the rules and the gate, in seconds, with no model call. Name
`deterministic,arms` to allow the Arms run as well; it then runs only on a model row whose key
variable is set, as on the page.

**The spend.** A deterministic run costs nothing. An Arms run calls a model twice, on your
provider's bill, and takes minutes. Allow it only where you mean to pay for it.

**The shared store.** There is one store. A run wipes it and loads the scenario again, so every
viewer of the page sees the assistant's run: the page's banner says it was started over MCP. While
the run loads, the read-only server's gate refuses and names the run. The record is never written.

**Where the page is.** `KG_PAGE_URL` names the page (default `http://localhost:8080`, the page inside
the stack's container). If the page asks for a token, `KG_PAGE_TOKEN` holds it; the server sends it
with every request and never repeats it in a reply. Anyone who can use this server can start runs,
so keep it as private as the token.

Inside the stack's container, Claude Code connects it as it does the reader:

```bash
claude mcp add knowgov-runs -s user -- docker compose -f /path/to/knowgov/demo/docker-compose.yml exec -T app python harness/mcp_runs.py
```

The shipped `managed-mcp-allowlist.json` admits the read-only server only. An organisation that
wants assistants to start runs adds `{"serverName": "knowgov-runs"}` to its own list. A tool that
wipes the store should be approved call by call, not once for good.

### The MCP servers when the stack runs on another machine

When the stack runs on a server you reach over SSH, such as the EC2 instance in `demo/README.md`
(*The Arms mode on an EC2 instance*), your own computer has no container to start the servers in,
and the commands above find nothing. Start them over SSH instead. The assistant runs `ssh`, `ssh`
runs the same `docker compose … exec` command on the server, and the protocol travels over the SSH
connection's input and output, as it did over the local command's. Nothing new listens anywhere:
the stack keeps its `127.0.0.1` bind, no port is opened and no token is needed. SSH, which you
already use for the page's tunnel, is the lock.

**What it needs first.** The assistant starts `ssh` with no terminal, so SSH must connect without
asking anything: Claude Desktop cannot answer a password prompt or a *yes/no*.

1. *A short name for the server.* Add a block to `~/.ssh/config` on your computer (create the file if
   it is not there), with your instance's address and your key file:

   ```text
   Host knowgov-ec2
       HostName <the instance's public address>
       User ubuntu
       IdentityFile ~/.ssh/<key>.pem
       IdentitiesOnly yes
       BatchMode yes
       ServerAliveInterval 30
   ```

   `BatchMode yes` makes SSH fail with a message instead of waiting for an answer nobody can give.
   The key file AWS creates has no passphrase. If yours has one, add it to the agent first (on a Mac,
   `ssh-add --apple-use-keychain ~/.ssh/<key>.pem`, with `UseKeychain yes` and `AddKeysToAgent yes`
   in the block).
2. *The server's host key known.* Connect once in a terminal and answer `yes` when SSH asks whether
   to trust the server:

   ```bash
   ssh -o BatchMode=no knowgov-ec2 true
   ```

   Never set `StrictHostKeyChecking no` to skip this: SSH would then talk to whichever machine
   answers at that address.
3. *Docker without `sudo` on the server*, for the user in the block (step 2 of the EC2 route does
   it), and the stack running there.

Check all three at once. This must print the `app` service as *healthy* and ask nothing:

```bash
ssh knowgov-ec2 docker compose -f knowgov/demo/docker-compose.yml ps app
```

The path `knowgov/demo/docker-compose.yml` is read on the server, from your home folder there (where
the EC2 route cloned `~/knowgov`); it is not a path on your computer.

**Claude Code.** Register both servers once. If you registered them for a local stack before, remove
those first (`claude mcp remove knowgov -s user`, and the same for `knowgov-runs`):

```bash
claude mcp add knowgov -s user -- ssh -T knowgov-ec2 docker compose -f knowgov/demo/docker-compose.yml exec -T app python harness/mcp_server.py
claude mcp add knowgov-runs -s user -- ssh -T knowgov-ec2 docker compose -f knowgov/demo/docker-compose.yml exec -T app python harness/mcp_runs.py
```

`ssh -T` asks for no terminal on the server, as `exec -T` does in the container: the protocol needs
plain input and output end to end. `claude mcp list` then shows both as connected; in a session
already open, `/mcp` and reconnect each. This holds for Claude Code running on your computer (in a
terminal, or a local session of the desktop app's Code tab). A cloud session (claude.ai/code, or a
Code-tab session marked with a cloud) runs on another machine: it never sees what `claude mcp add`
registered on yours, and has neither your key nor an address the security group admits.

**Claude Desktop.** In `claude_desktop_config.json` (where to find it is under *Connecting Claude
Desktop*), the command is the full path to `ssh`, which on a Mac is `/usr/bin/ssh`. Add both entries
inside your `mcpServers`, beside any servers already there:

```json
{
  "mcpServers": {
    "knowgov": {
      "command": "/usr/bin/ssh",
      "args": ["-T", "knowgov-ec2", "docker", "compose", "-f", "knowgov/demo/docker-compose.yml",
               "exec", "-T", "app", "python", "harness/mcp_server.py"]
    },
    "knowgov-runs": {
      "command": "/usr/bin/ssh",
      "args": ["-T", "knowgov-ec2", "docker", "compose", "-f", "knowgov/demo/docker-compose.yml",
               "exec", "-T", "app", "python", "harness/mcp_runs.py"]
    }
  }
}
```

Then quit Claude Desktop completely and reopen it. SSH finds `~/.ssh/config` and your key by itself;
the rule that every path in this file is absolute concerns the paths on your computer, and the only
one here is `/usr/bin/ssh`.

**knowgov-runs needs nothing more.** It runs inside the `app` container on the server, so its default
page, `http://localhost:8080`, is the page on the server, and the page's `KG_PAGE_TOKEN`, if you set
one, is already in that container. The SSH tunnel to port 8080 is for your browser; neither server
needs it.

**Checking it.** From a terminal on your computer, this sends the server the protocol's opening and
asks it which subjects it knows:

```bash
ssh -T knowgov-ec2 docker compose -f knowgov/demo/docker-compose.yml exec -T app python harness/mcp_server.py <<'END'
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "1"}}}
{"jsonrpc": "2.0", "method": "notifications/initialized"}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_subjects", "arguments": {}}}
END
```

It prints two lines: the server's greeting, then the subjects, every one under the stack's
`KG_SUBJECTS` (`cargo_quote` and `jef_data_load` on the public stack). Then ask the assistant
"What does the knowgov store hold right now?" (`store_status`) and "Which subjects can I ask
about?" (`list_subjects`).

**When it does not connect.** Claude Desktop's log for the server
(`~/Library/Logs/Claude/mcp-server-knowgov.log`) shows what SSH said:

- `Using MCP server command: /usr/local/bin/docker`, then `service "app" is not running`: Claude
  Desktop still runs the local entry. `claude mcp add` changes Claude Code only; Claude Desktop reads
  its own file, so replace its `knowgov` entry there and quit and reopen it.
- `Permission denied (publickey)`: the block's `IdentityFile` or `User` is wrong.
- `Host key verification failed`: step 2 has not been done, or the instance is new; do it again.
- It hangs, then times out: the instance's address has changed (a stopped and started instance gets
  a new one) or your own has (the security group admits *My IP* only). Put the new address in the
  block's `HostName`, the one place both clients read it; an Elastic IP keeps it fixed.
- `permission denied while trying to connect to the Docker daemon socket`: step 3.
- `no such service: app`, or `open …docker-compose.yml: no such file`: the stack is not running, or
  the path on the server is not where you cloned knowgov.

## Creating a subject with an assistant

Writing a subject by hand means a manifest of up to sixteen tables, a register map and a scenario
file, and its mistakes either pass every check or surface late, dressed as missing knowledge. An
assistant can guide you through it instead: a *wizard*, in the sense of a step-by-step procedure,
that proposes, checks after each step and explains the findings. Its steps and its stops are
deterministic: the checks decide, never the assistant.

Two things to know first. The assistant writes the files with its own tools, in your instance
checkout, on a new branch, and ends in a pull request that someone other than its author reviews;
knowgov's server only reads, and checks what is proposed without storing it (`subject_check`). And
there are three things the assistant must never do, which the procedure says in so many words:

- **draft a document's content.** It places, names and checks documents people of record wrote.
  A missing document is a question for its owner, never a draft;
- **write an attestation.** `[verification]` and `[provenance]` in `subject.toml`, `captures/`,
  review files, `preload-baseline.json` and `register/` are a person's act. The attestation hook
  ("Guarding what people attest", below) blocks these writes;
- **take the task's keys from what the documents say.** The keys are what the task needs; what the
  documents yield is shown beside them as a check (a misspelt key gets a *did you mean*), never as
  their source.

**Starting it.** The knowgov server offers two *prompts*, ready-made opening messages a client shows
as commands. In Claude Code, with the server registered as `knowgov` (above):

```
/mcp__knowgov__new_subject renewal codegen
/mcp__knowgov__add_artefact renewal artefacts/textual-requirements/renewal.md
```

In plain English: the first starts a new subject `renewal` whose task class is `codegen`; the second
adds one document to it. Each argument is one word, because Claude Code splits them on spaces;
everything else the assistant asks in the conversation, at most five questions (what the subject is
for, the task, which documents, which owning units, who attests). The same text ships as a Claude
Code *skill*, a procedure the assistant loads by name, for a session without the server: copy
`instance/ci/claude/skills/knowgov-onboard/` into your instance repository's `.claude/skills/`. The
skill and the prompts are one text (`harness/wizard.py` builds the prompts from the skill), and it
carries the kinds table and what each mapper reads (`instance/mappers.toml`), so the assistant need not look them up.

**What happens, in order.** The register first (`register_nodes` to find the nodes the task
touches, `register_impact` for what rests on them and who owns it; `proposal_impact` first for a
new product); then each document into its kind's folder, its mapper
picked by what the check reports it yields (a document that yields nothing is the wrong mapper, not
an empty document, and the check's *zero-yield* warning says so); then the manifest, with the pristine scenario `S0` from `subjects/minimal/`, renamed `<id>-S0`;
then the task's keys and the register map rows; then the attestation lines, written commented out
with what their absence costs; and last, for a key still missing, the owners' questionnaires. After
every write it checks (`subject_check`, or `tools/check_subject.py` and `tools/check_instance.py`
where it has a shell).

**When it stops.** Only when the subject check exits 0 with no warning, the gate's dry run on the
branch exits 0 or 1 (never 2, cannot run), and every remaining finding is knowledge with an owner
and a route. Then it opens the pull request, with a readiness card (per document: kind, mapper,
yield, form; per key: yielded or not, owner, level) and the questionnaires.

**After the merge,** the page lists the new subject on its next request, with no restart, and both
servers answer for it by id with no relaunch (every tool takes `subject`; see "One registration for
every subject" below). One step is yours: load `<id>-S0` (on the page, or `start_run` on `knowgov-runs`
with the subject's id), knowing the load replaces what everyone else viewing that store sees.

**Claude Desktop's role, for now: asking the gate, not onboarding.** In Claude Desktop, use the
server to ask `gate_verdict`, `evidence_bundle`, `three_valued_answer`, `register_impact` and
`proposal_impact`. Creating a subject is Claude Code's job: it writes files on a branch, runs the
checks and the dry run, and opens the pull request. Whether Desktop lists these prompts and runs
`subject_check` has not been tried yet. Until that test shows both, treat Desktop's assistant,
which writes no files without a file extension and has no shell, as unfit to onboard a subject.

## A fail-closed hook for Claude Code

The CI route above fails closed: a pull request whose gate exits 1 or 2 does not merge. The same
gate can stop an AI coding assistant earlier, at the moment it moves from one stage to the next,
before anything reaches a pull request. `instance/ci/claude/` holds the recipe for Claude Code:

| File | Where it goes | Mandatory? |
|---|---|---|
| `managed-settings.json` | your organisation's managed settings: as a drop-in file, `/etc/claude-code/managed-settings.d/50-knowgov.json` on Linux and WSL, `/Library/Application Support/ClaudeCode/managed-settings.d/50-knowgov.json` on macOS, `C:\Program Files\ClaudeCode\managed-settings.d\50-knowgov.json` on Windows; or its keys in server-managed settings from the claude.ai console, the only kind a cloud session receives | **yes**: only the managed one is mandatory |
| `managed-mcp-allowlist.json` | the same managed settings, beside `managed-settings.json`, only if your organisation chooses it: its entries merged into the MCP lists you already hold | no: opt-in, your organisation's own tool policy |
| `settings.json` | the instance repository's `.claude/settings.json`, committed | no: a team default an engineer can switch off |
| `settings.advisory-fail-open.json` | the same place, *instead of* `settings.json`, for a team that chooses it | no: advisory, and fail-open |
| `knowgov_hook.py` | stays in a knowgov checkout at a tag, outside the repository the assistant edits (`/opt/knowgov` in the snippets: change the path to yours) | the script all three call |

In plain English: a hook in the repository's `.claude/settings.json` is one an engineer, or the
assistant, can edit away. A hook in managed settings is not: `allowManagedHooksOnly` runs only the
organisation's hooks. That hook is the enforcement that matters, and `managed-settings.json` carries
nothing else.

**The MCP allowlist, an opt-in.** `managed-mcp-allowlist.json` carries `allowManagedMcpServersOnly`
with `allowedMcpServers`, which let the assistant reach the knowgov MCP server (named `knowgov`, as
"Letting an AI assistant ask the gate" registers it) and no server the organisation has not listed.
Which MCP servers an assistant may use is your organisation's own tool policy, so this fragment is
yours to adopt or leave. Both lists replace the lists of every lower settings source rather than
adding to them: copied as is, the fragment would switch off every other MCP server your organisation
allows. Merge its entries into the lists your managed settings already hold. Without the opt-in the
hook stays mandatory all the same: the gate still blocks at every stage transition.

**When it fires.** At stage transitions, never on every edit: a gate that loads the store takes
seconds, and a hook on every edit must be fast and file-scoped. The script decides itself whether a
tool call is a transition, so the snippets need no fragile command pattern:

- **plan**: the assistant presents a plan for acceptance (`ExitPlanMode`);
- **spec**: a `git commit` that carries a spec file (`--spec GLOB`, default `spec.md` at any depth),
  whether it was staged earlier or by the same command (`git add docs && git commit`, `git commit -a`,
  `git commit spec.md`); when the hook cannot read the command or the worktree, it treats the commit
  as this transition;
- **push**: before `git push`, written `/usr/bin/git push`, `git -C dir push`, `bash -c 'git push'`,
  `` echo `git push` `` or through an alias (`git -c alias.ship=push ship`, or one in your git configuration)
  as well. Where a variable stands for git or its subcommand (`x=git; $x push`), the hook cannot tell what runs,
  so a command that names `push` is treated as the push.

Any other tool call gets no decision from it, and goes on through the normal permissions.

**What it does.** It runs `knowgov-gate.sh gate` with the task class the snippet names
(`--task codegen`; `--task-for spec=CLASS` for another class at one stage), reads the report, and
maps the exit code. All three snippets carry `--task-for spec=design`: the spec commit is read under
the `design` class, as the pilot protocol does. Keep it only where every subject the hook gates
declares `[tasks.design]` in its `subject.toml`; a subject without that class makes the gate
exit 2 at the spec commit, so the mandatory hook blocks it (the advisory one lets it through, FAIL-OPEN).
Where no subject declares the class, drop the two arguments from whichever snippet you use and the
spec commit is read under `codegen` like the other stages. Claude Code blocks a tool call when a hook exits 2 (exit 1 is only a warning there), so:

| Gate | Mandatory hook | Advisory profile (fail-open) |
|---|---|---|
| 0, PROCEED | the action goes ahead | the action goes ahead |
| 1, a finding | **blocked**, naming the findings and the route to approval: the key's owner answers it, a reviewer who is not the author settles it | **blocked**, the same |
| 2, cannot run (no subject, rdflib missing, a timeout; for a gate that uses the store, an unreachable store) | **blocked**, naming the gate as unavailable | goes ahead, with a warning that says FAIL-OPEN |
| a report for another task, or for `keys` | **refused**, blocked | **refused**, blocked |

A report for `keys` is one the MCP server's `gate_verdict` gives for a set of keys the assistant chose
itself; a mandatory check reads only the task class's own scope, which changes by pull request. The
snippets also set `"onFailure": "block"` (Claude Code 2.1.295 or later), so a missing script, a
crash or a timeout blocks too; the advisory one does not. A block is never lifted by the session
that hit it: the route is the owner's answer, or an exception from whoever owns the managed settings.

**Its settings.** The store, the subject, the scenario and the date are the gate's own `KG_*`
variables, as "Running the gates in your pipeline" lists them, in the environment Claude Code starts
with (the managed settings' `env` key, or the engineer's shell). The hook's gate loads the scenario
into a private copy in memory and leaves the store `KG_STORE` names as it was, so two sessions can
share one Neo4j. The exception is a gate set to use that store: `KG_PUBLISH=1` in that environment,
or one told to read the store as the instance left it. Then keep one store per worktree: rdflib in memory (`KG_STORE=rdflib` and no `KG_RDFLIB_FILE`: every run
loads its own), a `KG_RDFLIB_FILE` inside each worktree, or one compose project per worktree. Either
way, pass the MCP tools' `scenario` argument, so a read of another session's load is refused.

`python3 knowgov_hook.py run -- COMMAND` maps any other check under the gate contract the same way,
and `decide()` is the mapping for a script that imports it. This repository's tests run the script
against PROCEED, BLOCKED, an unreachable store and a missing subject; only PROCEED lets the action
through (`tests/test_claude_hook.py`, live on rdflib in CI).

### Guarding what people attest

Some files in your instance record what a *person* vouched for, and an assistant must never write
them for that person. They are:

- in a `subject.toml`, the `[verification]` table (when the documents were reviewed, what they were
  read against, where the approval is recorded) and the `[provenance]` table (who attests): see
  "Who vouches for a document"; and its `[capture]` table, since re-pointing `[capture] dir` would make
  any folder the capture folder;
- a subject's `captures/` folder (answers people gave, and `captures/reviews/`, the rulings on them),
  or the folder its `[capture] dir` names;
- the file its `[verification] map` names, which says which keys a test or a dated review covers;
- a review file anywhere (a TOML file with a `[review]` table or a `[[ruling]]`);
- a capture anywhere (a TOML file with `[[answer]]` or `[[unknown]]` rows, a `[capture]` table, or an
  `[answered]` table that names a handle or a date); a blank questionnaire is not one;
- `preload-baseline.json`, the pre-load findings an owner accepted (see "Checking a document before the load");
- everything under `register/`, which changes by its own pull request and checks.

`attestation_paths.py`, beside `knowgov_hook.py`, is a second hook that blocks an assistant's Edit,
Write, MultiEdit or NotebookEdit on any of these. In plain English: the assistant may add an artefact
or a task class to `subject.toml`, and may remove the attestation tables outright (that attests
nothing), but the moment a write would add or change `[verification]`, `[provenance]` or `[capture]`, or touch one
of the files above, Claude Code stops it and tells the assistant to leave it to the person of record.
The same holds for `[oracle] suite` while `[verification]` stays: removing it would unbind the suite's
expectations from the digests `execution` lists.
It compares the two tables as parsed TOML before and after the write, so moving a comment or adding
an artefact is not mistaken for an attestation.

It fails closed, like the gate's hook: an event it cannot read, an edit whose text is not in the
file, or a `subject.toml` that does not parse after the write blocks too, and says so. It maps its
answer through the same `decide` as `knowgov_hook.py`, and calls nothing else.

`settings.attestations.json` wires it. Add its `PreToolUse` entry to the instance repository's
`.claude/settings.json` beside the gate's, or, for the mandatory version, drop it into managed
settings as a second file next to the gate's, for example
`/etc/claude-code/managed-settings.d/51-knowgov-attestations.json` on Linux (the same folders as the
table above). Change `/opt/knowgov` to your checkout's path.

What it does not see: a shell command that writes the same file (`harness/capture.py ingest` and
`review` are such commands, run by the person whose act they record), and anything written outside
the assistant. The hook guards the assistant's file tools; the pull request, reviewed by someone
other than its author, guards the rest.

## The settings an instance may rely on

Most of what you configure is in files: `subject.toml`, `code_map.toml`, the CI templates. A few things are
*environment variables*, set in the shell, the CI job or the compose file before a command starts. The table
below has one row for every `KG_*` setting this guide or [`docs/security.md`](../docs/security.md) names, and,
since decision-0034 choice 1, for every one the code reads or a compose file under `demo/` passes, but for a
short list of internal names, each with its reason, in `tests/test_settings_table.py`. **A setting is a
contract when the table marks it so** (decision-0016 point 3, as amended by decision-0033 choice 1): the
settings an instance's CI, compose file or hook sets in order to run, decision-0027's twenty among them. A row
marked *no* is named so you can find it: the demo stack's own settings, tuning knobs, a debugging aid and one
escape. It may change in any release, so do not build on it. A setting that neither file names is not a
contract. Where a row says "see", the setting is described there; the worker's limits are in
[`docs/security.md`](../docs/security.md).

**On and off.** A setting that switches something on or off reads one way everywhere (decision-0033, task-0276):
`1` is on, and `0`, empty or unset is off. The two checks this guide and `docs/security.md` switch off by name keep
their word: `KG_LOAD_MEMORY_CHECK=off` and `KG_KEY_CHECK=off`, in any case, with `on`, empty or unset leaving them on.
`KG_CLOCK` takes `pinned`, exactly, or nothing (task-0287). No value is trimmed: `' 1'` or `'pinned '` is refused, not
read. Any other value stops the command with exit 2 and names the setting and what it accepts; before 0.9.0,
`KG_NO_LOAD=true` was silently off. The list is `harness/switches.py`'s `SWITCHES`. The GitHub action's `publish`,
`annotate` and `sarif` inputs take `true` or `false`, in any case, and any other value fails the step, naming the
input; the GitLab include's `KG_PUBLISH` and `KG_NO_LOAD` follow the rule above.

| Setting | Group | What it does | Default | Contract |
|---|---|---|---|---|
| `KG_GATE` | CI templates and hook | which gate the job runs: `preload`, `gate`, `trace-check` or `trace-register`. You set it as a variable of the GitLab include; the GitHub action sets it from its `gate` input | `gate` in the GitLab include | yes |
| `KG_TASK` | CI templates and hook | the task class the gate and the trace read. `keys` is refused with exit 2: a pipeline checks a task class, never a key set an assistant chose. The GitHub action sets it from its `task` input; the hook, per stage, from its settings snippet | `codegen` | yes |
| `KG_STAGE` | CI templates and hook | `2` brings in the scenario's later version (the gate's `--stage 2`); the GitHub action sets it from its `stage` input | none: the first stage | yes |
| `KG_NO_LOAD` | CI templates and hook | `1` makes the gate read the store as your instance's load left it, instead of loading a private copy (the gate's `--no-load`) | none: the gate loads a private copy | yes |
| `KG_PUBLISH` | CI templates and hook | `1` makes the gate load into the store `KG_STORE` names and publish it, for a later step that reads it; see "Running the gates in your pipeline" | none: the gate's own private copy | yes |
| `KG_SCENARIO` | CI templates and hook | the scenario the gate loads | the subject's first | yes |
| `KG_FAIL_ON` | CI templates and hook | the severity at or above which a gate exits 1 | each command's own | yes |
| `KG_AS_OF` | CI templates and hook | the date review currency is read on: `YYYY-MM-DD`, `record` or `today`; see "Running the gates in your pipeline" | `today` | yes |
| `KG_BASE` | CI templates and hook | the git ref the changed files are taken against, a pull request's base | none: every file | yes |
| `KG_COMMIT` | CI templates and hook | the commit being checked or registered; `trace-register` needs it | none | yes |
| `KG_FILES` | CI templates and hook | the files `trace-register` registers, relative to `code_map.toml`'s root | the files changed since `KG_BASE` | yes |
| `KG_LEDGER` | CI templates and hook | the trace ledger `trace-check` reads and `trace-register` writes (`--ledger`) | `trace-ledger.json` in the working directory | yes |
| `KG_CODE_REPO` | CI templates and hook | the name of your code repository, in the id `trace-register` gives each file it registers. The GitHub action fills in the repository's name, and the GitLab include the project's | `code` | yes |
| `KG_REPORT` | CI templates and hook | where a gate also writes its JSON report, to keep or annotate | none | yes |
| `KG_ANNOTATE` | CI templates and hook | the report as your platform's annotations, `FORMAT[:FILE]`, comma-separated; see "Running the gates in your pipeline" | none | yes |
| `KG_PRELOAD_BASELINE` | CI templates and hook | the baseline the pre-load check fails against only on regression (`--baseline`); see "Checking a document before the load" | none | yes |
| `KG_PROPOSAL_REPORT` | CI templates and hook | where the optional proposal step also writes its JSON report; see "A register pull request read before approval" | none | yes |
| `KG_SUBJECT_IN` | CI templates and hook | the GitHub action's own carrier for its `subject` input: when it is set, the action passes it on as `KG_SUBJECT`. You set the input, not this variable | none: the instance's only subject | yes |
| `KG_HOME` | CI templates and hook | where the Claude Code hook finds the knowgov checkout. The hook's settings snippets set `/opt/knowgov`: change it to your checkout's path | the checkout the hook file is in; the hook's `--knowgov` option overrides both | yes |
| `KG_SPECTRAL` | Pre-load linters | the Spectral command, when it is not on `PATH` | `spectral` on `PATH` | yes |
| `KG_MARKDOWNLINT` | Pre-load linters | the markdownlint command, when it is not on `PATH` | on `PATH` | yes |
| `KG_GPLINT` | Pre-load linters | the gplint command, when it is not on `PATH` | on `PATH` | yes |
| `KG_BPMNLINT` | Pre-load linters | the bpmnlint command, when it is not on `PATH` | on `PATH` | yes |
| `KG_DMNLINT` | Pre-load linters | the dmnlint command, when it is not on `PATH` | on `PATH` | yes |
| `KG_SUBJECT` | Subject and register | the subject root a command reads | in the CI templates, the instance's only subject | yes |
| `KG_SUBJECTS` | Subject and register | the folder of subjects the page and both MCP servers list | `subjects/` of the checkout | yes |
| `KG_REGISTER` | Subject and register | the register checkout every subject joins | `demo/register`, the public register | yes |
| `KG_REGISTER_PREVIOUS` | Subject and register | the register checkout before an update, which the page's register view reads to show what the update withdrew; the gate's own option for it is `--register-previous` | none | yes |
| `KG_INSTANCE` | Subject and register | your instance's checkout, for the stack's compose file and the upward joins | none | yes |
| `KG_PRELOAD_REPORT` | Subject and register | the pre-load report the load records per document version | `preload-report.json` at your instance's root | yes |
| `KG_STORE` | Store | which store: `neo4j` or `rdflib` | `neo4j` | yes |
| `KG_RDFLIB_FILE` | Store | the file an rdflib store is kept in | none: in memory | yes |
| `KG_NEO4J_URI` | Store | the address of the Neo4j store, as a bolt URL. The image and the compose file set `bolt://neo4j:7687`, the stack's own Neo4j | `bolt://localhost:7687` | yes |
| `KG_NEO4J_USER` | Store | the Neo4j user name, when your Neo4j has another user | `neo4j` | yes |
| `KG_NEO4J_PASSWORD` | Store | the Neo4j password; on a wider bind the stack refuses to start without it. See `docs/security.md` | the demo's own, on the default bind only | yes |
| `KG_LOAD_MEMORY_CHECK` | Store | `off` loads a Neo4j load the forecast refuses; see "Sizing the Neo4j heap" | on | yes |
| `KG_LOAD_MEMORY_MARGIN` | Store tuning | the margin the load's memory forecast keeps, 0 to 4 | `0.25` | no: a tuning knob |
| `KG_NEO4J_LEASE_SECONDS` | Store tuning | how long a Neo4j writer's lease lasts, renewed while it runs; see `docs/security.md` | `60` | no: a tuning knob |
| `KG_NEO4J_LOCK_TIMEOUT` | Store tuning | how long a second Neo4j writer waits; see `docs/security.md` | `60` | no: a tuning knob |
| `KG_NEO4J_READ_WAIT` | Store tuning | how long a Neo4j read waits on a live publication; see `docs/security.md` | `10` | no: a tuning knob |
| `KG_RDFLIB_LOCK_TIMEOUT` | Store tuning | how long a second rdflib writer waits for the file's lock; see `docs/security.md` | `60` | no: a tuning knob |
| `KG_STORE_READ_ATTEMPTS` | Store tuning | how many times a read retries a changed generation; see `docs/security.md` | `3` | no: a tuning knob |
| `KG_BIND` | Page and MCP servers | the address the stack publishes the page, Neo4j Browser and bolt on | `127.0.0.1` | yes |
| `KG_PAGE_TOKEN` | Page and MCP servers | the bearer token the page's state-changing requests must carry; knowgov-runs sends it | none | yes |
| `KG_PAGE_AUTHORITIES` | Page and MCP servers | the further `host:port` names the page answers for, behind a proxy | none | yes |
| `KG_PAGE_ORIGINS` | Page and MCP servers | the further web origins the page accepts a request from | none | yes |
| `KG_DEMO_HOST` | Page and MCP servers | the host name the page answers for on its published port, besides the loopback names | `localhost` | yes |
| `KG_BROWSER_URL` | Page and MCP servers | Neo4j Browser's address, for the page's links; its origin reads the impact guides | `http://localhost:7474` | yes |
| `KG_MCP_HOST` | Page and MCP servers | the MCP reader's HTTP bind address (`--host`) | `127.0.0.1` | yes |
| `KG_MCP_PORT` | Page and MCP servers | the MCP reader's HTTP port (`--port`) | `8765` | yes |
| `KG_MCP_TOKEN` | Page and MCP servers | the secret every HTTP request to an MCP server must carry; a wider bind is refused without it | none | yes |
| `KG_MCP_AUTHORITIES` | Page and MCP servers | the further `host:port` names the MCP server answers for | none | yes |
| `KG_MCP_ORIGINS` | Page and MCP servers | the further web origins the MCP server accepts a request from | none | yes |
| `KG_MCP_RUN_MODES` | Page and MCP servers | what knowgov-runs' `start_run` accepts: `deterministic`, or `deterministic,arms` | `deterministic` | yes |
| `KG_PAGE_URL` | Page and MCP servers | where knowgov-runs finds the page | `http://localhost:8080` | yes |
| `KG_SUBJECT_CALL_TIMEOUT` | Page and MCP servers | how many seconds the MCP reader lets one call for another subject take; past it the call's own process ends and the tool answers with an error naming the subject | `300` | yes |
| `KG_PAGE_MAX_RESPONSE` | Server limits | the largest page response, in bytes; see `docs/security.md` | 8 MiB | no: a tuning knob |
| `KG_PAGE_MAX_RUNS` | Server limits | the largest `n` a page run takes | `5` | no: a tuning knob |
| `KG_MCP_MAX_RESPONSE` | Server limits | the largest MCP tool result, in bytes; see `docs/security.md` | 16 MiB | no: a tuning knob |
| `KG_PAGE_MAX_BODY` | Server limits | the largest request body the page reads, in bytes | 64 KiB | no: a tuning knob |
| `KG_PAGE_READ_TIMEOUT` | Server limits | the seconds a page request has to arrive whole | `10` | no: a tuning knob |
| `KG_PAGE_IDLE_TIMEOUT` | Server limits | the seconds the page waits through one silence in a request | `5` | no: a tuning knob |
| `KG_PAGE_MAX_CONNECTIONS` | Server limits | the connections the page serves at once; more get 503 | `32` | no: a tuning knob |
| `KG_MCP_MAX_BODY` | Server limits | the largest request body the MCP server reads, in bytes | 4 MiB | no: a tuning knob |
| `KG_MCP_READ_TIMEOUT` | Server limits | the seconds an MCP request has to arrive whole | `10` | no: a tuning knob |
| `KG_MCP_IDLE_TIMEOUT` | Server limits | the seconds the MCP server waits through one silence in a request | `5` | no: a tuning knob |
| `KG_MCP_MAX_CONNECTIONS` | Server limits | the connections the MCP server serves at once; more get 503 | `32` | no: a tuning knob |
| `KG_PORT_APP` | Demo stack | the host port the stack publishes the page on | `8080` | no: a demo port |
| `KG_PUBLIC_PORT` | Demo stack | the compose file's carrier of `KG_PORT_APP` into the page; you set `KG_PORT_APP`, not this | `KG_PORT_APP` | no: a demo port |
| `KG_PORT_BOLT` | Demo stack | the host port the stack publishes bolt on, and the one the page's Browser link names | `7687` | no: a demo port |
| `KG_PORT_BROWSER` | Demo stack | the host port the stack publishes Neo4j Browser on | `7474` | no: a demo port |
| `KG_DEMO_PORT` | Demo stack | the port the page listens on inside its container | `8080` | no: a demo port |
| `KG_PAGE_LISTEN` | Demo stack | the address the page listens on inside its container; the image sets `0.0.0.0`, and `KG_BIND` decides what reaches it | `127.0.0.1` | no: the image's own; set `KG_BIND` |
| `KG_DEMO_RUNS` | Demo stack | the folder the page keeps its runs in, and the MCP reader replays from | the checkout's `runs/`; the image sets `/repo/runs` | no: the demo's own folder |
| `KG_BUILD_COMMIT` | Demo stack | a build argument: the commit the image says it was built from | none: read from `.git` | no: a label on the image; nothing decides on it |
| `KG_BUILD_DESCRIBE` | Demo stack | a build argument: `git describe` for the image, its distance from the release | none: unknown | no: a label on the image; nothing decides on it |
| `KG_ANTHROPIC_KEY` | Demo stack | the key the compose file passes to the demo's LiteLLM service, for its Claude row | none | no: the demo's own model row |
| `KG_OUTCOMES` | Demo stack | a file each check tool appends its outcome to, one JSON line | none: nothing written | no: the check tools' log, for this repository's CI |
| `KG_MODEL_BASE_URL` | Model endpoint | the endpoint the arms call | `https://api.openai.com/v1` | yes |
| `KG_ARMS_MODEL` | Model endpoint | the model the arms call; each row of the model table names its own | the subject's record model, else `gpt-5.5` | yes |
| `KG_MODEL_API_KEY_VAR` | Model endpoint | the *name* of the environment variable that holds the model key, never the key itself | `OPENAI_API_KEY` | yes |
| `KG_MODEL_API_KEY` | Model endpoint | a variable the compose file passes into the page, for a key, so that `KG_MODEL_API_KEY_VAR` or a row's key variable can name it. Set it in your shell before `docker compose up`, never in a file you commit | none | yes |
| `KG_MODELS` | Model endpoint | the table of model rows the page's Arms drop-down lists | `demo/models.toml` (inside the container, `/repo/demo/models.toml`) | yes |
| `KG_KEY_CHECK` | Model endpoint | `off` sends nothing to check a row's key; see `docs/security.md` | on | yes |
| `KG_ARMS_EFFORT` | Model endpoint | the reasoning effort sent with every arm call | none: the model's own | no: its values are the model API's |
| `KG_ARMS_MAX_TOKENS` | Model endpoint | the most prompt and completion tokens one arms process spends | 6,000,000 | no: a tuning knob |
| `KG_AGENT_MAX_CALLS` | Model endpoint | the most model calls one agent rebuild makes | `30` | no: a tuning knob |
| `KG_AGENT_MAX_TOKENS` | Model endpoint | the most tokens one agent rebuild spends | 1,500,000 | no: a tuning knob |
| `KG_AGENT_MAX_SECONDS` | Model endpoint | the longest one agent rebuild runs, in seconds | `1500` | no: a tuning knob |
| `KG_AGENT_IDLE_SECONDS` | Model endpoint | the longest silence an agent's stream may keep, in seconds | `120` | no: a tuning knob |
| `KG_WORKERS` | Worker | how many of an arm's runs the harness makes at once; see `docs/security.md` | `5` | yes |
| `KG_WORKER_CPUS` | Worker | the worker container's CPUs; see `docs/security.md` | `2` | yes |
| `KG_WORKER_MEM` | Worker | the worker container's memory; see `docs/security.md` | `4g` | yes |
| `KG_WORKER_JOB_SECONDS` | Worker | the wall time one job may take; see `docs/security.md` | `900` | yes |
| `KG_WORKER_JOBS` | Worker | the jobs folder the app and the worker share; see `docs/security.md` | the compose file's `/jobs` | yes |
| `KG_WORKER_WORK` | Worker | the worker's own work folder; see `docs/security.md` | `/work` | yes |
| `KG_WORKER_MEMORY` | Worker | the address space one job may use, in bytes, inside the container's own memory | 4 GiB | no: a bound inside the container's, which `KG_WORKER_MEM` sets |
| `KG_WORKER_PROCESSES` | Worker | the processes one job may run | `128` | no: a bound inside the container's |
| `KG_WORKER_FILE_BYTES` | Worker | the largest file one job may write, in bytes | 64 MiB | no: a bound inside the container's |
| `KG_WORKER_MAX_JOB_SECONDS` | Worker | the longest wall time a job may ask for | `900` | no: a bound inside `KG_WORKER_JOB_SECONDS`'s |
| `KG_ALLOW_UNCONTAINED_EXECUTION` | Worker | `1` runs model-written code on the host, uncontained; see `docs/security.md` | none | no: an escape, never to be relied on |
| `KG_CLOCK` | Clock | `pinned`, exactly, makes a command that would read the wall clock fail; any other value but empty exits 2 (task-0287); see "Capturing what people know" | none | yes |
| `KG_TODAY` | Clock | a fixed today, `YYYY-MM-DD`, for a reproducible run | the wall clock | yes |
| `KG_NOW` | Clock | a fixed instant, ISO 8601 (naive reads as UTC), for the read that compares a live run's heartbeat with the clock; under `KG_CLOCK=pinned` that read refuses without it | the wall clock | yes |
| `KG_TRACEBACK` | Diagnostics | `1` prints a command's traceback after its one-line cause, for a person debugging | none | no: a debugging aid |

## What stays stable from 1.0: the contracts

A **contract** is a part of knowgov your instance is allowed to depend on: a flag your pipeline
passes, a file name it writes, a report field it reads. knowgov follows version numbers that say
when one changes. Release 0.9.0 freezes the contracts, and 1.0.0 promises to keep them. Which
parts count is decided in the project's record, decision-0016, point 3, quoted here as accepted on
2026-11-06:

> **The contracts at 1.0** are decision-0003 §2's list (the gate command's exit codes and flags, the JSON shapes under `harness/schemas/`, the instance layout, the store port, the subject manifest format), and also:
> - the MCP reader's and the runs server's tools, prompts, and their inputs and outputs;
> - the `KG_*` settings that `instance/README.md` or `docs/security.md` documents (an undocumented setting is not a contract);
> - the page's HTTP API, as `demo/README.md` documents it;
> - the inputs and outputs of `instance/ci/`: the action, the GitLab include, the shell wrappers, the hooks' settings snippets;
> - the image's name and tag scheme (decision-0003 §3);
> - the format versions of the instance's inputs, and the ieam-register format versions an instance's register may be in.

In plain English: each row is one contract, where it is described, and how you are told when it
changes. Every contract change is listed in `CHANGELOG.md` under its release's **Contract changes**
heading, so that heading is the one place to watch. Some contracts also carry a signal of their own,
named in the last column.

| You can rely on | Described in | How you are told of a change |
|---|---|---|
| the gate command's flags and its exit codes: 0 no finding at or above `--fail-on`, 1 a finding at or above it, 2 the gate could not run | "Running the gates in your pipeline", above | `CHANGELOG.md`, Contract changes |
| the shape of every JSON report, each pinned by a schema | `harness/schemas/` | `CHANGELOG.md`, Contract changes; where a report carries `schema_version`, the line names it when it moves |
| the folders and files of your instance | "The layout", at the top | `CHANGELOG.md`, Contract changes |
| what a store must offer the platform (the store port) | `harness/store.py` | `CHANGELOG.md`, Contract changes |
| the fields of `subject.toml` | the [subjects guide](../subjects/README.md) | `CHANGELOG.md`, Contract changes; its `[format] version` moves with its format ("Format versions", above) |
| the tools and prompts of both assistant servers (the reader and the runs server), what they take and what they return | "Letting an AI assistant ask the gate", above | `CHANGELOG.md`, Contract changes; each server names the knowgov version it runs |
| the `KG_*` settings this file or [`docs/security.md`](../docs/security.md) names that the settings table marks as contracts (decision-0016 point 3, as amended by decision-0033 choice 1) | "The settings an instance may rely on", above, and `docs/security.md` | `CHANGELOG.md`, Contract changes |
| the page's HTTP API: the four routes the demo's guide names, `POST /api/run`, `GET /api/scenarios`, `GET /api/subjects` and `POST /api/models/check` (decision-0030); every other route may change in any release | the [demo's guide](../demo/README.md), "The page's HTTP API" | `CHANGELOG.md`, Contract changes |
| the CI action, the GitLab include, the shell wrappers and the hooks' settings files | "Running the gates in your pipeline" and "A fail-closed hook for Claude Code", above | `CHANGELOG.md`, Contract changes; you run them from the knowgov tag you pin |
| the image's name and tags: `ghcr.io/fdurieux/knowgov:vX.Y.Z` for a release (its tag, `v` included), `:latest` for the last build of `main`; `:<short-sha>` is a build of `main`, not a contract (decision-0033) | the [README](../README.md) | each release's tag; `CHANGELOG.md`, Contract changes |
| the format version each of your input files declares (built: decision-0023 and its Amendment A1, task-0174, task-0236): a file with no number is read as version 1, in every release | "Format versions", above | the number in the file moves, and `CHANGELOG.md` says what changed and how to bring an older file up to date |
| which ieam-register format versions your register may be in: this release of knowgov reads a register in the format of ieam-register `v0.2.13`, the tag it vendors (`demo/register/SOURCE.md`) and tests. A register at another tag may load, but is untested (decision-0028) | `demo/register/SOURCE.md` | `CHANGELOG.md`, when a release vendors another tag; one that changes a contract output is listed under Contract changes |

Two things follow from the quoted text, with decision-0033 choice 1, which amends its `KG_*` item to "a
setting the table marks as a contract". A `KG_*` setting that neither this file nor `docs/security.md` names
is not a contract, and one they name is a contract only when the table in "The settings an instance may rely
on" marks it so; do not build on the others. A setting the demo's guide
alone describes is a convenience of the demo, not a promise. And the page's HTTP API is the
contract only as far as the demo's guide documents it.

### How a change reaches you, and for how long you are supported

The same decision says how the contracts may change, and for how long a release is looked after.
In plain English: from 0.9.0, a release whose last number moves (0.9.1, 0.9.2) only fixes things,
and any change to a contract waits for 0.10.0. From 1.0.0, nothing you rely on disappears without
warning: it is first marked *deprecated*, keeps working for a while, and is removed only in a new
major version. Support covers the latest minor release only, on a best-effort basis, until the
organisation that will offer support exists. Its points 2, 5 and 6, as accepted:

> **0.9.x carries fixes only.** A fix, a documentation change or a dependency pin is a patch. Any contract change, additive or breaking, is 0.10.0 and restarts the freeze. This amends decision-0003 §2 from 0.9.0 on. Until 0.9.0, decision-0003 §2 stands, and contract changes after 0.8.0 gather for 0.9.0.

> **Deprecation, from 1.0.0.** A contract element is deprecated in a minor release, under a `### Deprecated` heading in `CHANGELOG.md`. It keeps working for at least one further minor and ninety days, and is removed only in a major. Ninety days is the drafter's figure.

> **Support.** Until task-0060's entity exists, the latest minor only, on a best-effort basis; from then, the entity's support terms.
