# Reverse engineering a code base, and finding its knowledge gaps

This guide is for a team that has working code and wants two things from it: a written description
of what the code does, good enough to rebuild it from, and a list of what nobody has written down.
It walks the process step by step, says which tool runs each step today, what record each step
leaves and where that record lives. Its source is knowgov's decision-0018 and its brief, doc-0032,
both under `backlog/`. The first run of the process, on a real program, is pumllint's recreation
experiment (`recreate_experiment/` and `docs/recreate-experiment.md` in pumllint).

## The words this guide uses

| word | meaning |
|---|---|
| reverse engineering | reading existing code and writing down what it does, as documents someone else can build from |
| kit | the documents that come out of it: requirements, contracts, decision tables, diagrams, and acceptance scenarios that can be run |
| claim | what one statement in the kit is: *observed* (the code does this today), *inferred* (a guess at a rule or a reason, not yet confirmed) or *intended* (the person responsible for the behaviour has accepted it) |
| existing artefacts | the documents your organisation already has about the same code: models, specifications, wiki pages, decision records |
| linter | a program that checks a document's form and reports findings, the way a spell checker reports words |
| gap | something knowgov cannot answer from the documents: a missing statement, a contradiction, a vague one, or one nobody has confirmed |
| owner | the unit in your register that answers for a fact, and so receives the questions about it |
| subject | the set of documents knowgov loads together, with the task they serve (`subjects/README.md`) |
| instance | your organisation's own copy of knowgov's layout, kept in your own repository (`instance/README.md`) |
| pre-registration | a short document, written before anything is measured, that fixes what will be done and how success is judged |

## The process in one paragraph

Pick the code and freeze it at one commit. Have someone, usually an AI assistant, read it and write
the kit, marking every statement as observed, inferred or intended. Collect the documents your
organisation already has about the same code. Run the linters on both, the new kit and the old
documents, without fixing anything first. Load both into knowgov as one subject: every finding, every
contradiction between what the code does and what a document says, and every behaviour no document
mentions becomes a gap, sent to the person who owns it. Those people answer, correct or decide. If you
want proof that the kit is enough, have a second, independent assistant rebuild the code from the kit
alone and compare the result with the original. When the code changes, run the process again on the
new commit: knowgov shows which statements went stale and which work rested on them.

## Before you start: three rules

**Fix the bars first.** Write down, before anything runs, what counts as success: which outputs of
the rebuild must be identical, which are only reported, and what list a coverage figure is counted
against. Decide these after seeing the numbers and you will tend to choose the ones that look good.
The template beside this guide, `docs/reverse-engineering-preregistration.md`, lists every field.

**Keep the roles apart.** Three roles take part, and each sees something different:

| role | does | may read |
|---|---|---|
| extraction | writes the kit from the code | everything it is allowed to: the code, and, if your pre-registration says so, its tests and documents |
| recreation | rebuilds the code from the kit (step 7) | the frozen kit and the bundle the pre-registration names; never the original code, its tests or an earlier rebuild |
| validation | compares the rebuild with the original and sorts every difference | the original, the rebuild and the reference outputs |

If one person or one assistant session plays two roles, a successful rebuild proves less: what the
rebuilder already knew fills the kit's holes without anyone noticing.

**Never report "we captured 80 % of the knowledge".** Nobody knows how much knowledge there was, so
there is nothing to divide by. Report counts against a list you wrote down: "158 requirements, 12
contradicted by the code, 33 never exercised by a test".

## The eight steps

Each step says what to do, which tool does it today, what record it leaves, and where to keep that
record. Keep every run's records together in your instance's repository, for example under
`reverse-engineering/<run>/`, so a later run can be compared with this one.

### Step 1. Scope at a named commit

Choose the part of the code to describe (the *lane*: a list of files or folders) and the commit to
read it at. Fill in the pre-registration template: the lane, the commit, who plays each role, what
the extraction role may read, the bars, and what the rebuilder will be given.

- **Tool:** none to run. `docs/reverse-engineering-preregistration.md` is the template.
- **Record:** the filled-in pre-registration, committed before step 2 starts.
- **Where:** your instance's repository, in the run's folder.

### Step 2. Reverse-engineer the code into a kit

The extraction role reads the lane and writes the kit, in the conventions knowgov's bundle mappers
read (`subjects/README.md`, the `requirements_json`, `contracts_markdown`, `dmn_decisions`,
`plantuml_realises` and `gherkin_tagged` mappers). Each requirement gets a stable id. Each statement
says what it is with its claim:

- `observed`: the code does this today, and a scenario run on the original shows it;
- `inferred`: a rule or a reason read into the code, not confirmed by anyone;
- `intended`: the person responsible has accepted it as the behaviour wanted.

Keep the three apart even when they disagree. A defect in the code must not become the wanted
behaviour just because the code does it; keeping it on purpose takes an explicit decision.
`subjects/README.md` ("The claim") shows where each kind of document carries the claim. A statement
with no claim is read as before, as if no one had said what it is.

- **Tool:** an assistant session, briefed with the pre-registration. Then `pumllint` on the
  diagrams. The kit's acceptance scenarios are run on the original and must all pass: a scenario that
  fails on the code it describes is wrong.
- **Record:** the kit, a list of its files with their digests (a fingerprint of each file's bytes),
  and a private provenance map: which source lines each statement rests on. The provenance map is never
  given to the recreation role.
- **Where:** the run's folder. Freeze the kit once it is written: a later correction is a new version.

### Step 3. Gather the existing artefacts

Collect what your organisation already has about the same code: process models, decision tables,
interface contracts, wiki pages, comments in the code itself. Put each under your instance's
`artefacts/<kind>/` folder, where `instance/kinds.toml` lists the kinds. An export from a modelling
tool such as ARIS can be landed with `tools/connector.py`.

```bash
python tools/check_instance.py my-instance --json
```

This reads your instance's folders and reports, as JSON, any document in a place no kind covers and
any subject whose manifest does not hold. It changes nothing.

Missing documentation shows up here: a behaviour the kit states and no existing artefact mentions is
undocumented. That is a fact about your documents, not a defect in the code.

- **Record:** the artefacts as you found them, each with its digest.
- **Where:** your instance's `artefacts/` folder, at a commit you note in the run's folder.

### Step 4. Lint both, the kit and the existing artefacts

Run every linter on both sets as they are. Fix nothing first: every finding is a question, and only
the document's author can say whether it is a slip or something real nobody wrote down.

```bash
python tools/preload_check.py my-instance --layout -f json -o my-instance/preload-report.json
```

This runs the linters knowgov knows for each kind (pumllint for PlantUML, Spectral for API
contracts, markdownlint, gplint, bpmnlint and dmnlint), writes one report with every finding, its
file and its severity, and exits 1 if any finding is at or above the threshold (`--fail-on`). With
`--baseline`, it fails only on findings that were not there before. The report goes to the root of
the instance, where step 5's load reads it; keep a copy in the run's folder as the first report.

After the linters, the same command runs three checks that read documents together:

- `pumllint trace --features` joins the requirements to the scenarios that test them and the diagrams
  that show them. It lists requirements with no test, and tests citing a requirement that does not
  exist.
- A glossary check lists terms used in three or more requirements and defined nowhere in your
  glossary.
- A decision-table gap check lists inputs no rule covers and inputs two rules claim.

Their findings are in the same report, each with the document it is about.

Keep one more list here: the code's quirks. A quirk is a place where the code and its own comments
disagree. In the experiment, for example, a comment said a time was in milliseconds while the code
stored seconds. A quirk is a question for the code's owner, not a fix.

- **Record:** the lint report, the trace report, and the quirk list, each with the tools' versions.
- **Where:** the run's folder.

### Step 5. Load as a subject, so findings become gaps with owners

Write a subject manifest (`subject.toml`) naming the kit's documents and the existing artefacts, and
the task they serve: the facts a rebuild, a change or a review needs, called *keys*. Check it before
loading:

```bash
python tools/check_subject.py my-instance/subjects/my-lane --json
```

This runs the mappers on your documents without loading anything, and reports a key no document
states, a document no mapper can read, and a claim it does not know. Then ask the gate:

```bash
python harness/gate_cli.py --subject my-instance/subjects/my-lane --scenario S0 --task rebuild -f json -o gate.json
```

The gate loads the subject into a private store, with step 4's report from the instance's root, and
answers with a verdict: PROCEED (build on it),
QUALIFIED (build, naming each assumption) or BLOCKED (do not build). A task that must rest on wanted
behaviour, not only on what the code does today, says `require_approved = true` in `subject.toml`
(`subjects/README.md`): then a fact shown by running the original, but never accepted by a person,
keeps the gate from PROCEED. Its findings name each gap, the
key it concerns, the owner of that key, and the questionnaire the owner answers.

What turns into a gap:

| what you found | what knowgov makes of it |
|---|---|
| a quirk: the code says one thing, a comment or document another | two statements of one key that disagree: a dispute, until the owner rules |
| a behaviour no existing artefact mentions | a key with only an observed statement: below approved; with `require_approved = true` on the task (the intended bar), the gate does not read PROCEED until a person intends it |
| a behaviour the kit states and no scenario exercises | a key with no execution: below verified |
| an inferred rule | a statement that stays proposed, however often it is repeated |
| a requirement no scenario tests | a gap of its own |
| a lint finding | a lint gap on that document, a gate finding naming the document's owner and the route to them; it never lowers a key's level, because it is about the document's form |

- **Record:** the subject manifest and the gate's report.
- **Where:** the subject's folder in your instance, and the run's folder for the report.

### Step 6. Address the gaps

Send each owner the questions about their keys, and record what they answer:

```bash
KG_SUBJECT=my-instance/subjects/my-lane python harness/capture.py questionnaire --scenario S0 --task rebuild --out questions/
```

This writes one questionnaire per owning unit, listing the keys the gate could not settle. Each
owner fills in their file; the answers come back in as statements attributed to the person who gave
them:

```bash
KG_SUBJECT=my-instance/subjects/my-lane python harness/capture.py ingest questions/ORG-0001.toml
```

They stay proposed until a second person reviews them:

```bash
KG_SUBJECT=my-instance/subjects/my-lane python harness/capture.py review my-review.toml --scenario S0
```

This checks the review file (who approves, which statements, why) against the rules in
`backlog/decisions/` and refuses one that breaks a rule, naming it. A model's inferred statement can be
rejected but never approved this way.

Each finding ends as one of four, as the pumllint experiment's knowledge-transfer plan names them:

- a **slip**, corrected in the document, which becomes its next version;
- a **choice**, kept on purpose and recorded with its reason as a decision;
- an **exception** nobody had written down, which becomes a new statement;
- **open**, when nobody knows, which stays a gap with its owner.

A lint gap ends the same way. A slip is corrected in the document, and the next version carries no
finding. For a choice, an exception or an open question, the document's owner adds a `[[resolves]]`
entry to a review file. It names the gap, the resolution and a digest of the finding's text, so a
changed finding needs a new ruling. A gap resolved as a choice or an exception then shows at info.

Then run step 4's linters again at the same versions, against the first report:

```bash
python tools/preload_check.py my-instance --previous first-report.json -f json -o my-instance/preload-report.json
```

Here `first-report.json` is the copy of step 4's report kept in the run's folder. `--previous` adds a
delta to the report. It sorts each finding as new, gone or kept, and a finding
that is gone because its file's bytes changed is counted as a slip. The delta only compares runs
made at the same tool versions. This second report is the evidence that the slips are gone.

- **Record:** the questionnaires, the answers, the review files, the decisions and the second lint
  report.
- **Where:** the subject's `captures/` folder, and the run's folder.

### Step 7. Optionally, rebuild and grade

This step answers a different question: is the kit enough to rebuild the code? A fresh assistant,
the recreation role, receives only the frozen kit and the bundle the pre-registration names. It
rebuilds the code. The validation role then runs the kit's scenarios and the reference comparison on
the rebuild, and sorts every difference into one cause: the kit left something out, the rebuild got it
wrong, a scenario is wrong, or the original is wrong.

- **Tool:** knowgov's arms (the model connection) and its contained worker, which runs model-written
  code with no network and no secrets (`docs/security.md`); the subject's own test suite as the oracle.
  In the pumllint experiment, three rebuilds from the kit alone matched the original on every exported
  number.
- **Record:** the rebuild, the scores against the bars of step 1, and the list of differences with
  their causes.
- **Where:** the run's folder. Never rebuild from a kit someone has corrected while watching the
  rebuild: that is a repair, not a test. A correction makes a new kit version, and an independent claim
  needs a fresh rebuild.

### Step 8. Re-run on change

When the code moves to a new commit, or a document changes, run the steps again on what changed:
re-extract the parts of the kit the change touched (a new kit version), and ask the gate again,
comparing with the earlier report:

```bash
python harness/gate_cli.py --subject my-instance/subjects/my-lane --scenario S0 --task rebuild --baseline gate.json -f json -o gate-after.json
```

This loads the documents as they now stand and exits 1 only on what got worse since `gate.json`.
The reviews and rulings people gave in step 6 apply again, each bound to the statement it ruled on:
if that statement changed, the ruling is not carried over to the new value, and the gate lists it,
naming who gave it and what changed, so it goes back to its owner.

```bash
python harness/trace.py check --instance my-instance --ledger ledger.json -f json -o trace.json
```

This compares the work you registered with `harness/trace.py register` (code, generated files, a
rebuild) with what it rested on, and reports what is now suspect because a statement under it
changed, and any registered file whose bytes changed since it was registered. A changed file is
reported as minor, the second-lowest of five severities. Unless you say otherwise, the command fails
only on the highest, blocker. To make a changed file stop a pipeline, add `--fail-on minor`.

Know what each instrument sees. The gate sees an edit to a document. trace sees that a registered
file's bytes changed, but not whether its behaviour did. Only running the kit's scenarios on the new
commit shows a change of behaviour. Run all three, and note which caught what. knowgov's first test of
this step planted two changes in the J-F subject's public rebuild, two lines of one file
(`subjects/jef_data_load/probes/h7/RESULTS.md`). The gate saw neither change, because no document
changed. trace saw both, but could not tell them apart. Only the scenarios separated them: 2 failing cases
for the change that shows only when a download fails, and 19 for the other.

- **Record:** the new gate report, the trace report, the scenarios' results on the new commit.
- **Where:** a new run folder beside the first, naming the commit it read.

## What this process does not do

- It never tells you that a well-formed, fully traced document is right. A linter checks form; the
  scenarios check that the code does what the kit says; only the people who own the behaviour can
  say it is the behaviour wanted.
- It does not edit your code, your documents or your modelling tool. Every correction is made by a
  person, in the document's own home.
- It gives no figure for "how much knowledge was captured" (see "Before you start").

## Further reading

- `docs/reverse-engineering-preregistration.md`: the template for step 1, with the pumllint
  experiment's first run filled in as the example.
- `subjects/README.md`: the subject format, the kit's mappers and the claim.
- `instance/README.md`: your instance's layout, capturing what people know, and the review rules.
- `docs/guide.md`: knowgov for adopters, from the first load to the gate in a pipeline.
- pumllint, `docs/recreate-experiment.md` and `recreate_experiment/`: the first run, its kit and its
  results.
