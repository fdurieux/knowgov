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

The platform reads this folder and never writes to it: the compose file mounts it read-only,
and every run lands in the platform's own `runs/` folder. The one tool that writes is the
connector, which you run yourself, in your own checkout, to add an export to your register.

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
- `MANIFEST.toml`: the export time, the source and its version, the tool, the previous folder,
  a sha256 per file, and the register ids carried, with their names.
- `RECONCILE.json`: what changed since the previous folder. That means files and ids added,
  updated or renamed, and deleted. It also lists the *stale* register nodes: those whose id the
  previous export carried and this one does not.

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

`KG_AS_OF` is the date the gate, `trace-check` and `trace-register` read review currency on (`--as-of`, decision-0005):
a `YYYY-MM-DD` date, `record` (the subject's pinned record date) or `today`, the default. Set it to
check a release as of its cut date, or to rehearse a lapse before it falls due: S1 as of 2027-08-08
is BLOCKED, with a `lapsed` finding for each review past its months. The action takes it as the
input `as-of`; the GitLab include as the variable `KG_AS_OF` (task-0089; `trace-register`, task-0093).

- **GitHub Actions**: a composite action. It runs the knowgov tag you name in `uses:`, and maps the
  commit and the pull request's base for you:

  ```yaml
  - uses: fdurieux/knowgov/instance/ci/github@<tag>
    with: { gate: trace-check, instance: instance, ledger: trace/ledger.json }
  ```

- **GitLab CI**: an include, `instance/ci/gitlab/knowgov.gitlab-ci.yml`, with a hidden job
  `.knowgov-gate` your jobs extend. It maps `CI_COMMIT_SHA` and `CI_MERGE_REQUEST_DIFF_BASE_SHA`.
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
report names statements, not lines in a document. A pre-load finding your baseline holds is at most a
warning, since it did not fail the check. The layout check's problems appear in the job's log only.
Annotations never change the exit code.

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

- coverage C1 to C3 before and after, with the new gaps;
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

The example instance shows what a first run finds. Its prose, Gherkin and DMN are clean under the
shipped configurations; its BPMN model (`quote_process.bpmn`) has no diagram interchange and no
`incoming`/`outgoing` references on its nodes, so `bpmnlint:recommended` reports 97 errors on it.
That is a real finding about the model's form, not a fault of the check: adopt over it with a
baseline (below), or fix the model.

To run it on every pull request, copy `instance/ci/preload-check.yml` into your instance's
`.github/workflows/`, pin `KNOWGOV_REF` to a knowgov tag, and make the job a required check with
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
per document, and the gate lists the documents behind a task's keys whose form was unchecked or
had findings, as `info` findings that change the exit only under `--fail-on info`. Without a
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

## Capturing what people know

Some knowledge is in nobody's documents, only in people's heads. The gate then reports a key as
*absent* or as a *declared gap*, and it blocks. The capture path turns that into a recorded
statement, without anyone having to write a document first.

```bash
python harness/capture.py questionnaire --scenario S2 --out questionnaires/
```

In plain English: this loads the scenario, asks the gate which keys are missing or weak, and
writes one questionnaire per *owner*: the organisation unit your register names as owner of the
building blocks each key concerns. When several units own those building blocks, give the key's
row in `register_map.toml` an `owner`, one of them, and only that unit is asked; otherwise each
of them is, and two people may answer the same key. Each questionnaire says how many keys the owner has and how
many need an answer. For each one it shows what the store holds now and asks one question. A key
no register row covers goes to a questionnaire named `unassigned`, so nothing is dropped.

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
  The example register has one since its v0.2.6: CargoQuote's OD-1 names compliance, which is
  ORG-0004 there (a stand-in, its decision 0011), and only `employee-4` of that unit closes it.
- **An approved answer lapses** six months after it was given: the statement reads *proposed*
  again until someone re-asks and a reviewer approves again. Set `KG_TODAY=YYYY-MM-DD` for a
  reproducible date, and `KG_CLOCK=pinned` in a pipeline so a command that would read the wall clock
  fails instead (task-0075).

**When a document's review falls due.** A statement a document's review verified is current for
the review months of the kind its key concerns, from your register's `metamodel/lifecycle.toml`:
`[review.kinds]` (the example register: capability 12, product 6), the shortest among the nodes
the key's row in your subject's `register_map.toml` names, else `[review] default_months` (knowgov
decision-0005). The load writes that date as the verification's `valid_until`. From the next day the
statement reads *validated*, its approval with it, and `gate_cli.py` lists a *lapsed* finding (major).
Read as of today, which is the default, your `--baseline` pipeline then reports the key as
`verified -> validated`, a regression. Renew it by a review: a reviewer of an owning unit approves the
statement in a review file, as above (a document's statement needs the role `closes`), and it is
current again for the key's months from the review's `on`. A verification by execution does not lapse by date. `--as-of YYYY-MM-DD` reads as of another
date, to see what falls due when; `--as-of record` reads as of your subject's `[record] as_of`, if you
pinned one.

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
seven tools, and all of them only read:

| Tool | What the assistant asks | What it gets back |
|---|---|---|
| `store_status` | What does the store hold? | the subject, the scenario loaded and when it was loaded (`loaded_at`), the task classes and their required keys, and the date the server reads reviews on; one store serves every subject, so a scenario another subject loaded reads as none loaded, named in `held_by_other_subject`, and every tool that reads a scenario refuses until your subject's is loaded |
| `gate_verdict` | May I build on the knowledge this task needs, or on these keys? | PROCEED, QUALIFIED or BLOCKED with the findings: the same report `gate_cli.py --no-load -f json` prints |
| `three_valued_answer` | What is known about this one key? | asserted, documented absent, or unknown, with where each statement came from and who verified it; and any statement a document change invalidated, with `superseded_by` naming the verified or approved statement that replaced it (none: the old value no longer holds and nothing does yet) |
| `evidence_bundle` | What exactly may I build on, and on what evidence? | the evidence bundle the governed arm reads, as text: the verdict and the policy, every required key's statements with their evidence, verifications, approvals and gaps, lapsed reviews, invalidated statements and what supersedes them, unchecked or flawed documents behind the keys, suspect derived outputs, and the documents the task names verbatim; for a task or for your own keys |
| `register_impact` | What does retiring or changing this register node touch? | your register's own impact walk from the node (the register's tag and commit, the node, its children listed but not walked unless the assistant asks with `children`, which walks every approved descendant as the register's decision 0014 does, every edge with whether it was followed, what it reaches with each node's owning unit), and the keys your subject's `register_map.toml` places on the node or on what it reaches, each with its owner, its anchor and the node it came through; with `children`, the keys resting only on a withdrawn descendant are listed last, flagged `withdrawn`; with a scenario loaded, each key's level, stale statements and suspect derived outputs as `gate_verdict` reports them for the task class the assistant names with `task` (`codegen` by default) |
| `proposal_impact` | What would this proposed product, capability or journey touch, and what does it lack, before anyone approves it? | the proposal (new nodes with provisional ids, links, the register nodes it reuses as they are or changed, proposed exceptions) read by your register's own checker and walks as if approved, every proposed element marked `hypothetical` and nothing stored: placement findings (a forbidden synonym; a node in no tool yet), link candidates D1 to D4 each `authored` or `inferred` and never more than `proposed`, C1 to C3 coverage before and after with the new gaps, what each reused node reaches before and after, what each new node rests on, each reused node's keys as `register_impact` reads them, the new nodes left unmapped, and which unit must approve what. Its walkthrough is in `demo/README.md` |
| `scenario_runs` | Which scenarios have been run, in which mode, and what did they show? | every scenario of your subject with its title and card line; what the record holds for it (deterministic results and the gate's verdict, the arms with how many runs and which model, the extra sources the subject declares); its runs newest first, each as its folder's `run.json` describes it (mode, model, as-of date, who started it, `page` or `mcp`, start, end, status, and the verdict of its results), or inferred, flagged `inferred`, for a folder from before `run.json`; the scenario the store holds and when it was loaded; and the run loading the store now, if any. Replay is not a run: it is the record shown, and nothing records it |

While a run of your subject is loading the store (its `run.json` reads `running` and the page has
rewritten it in the last 120 seconds; it does so every 30), `gate_verdict`, `three_valued_answer` and
`evidence_bundle` refuse and name the run, since a read then sees part of a graph. Ask again when it
has ended. A page that stops mid-run leaves a `running` file whose heartbeat goes stale; it no longer
blocks, and the page closes it as failed (`page restarted`) when it starts again.

The server reads the store as the page or a run left it. It never loads a scenario and never
writes to the store, the register or your instance; a change to the record is still a pull
request. Load what the assistant should see first, on the page or with a run.

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
inside the container, never the bare `cargo_quote`. Inside the stack's container it is already set
to the subject the page opens on.

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
list` then shows `knowgov` as connected, and inside a session `/mcp` shows its six tools.

The compose file publishes the page and Neo4j, not the server's HTTP port (8765), so this stdio
route is the one that works with the stack as it stands. For a stack started under another project
name (`docker compose -p knowgov-jef`, as the compose file's notes show), add the same `-p` after
`docker compose`. To ask about another subject than the one the page opens on, name its root in the
container: `exec -T -e KG_SUBJECT=/repo/subjects/jef_data_load app python harness/mcp_server.py`.

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
- "On scenario S1, may I build the codegen task? Which keys block it, and who owns each?" (`gate_verdict`)
- "On S1, what is known about `weight_kg|max`, and who verified it?" (`three_valued_answer`)
- "Give me the evidence bundle for codegen on S1 before you write any code." (`evidence_bundle`)
- "Read the gate on S1 as of 2027-06-01: which reviews will have lapsed?" (`gate_verdict` with `as_of`)

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
- **spec**: a `git commit` that carries a spec file (`--spec GLOB`, default `spec.md` at any depth);
- **push**: before `git push`.

Any other tool call gets no decision from it, and goes on through the normal permissions.

**What it does.** It runs `knowgov-gate.sh gate` with the task class the snippet names
(`--task codegen`; `--task-for spec=CLASS` for another class at one stage), reads the report, and
maps the exit code. Claude Code blocks a tool call when a hook exits 2 (exit 1 is only a warning there), so:

| Gate | Mandatory hook | Advisory profile (fail-open) |
|---|---|---|
| 0, PROCEED | the action goes ahead | the action goes ahead |
| 1, a finding | **blocked**, naming the findings and the route to approval: the key's owner answers it, a reviewer who is not the author settles it | **blocked**, the same |
| 2, cannot run (store unreachable, no subject, a timeout) | **blocked**, naming the gate as unavailable | goes ahead, with a warning that says FAIL-OPEN |
| a report for another task, or for `keys` | **refused**, blocked | **refused**, blocked |

A report for `keys` is one the MCP server's `gate_verdict` gives for a set of keys the assistant chose
itself; a mandatory check reads only the task class's own scope, which changes by pull request. The
snippets also set `"onFailure": "block"` (Claude Code 2.1.295 or later), so a missing script, a
crash or a timeout blocks too; the advisory one does not. A block is never lifted by the session
that hit it: the route is the owner's answer, or an exception from whoever owns the managed settings.

**Its settings.** The store, the subject, the scenario and the date are the gate's own `KG_*`
variables, as "Running the gates in your pipeline" lists them, in the environment Claude Code starts
with (the managed settings' `env` key, or the engineer's shell). Keep one store per worktree:
the gate loads the scenario before it reads, so two sessions sharing one Neo4j would overwrite each
other's load. Use rdflib in memory (`KG_STORE=rdflib` and no `KG_RDFLIB_FILE`: every run loads its
own), a `KG_RDFLIB_FILE` inside each worktree, or one compose project per worktree; and pass the MCP
tools' `scenario` argument, so a read of another session's load is refused.

`python3 knowgov_hook.py run -- COMMAND` maps any other check under the gate contract the same way,
and `decide()` is the mapping for a script that imports it. This repository's tests run the script
against PROCEED, BLOCKED, an unreachable store and a missing subject; only PROCEED lets the action
through (`tests/test_claude_hook.py`, live on rdflib in CI).
