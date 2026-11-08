# Reverse engineering a code base, and finding its knowledge gaps

This guide is for an organisation with a working program whose knowledge lives mostly in its code
and in a few people's heads. That might be before a rebuild or a migration, or before the person who
knows the program moves on. It shows how to write that knowledge down as specifications, and how to
turn everything that is missing, contradictory or unchecked into a *gap*: an item with an owner, a
route to that owner, and a recorded resolution. At the next commit, the same steps run again, and the
same checks find what changed.

Read [`docs/guide.md`](guide.md) first. It explains the words this guide builds on: an *instance*
(your own repository of documents and register), a *subject* (one body of documents the platform
loads), a *key* (one fact a task needs), the *gate* (the check that reads a task's keys and gives a
verdict), and *capture* (turning a person's answer into a recorded statement).

The process has eight steps. It was decided in `backlog/decisions/decision-0018`, and the brief behind
it, with its reasons, is `backlog/docs/doc-0032`. It has been run once, by hand, on J-F's daily data
load: pumllint's recreation experiment, which knowgov carries as the subject `jef_data_load`. That run
is the worked example throughout this guide. The first run that follows this guide is still to come
(`backlog/tasks/task-0220`). Section 5 lists what is not built yet.

## 1. The words

| word | meaning |
|---|---|
| reverse engineering | writing down, from a working program, what it does and what rules it follows |
| the original | the program you reverse-engineer, at one named commit, read and never changed |
| lane | the part of the original in scope: a named set of files |
| kit | the specification you write from the original: requirements, contracts, decision tables, diagrams and test scenarios, each statement carrying an id |
| statement | one sentence or row of the kit that says one thing, such as "sync shall refresh the corporate actions before the first bar fetch" |
| claim | what a statement is: `observed` (the original does this), `inferred` (someone's explanation or generalised rule, which may be wrong), or `intended` (the responsible person has accepted this behaviour as wanted) |
| existing artefacts | the documents the organisation already has about the lane: diagrams, contracts, decision records, comments in the code |
| pre-registration | a short document, written and frozen before anything is measured, that fixes the scope, the roles and the bars |
| bar | a result fixed in advance that a run must meet, such as "every exported table identical, cell for cell" |
| bounded inventory | a list you can count, such as the kit's 158 requirements, against which coverage is stated. Never a percentage of "all the knowledge" |
| role | one of three jobs, each done in its own context: *extraction* writes the kit, *recreation* rebuilds the program from the kit alone, *validation* runs the checks and compares |
| clean room | what a role is allowed to read, and what it is kept from |
| bundle | what the recreation role receives: the kit and any context the pre-registration names, never the original |
| oracle | a check that knows the right answer, such as the original's own test suite or a frozen output |
| finding | one thing a check reports, with a severity |
| gap | a finding the store keeps, with an owner (the organisation unit that answers for it) and a route (the questionnaire it goes to) |
| resolution | what the owner decided about a gap: a *slip* (a mistake, fixed by a new version of the document), a *choice* (deliberate, with a decision record), an *exception* (accepted as it is) or *open* (still undecided, kept with its owner) |

## 2. The eight steps at a glance

| # | step | what you do | the tool that runs it today | the record it leaves | where the record lives |
|---|---|---|---|---|---|
| 1 | Scope at a named commit | Name the original, its commit, the lane, the roles, the clean room and the bars | none: a document from [the template](reverse-engineering-preregistration.md) | the pre-registration, frozen | `<instance>/reverse-engineering/<run>/PREREGISTRATION.md` |
| 2 | Reverse-engineer into a kit | The extraction role writes the kit, each statement with its claim | none: a person or an assistant; `tools/check_subject.py` checks the result | the kit's files and its digest; the extraction role's private notes | the kit under `<instance>/artefacts/<kind>/`, named by `<instance>/subjects/<id>/subject.toml`; the notes under the run folder's `hidden/` |
| 3 | Gather the existing artefacts | Put the documents you already have beside the kit | `tools/connector.py` for a system of record's export; `tools/check_instance.py` | the gathered documents, in the same subject | `<instance>/artefacts/<kind>/`, or `<instance>/register/exports/` for an export |
| 4 | Lint both | Check the form of the kit and of the gathered documents, fixing nothing yet | `tools/preload_check.py` | the pre-load report | `<instance>/preload-report.json`, and a copy in the run folder |
| 5 | Load as a subject | Read everything into the store, so every finding becomes a gap with an owner | `harness/gate_cli.py`; `harness/capture.py questionnaire` | the gate report; one questionnaire per owner | the run folder |
| 6 | Address | Each owner resolves each gap; then lint again | `harness/capture.py ingest` and `review`; `tools/preload_check.py` with the first report | review files, answered questionnaires, new document versions, the re-lint report | `<instance>/subjects/<id>/captures/` and its `reviews/`; the run folder |
| 7 | Rebuild and grade, if you choose to | The recreation role rebuilds the lane from the bundle; validation grades it | the Arms, with the subject's oracle | the scored results | `<instance>/record/<subject>/` |
| 8 | Re-run on change | At a new commit, run steps 2 to 6 again on the same files | the same tools, with the earlier reports | the deltas | the next run's folder |

knowgov is the platform for steps 4, 5, 6 and 8, and step 3 uses your instance's own layout. Steps 1, 2
and 7 are roles, and what they leave is a record you keep.

Every record of a run lives in your instance, committed like any other change. Your instance is private,
so the records stay inside your organisation unless you decide to publish something (field 13 of the
template). `reverse-engineering/<run>/` is a suggested folder name, one per run, such as
`reverse-engineering/2026-11-20-billing/`. Nothing checks that folder, and the platform never writes to
it: what matters is that each run has one place, and that its pre-registration is never edited after
the freeze. J-F's first run is kept differently, because it came before this process: it lives, frozen,
in pumllint, and knowgov reads it and never writes to it.

## 3. Before you start: the roles and the bars

**Keep the roles apart.** Each role works in a context of its own: a separate person, or a fresh
assistant session. Never a copy of a session that has already read something, because a copy keeps
what it read.

- *Extraction* may read as much as the pre-registration allows. In J-F's run it read the lane's code
  only: no documentation, no tests, no README. That is a *full clean room*. In knowgov's own planned run
  (decision-0011, its point A1) the kit's author reads everything: code, backlog and documentation.
  Both are valid. Which one you choose is a parameter you write down in step 1.
- *Recreation* gets the bundle and nothing else: never the original, its tests or its history. If it
  could read the original, a faithful rebuild would show copying, not that the kit is enough.
- *Validation* runs the checks, launches the recreation, and compares. In J-F's run, the session that
  planned the run did this, and did not write the kit, because it had already read parts of J-F's
  documentation while planning.

**Fix the bars before measuring.** The pre-registration names, before anything runs:

- what counts as a faithful rebuild, split into what is *gated* (must hold) and what is only
  *reported*. J-F's run fixed eleven measures in advance. Eight carried a severity if they failed, the
  gravest being the exported tables identical cell for cell and the health check never green where the
  original is red. Three were only reported, such as the original's own tests run against the rebuild;
- the bounded inventories every coverage figure is stated against;
- what each outcome would mean, including failure. A failed expectation is recorded with the same
  prominence as a confirmed one.

Without bars fixed in advance, step 7 would measure whatever came out, and step 5 would have no
denominator.

## 4. The steps

The commands below run from a checkout of knowgov. Two variables tell them which subject and which
register to read:

```bash
export KG_SUBJECT=/path/to/instance/subjects/<id> KG_REGISTER=/path/to/instance/register RUN=/path/to/instance/reverse-engineering/<run>
```

In plain English: `KG_SUBJECT` is the folder of the subject you are building, and `KG_REGISTER` is
your organisation's register inside the same instance. Every knowgov command after this reads them.
`RUN` is the run's own folder, where the commands below write their reports.

### Step 1: scope at a named commit

Copy the skeleton at the end of [the template](reverse-engineering-preregistration.md) into
`$RUN/PREREGISTRATION.md` and fill in every field. Of its fifteen fields, these fix the run's scope:

- the original and its commit;
- the lane's file set, in scope and out of scope, with the reason for each exclusion;
- the roles, and who or what plays each one;
- the clean room: what each role may read;
- the bundle's contents;
- the bounded inventories;
- the bars, gated and reported, and what each outcome means.

Then commit the file, and write its commit and its SHA-256 digest into its own freeze line. From then on,
nothing above its *Results* heading changes. Results are added below it as each step completes. If the
scope must change, freeze a new version and say so.

The template's worked example is J-F's first run, field by field.

### Step 2: reverse-engineer into a kit

The extraction role reads the original, as the clean room allows, and writes the kit. A kit has up to
five layers, and each layer is a kind of document a knowgov mapper reads:

| layer | folder under `artefacts/` | mapper | where a statement's claim is written |
|---|---|---|---|
| requirements, as a JSON list of `{id, kind, statement, basis}` | `textual-requirements` | `requirements_json` | `"claim": "observed"` on the item |
| contracts in prose | `specification-prose` | `contracts_markdown` | a line `Claim: observed` in a part |
| decision tables, as DMN files | `decision-tables` | `dmn_decisions` | `claim: observed` in a decision's or a rule's description |
| diagrams in PlantUML, each listing the requirement ids it realises | `plantuml-models` | `plantuml_realises` | a comment line `' claim: observed` |
| test scenarios in Gherkin, tagged with requirement ids | `acceptance-scenarios` | `gherkin_tagged` | a tag `@claim:observed` on the Feature, a Rule or a Scenario |

Name the kit's files in the subject's `subject.toml`, as [`subjects/README.md`](../subjects/README.md)
describes, and give its requirement ids a pattern of their own (`[rules] requirement_id_pattern`), such as
`JDL-\d{3}` for J-F's.

**Mark every statement's claim.** This is what keeps a fact about the program apart from a guess about
it, and from a decision about it:

- `observed` loads as read from the document (`extracted`). It can become *verified* when a scenario the
  kit tags runs and passes on the original.
- `inferred` loads as `inferred`, and never rises above *proposed*: nothing verifies it, and no review
  may approve it.
- `intended` loads as written by a person (`authored`). It is approved only when the subject declares who
  vouches for it (`[verification] authored` and `approval`, decision-0009).

A statement with no claim loads as before. A fact resting on statements of different claims takes the
most cautious of them. [`subjects/README.md`](../subjects/README.md), "The claim", has the full rules.

**Keep the extraction role's notes apart from the kit.** In J-F's run, the extraction role also wrote a
map from each requirement to the code it was read from, and a list of quirks: places where a comment
says one thing and the logic another, such as a column documented as milliseconds that holds seconds.
These notes never go into the bundle, because the map would let a rebuild copy the original. Keep them
under `$RUN/hidden/`.

Check the subject before you go further:

```bash
python tools/check_subject.py "$KG_SUBJECT" --register "$KG_REGISTER"
```

In plain English: this reads the subject without loading it. It refuses a claim that is not `observed`,
`inferred` or `intended`, a key that is not written `<entity>|<predicate>`, and a register node the
register does not hold. It warns when a key a task needs is yielded by no document but a near one is,
and names that one. It exits 0 when the subject holds, 1 when it does not, and 2 when it cannot run.

### Step 3: gather the existing artefacts

Put the documents the organisation already has about the lane under `artefacts/<kind>/`, in the
folder for their kind, and name them in the same `subject.toml` as the kit. An export from a system of
record, such as a modelling tool, lands in your register with the connector:

```bash
python tools/connector.py /path/to/instance --system aris /path/to/the/export/
```

In plain English: this copies the export into `register/exports/<system>/<date>/`, with a manifest of
what it carries and a comparison against your register. It never overwrites an earlier export. Then
check the whole instance:

```bash
python tools/check_instance.py /path/to/instance
```

In plain English: this confirms every document a subject names exists, lists each one with the mapper
that reads it, and runs `tools/check_subject.py` on every subject. It exits 0 when the layout holds.

This is the step where missing documentation becomes visible. Once loaded (step 5), a key the kit states
and no existing artefact states is *undocumented*: a fact about your documents, not a fault in the code.
A key an existing artefact states differently from the kit is a *conflict*, and the store holds both
until someone rules.

The joining is still manual. An existing document that does not use the kit's ids yields keys that do not
match the kit's. The subject check's warning names the nearest key, and you align the two by hand.

In J-F's first run, the existing diagrams and data contract were deliberately read only after the
rebuild was scored, so that they could not influence the kit. Comparing them then found 25 claims in the
existing diagrams that the code contradicted. Under this process, they are gathered and loaded beside
the kit, so such a disagreement shows up as a conflict at step 5 rather than after the fact.

### Step 4: lint both

*Linting* means checking each document's form with the tool for its kind, before anything is read into
the store:

```bash
python tools/preload_check.py /path/to/instance -f json -o $RUN/lint-first.json
```

In plain English: this checks every document under `artefacts/` with its kind's linter where one runs
here: pumllint for PlantUML, markdownlint for prose, gplint for Gherkin, dmnlint for DMN, bpmnlint for
BPMN and Spectral for API contracts. It lists every other file as *unchecked*, naming the tool that would
check it, so no gap is hidden. It writes the report to `$RUN/lint-first.json` and exits 0 when clean, 1 on
a finding at or above `major`, and 2 when it cannot run.

Copy the report to `preload-report.json` at the root of your instance. The load in step 5 reads it there
(or wherever `KG_PRELOAD_REPORT` points) and records, for each document version, what the report said
about those exact bytes.

**Fix nothing yet.** Every finding is a candidate gap, and only the document's owner can say whether it
is a slip, a choice or an exception. A finding fixed before the load leaves no record that it was there.

Three checks from J-F's run do not run here yet (task-0217): pumllint's `trace --features`, which checks
that every requirement is drawn in a diagram and tested by a scenario; a glossary check; and a check that
the decision tables leave no input uncovered. Until they do, run pumllint's trace yourself on the kit and
keep its report in the run folder. Two of the run's code-level lists also have no tool or format yet: the
code the scenarios never execute (J-F's run counted 141 of the lane's 1,520 code statements, as a coverage
tool counts them), and the quirks. Keep them as notes in the run folder.

### Step 5: load as a subject

Loading reads every document into the store, one statement at a time, and turns what the checks found
into gaps:

```bash
python harness/gate_cli.py --subject "$KG_SUBJECT" --task <class> -f json -o $RUN/gate-first.json
```

In plain English: this loads the subject into a private store in memory, runs the rules, reads the keys
the task class `<class>` needs, and writes a report of findings, each with a severity. A finding about a
key names the key's owner and the route: the questionnaire it goes to. A finding about a document's form
names the document's owner: the unit that owns the keys the document states. It exits 0 when nothing is at or above `blocker`, 1 when something is, and 2 when it cannot run. A model or
an assistant that asks through knowgov's MCP server (`gate_verdict`) reads the same report.

What the experiment found, and what each becomes:

| found in the experiment | becomes in knowgov | the finding |
|---|---|---|
| a lint finding | a gap on the document version, with its owner and route | kind `lint`, at the linter's severity, at most `major`. It never lowers a key's level |
| a quirk: the comment says one thing, the code another | an observed statement and an existing artefact's statement on the same key | a conflict: the key is *disputed* until someone rules |
| missing documentation | a key with an observed statement and no intended one | below *approved*, if the task requires approved (below) |
| a requirement whose scenarios never pass on the original | a key whose statement no execution verifies | below *verified*: kind `key`, `major` |
| code no requirement reaches | a code file no row of `code_map.toml` maps to your register | listed as *UNMAPPED* by `tools/check_instance.py`; on a change, `unmapped` from `harness/trace.py check` |
| a requirement no scenario verifies | a gap the load records against the requirement: no verifying scenario | among the load's gaps; on a key the task needs, also kind `key` |

**Require approved where it matters.** A behaviour the kit observed, and its scenarios confirm on the original,
is *verified*: it shows the original does it, not that anyone wants it. A defect in the original passes that
test too. To keep such a behaviour from reading as safe to build on, give the task class
`require_approved = true` in `subject.toml`. A key that is verified but not approved then gets an
`intended` finding, routed to its owner, until a person approves it.

Then write one questionnaire per owner, from the gaps:

```bash
python harness/capture.py questionnaire --task <class> --out $RUN/questionnaires/
```

In plain English: this loads the subject privately again, asks the gate which keys are missing or weak,
and writes one file per owning unit, each listing what the store holds now and one question per key.

If your instance maps code to the register (a `code_map.toml`), `tools/check_instance.py` (step 3) has
already listed as *UNMAPPED* every code file no row maps: code that reaches no part of your register, and
so no knowledge.

### Step 6: address

Each owner resolves each gap. What a resolution looks like depends on the gap:

| resolution | for a lint gap | for a knowledge gap |
|---|---|---|
| slip | fix the document. The next load reads a new version, and the re-lint below shows the finding gone | fix the document, or answer the questionnaire |
| choice | a review file with `[[resolves]]` and `resolution = "choice"`, the review's `record` naming the decision record | a ruling in a review file, citing the decision record |
| exception | `[[resolves]]` with `resolution = "exception"` | an answered questionnaire, which a reviewer then approves |
| open | `[[resolves]]` with `resolution = "open"`: the gap stays, at its severity, with its owner | the key stays open, with its owner |

An answered questionnaire goes in with:

```bash
python harness/capture.py ingest $RUN/questionnaires/<file>.toml
```

In plain English: this checks the answers (a handle, never a name; a date not in the future) and saves
them in the subject's `captures/` folder, which you commit. Every later load reads them, as *proposed*
statements by that person.

A review, which a second person writes and which may rule on answers, settle a conflict, close a declared
gap or resolve a lint gap, goes in with:

```bash
python harness/capture.py review $RUN/review-<date>.toml
```

In plain English: this checks the review against what the store holds and against your register's list
of who may do what, then saves it in `captures/reviews/`. It refuses a review that breaks a rule and names
the rule. For a lint gap, the `gap` to write is the finding's `ref` in the gate report. Only someone in the
document's owning unit with the role `closes` may resolve it, and nobody approves their own statement.
[`docs/guide.md`](guide.md) §6 and [`instance/README.md`](../instance/README.md), "Capturing what people
know", give the file's form.

Then lint again, at the same tool versions, against the first report:

```bash
python tools/preload_check.py /path/to/instance --previous $RUN/lint-first.json -f json -o $RUN/lint-relint.json
```

In plain English: this runs the same check and also lists, against the first report, each finding as
*new*, *gone* (a slip, when the document's bytes changed) or *kept*. The kept ones should each carry a
recorded choice, exception or open item. That second report is the evidence that the slips are gone.

### Step 7: rebuild and grade, if you choose to

This step answers a different question: is the kit enough to rebuild the lane? The recreation role gets
the bundle, in a fresh context, and rebuilds. Validation then runs the oracle on the rebuild and compares
it with the original against the bars of step 1. In knowgov, the *Arms* run a model on a subject
(`[arms.agent]` in `subject.toml`), and the subject's oracle grades the result. The Arms are off until
you name a model and its key ([`docs/guide.md`](guide.md) §10).

This is only ready-made for J-F's subject, whose oracle runs the kit's suite
(`subjects/jef_data_load/oracle/jef_suite.py`). A new code base needs its own oracle adapter and a place
for the rebuild to run. State what the rebuild covered against each bounded inventory, never as a share
of everything. Keep the scored results under `record/<subject>/`.

In J-F's first run, two rebuilds, with and without the diagrams, both produced the exported tables
identical in 14 of 14 and never a health check green where the original was red. 22 of the 157 compared
outputs differed. Two kinds of gap in the kit explained some of them, and the rest differed by
construction, such as a module name. After one revision of the kit, 11 remained, all by construction.

### Step 8: re-run on change

At a new commit of the original, or when an existing artefact changes, run the steps again on the same
files, into a new run folder: step 2 updates the kit's files, so the next load reads new versions; step 4
lints against the last report with `--previous`; step 5 loads again.

Each instrument sees a different kind of change, and none sees everything:

| instrument | sees | misses |
|---|---|---|
| the re-lint (`tools/preload_check.py` with `--previous`) | a document's form that changed | anything the document's form does not show |
| the review files, bound to what they ruled on | a person's ruling or close whose statement changed: it is no longer applied, and the gate reports it as an `act` finding to its owner | a change no one had ruled on |
| `harness/trace.py check`, once you have recorded what was built from the kit (`harness/trace.py register`) | code built on a statement that has since changed (`suspect`); a recorded code file that changed (`drift`) | whether a changed file still behaves the same |
| the kit's scenarios, run on the new commit | behaviour that changed | behaviour no scenario covers |

Only running the scenarios tells a harmless edit from a change of behaviour. The first test of this is
planned on J-F's subject (task-0219): two small changes to the code, one that moves behaviour and one
that only reorders lines, with the expected result of each instrument written down first.

## 5. What is not built yet

- **Steps 1 and 2 have no tool.** The template gives step 1 its form. The extraction is a person's or an
  assistant's work, checked afterwards by `tools/check_subject.py`. The assistant prompts knowgov offers
  (`new_subject`, `add_artefact`) help write a subject's manifest, not a kit.
- **No command runs the steps in order.** Each command exits 0, 1 or 2, so a script of your own can chain
  them; nothing in knowgov does yet.
- **Step 4 lacks three checks** (task-0217): pumllint's trace, the glossary check and the decision-table
  gap check.
- **The code-level lists have no format:** the code the scenarios never execute, and the quirks. They stay
  notes in the run folder, and no mapper reads them.
- **Joining existing artefacts to the kit is manual** (step 3).
- **Step 7 needs an oracle adapter per code base.** Only J-F's exists.
- **The MCP server reads results; it runs no step.** An assistant connected to it sees the `lint` and
  `intended` findings in `gate_verdict`, and can check a proposed subject with `subject_check`. It cannot
  lint, load or review.
- **The process has one run behind it,** J-F's, done before most of these tools existed. The first run
  under this guide (task-0220) and the re-run probe (task-0219) are planned.

## 6. Where to read more

- [The pre-registration template](reverse-engineering-preregistration.md), with J-F's first run, field by
  field.
- [`subjects/README.md`](../subjects/README.md): a subject's manifest, "The claim" and `require_approved`.
- [`instance/README.md`](../instance/README.md): the instance's layout, the pre-load check, capture and
  reviews, tracing code to knowledge.
- `subjects/jef_data_load/vendor/docs/recreate-experiment.md` and
  `subjects/jef_data_load/vendor/recreate_experiment/PREREGISTRATION.md`: J-F's first run, as pumllint
  recorded it.
- `backlog/decisions/decision-0018` (the process), `backlog/docs/doc-0032` (the brief and its reasons),
  `backlog/decisions/decision-0011` (knowgov's own planned run).
