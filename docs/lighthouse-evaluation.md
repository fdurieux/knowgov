# Evaluating knowgov: the lighthouse protocol

This document is for whoever has to decide whether knowgov works for their organisation: an
architect, a platform owner, or the person running a pilot. It lists the questions an evaluator of
a governed-knowledge platform asks, says what the stack offers as evidence for each one, and says
how to collect that evidence.

The protocol has two halves:

- **The rehearsal**, on public, synthetic content: the CargoQuote kit, served from the example
  instance, and J-F's data-load kit. Anyone can run it, and its evidence is public. One script
  collects it.
- **The pilot**, on the lighthouse organisation's own documents and register. It uses the same
  checklist. Its evidence stays in the pilot's private record and never comes into this
  repository.

The criteria come from an assessment of operational ontology platforms that the maintainer read
against knowgov (`backlog/docs/doc-0013`, §2 and §5 candidate 8).
No banking scenario is used anywhere, in the rehearsal or in the pilot checklist.

## Running the rehearsal

In a Python 3.12 environment with the pins of `demo/Dockerfile` installed (the
[`demo/README.md`](../demo/README.md) lists them):

```bash
KG_STORE=rdflib python tools/lighthouse_evidence.py runs/lighthouse
```

To use the Neo4j store, leave `KG_STORE` unset and have the database running. The script works
in four steps:

1. It builds the example instance (`tools/example_instance.py`) under `runs/lighthouse/instance`.
2. It collects CargoQuote's evidence from that instance, and J-F's from its subject root
   (`subjects/jef_data_load`; the example instance carries CargoQuote only).
3. It digests the instance before and after, to show the collection wrote nothing into it.
4. It writes `evidence.json` (everything) and `evidence.md` (a summary per subject).

It exits 0 when every item was collected and agrees with the subject's record, 1 when one does not,
and 2 when it could not run. A full run on the in-memory store takes a few minutes. No model is
called.

What it collects for each subject:

| item | what it shows | how |
|---|---|---|
| walk | what a change to a register node reaches, and the statements behind it | the register's own impact walk from every node the subject's register map names; then, on the first scenario, the statements each node's cited anchor reaches in the store |
| gate | whether a task may build on its knowledge | `harness/gate_cli.py` on every scenario, with each verdict next to the record's |
| three-valued answer over MCP | what an assistant sees when it asks | the read-only MCP server over stdio, on the store each gate left. Its `gate_verdict` must equal `gate_cli.py --no-load`. Its `three_valued_answer` must carry provenance. The store's census must be unchanged |
| invalidation | what a document change does | for a scenario with a later version (CargoQuote S6): `--stage 2`, then `--stage 2 --reverify`. It records what was invalidated, what supersedes it (`superseded_by`) and the code marked suspect |
| export manifest | that the register's copy of the documents is the subject's | every file digest in the register's export manifest, checked against the subject's bytes, and the reconciliation record next to it |
| cost | what the evidence costs to produce | wall-clock time per step and the store's size |

## The seven criteria

For each criterion: the question an evaluator asks, what the stack offers today, the rehearsal's
evidence, and what the pilot must show. "Met" below means met on public, synthetic content. Only
the pilot can say whether it holds on real documents.

### Semantic modelling

*Does the platform hold a typed model of the business: its parts, their relationships, and who
owns them?*

- **The stack today:** met, on synthetic content.
  - The register (ieam-register, vendored under `demo/register`) holds seven taxonomies and ten
    relationship types, with an owner on every node and every link (`metamodel/types.toml`).
  - Statements in the store are typed by key (entity and attribute), basis and status.
- **Rehearsal evidence:** the walk item. It counts the register's nodes, lists the nodes each
  subject's map names, and shows what each one reaches.
- **Gap:** the register has no taxonomy for decision models. Decision tables and DMN files stay
  documents whose statements knowgov reads. A proposal to the register is recorded as task-0074.
- **Pilot:** the pilot's register checks clean (`tools/check_instance.py`). Every key the pilot's
  tasks need maps to a register node. Each node and link has an owner from the pilot's
  organisation.

### Traceability

*Can you follow a fact from its source document to what it affects, and back?*

- **The stack today:**
  - Met on the register: the impact walk follows approved links only and stops at retired nodes
    (register decision 0010).
  - Met from a node to its statements: task-0046, at the grain of the cited anchor.
  - Met through change: in CargoQuote S6 a source change invalidates four statements, ends their
    verifications and marks the code built from them suspect.
  - Partial from code back to knowledge: tasks 0050 and 0051.
- **Rehearsal evidence:**
  - The walk item, and its statements at each anchor.
  - The invalidation item: the four statements, the code marked suspect, and after
    re-verification, `superseded_by` naming each statement's replacement.
- **Pilot:** one real change to one real document, followed from the document to the statements,
  the register nodes and any code it reaches. Someone who knows the change confirms the result
  matches what they expected.

### Knowledge quality

*Does the platform know which facts are verified, and does it refuse to treat a guess as a fact?*

- **The stack today:** met.
  - Every statement carries its basis (authored, extracted, elicited, inferred, assumed or
    hypothesised) and its status.
  - A key's level is the lowest status of its statements.
  - Gaps are declared, contradictions are found, and an unreviewed answer from a person does not
    lower a key that holds a verified statement (decision-0004).
- **Rehearsal evidence:** the gate item, a verdict per scenario next to the record's. CargoQuote's
  scenarios cover what the gate is for: a clean kit, an undecided rule, a vague requirement, a
  contradiction, an unverified value, a change and an assumption.
- **Gap:**
  - The gate cannot see knowledge that is consistently wrong. J-F's degradation test planted the
    same defect in every document, and the gate said QUALIFIED.
  - A verification by review does not yet lapse by date (task-0067 asks the maintainer to decide
    whether it should).
- **Pilot:**
  - The gate runs on the pilot's main delivery task.
  - Every BLOCKED and QUALIFIED key is read by its owner, who confirms the level is right or
    names the defect.
  - Any wrong level is counted, never corrected by hand.

### Agent grounding

*Does an AI assistant use the governed knowledge, and does it stop when the knowledge is not good
enough?*

- **The stack today:**
  - Met for the mechanism.
    - The read-only MCP server (`harness/mcp_server.py`) gives an assistant the gate's verdict and
      the three-valued answer: asserted, documented absent, or unknown.
    - It names the source, the author and the verifications of every statement.
    - For a statement a change invalidated, it names what supersedes it.
  - Unproven for the outcome. In the proof of concept (pumllint
    `docs/neo4j-governed-knowledge-evaluation.md`), the governed assistant wrote no code under a
    BLOCKED verdict in 20 of 20 runs. That is one model on synthetic content; the outcome study is
    task-0057.
- **Rehearsal evidence:** the three-valued answer item. The server's report equals the command's,
  every answer carries provenance, and CargoQuote shows all three answers.
- **Pilot:**
  - The pilot's assistant is connected to the MCP server and runs at least one real task.
  - The record shows the verdict it was given, the keys it read, and whether it built or stopped.

### Operational safety

*Can an agent, or anyone, change the knowledge or act on the business without authority?*

- **The stack today:** met for writes.
  - The store and the register change only through pull requests and recorded rulings
    (decision-0002, with four eyes in the register).
  - The MCP server only reads: it refuses every store operation that is not a read. Over HTTP it
    binds to the loopback address unless a token is set.
  - A model may only read and propose inferred statements; it never rules.
  - There is no business action to secure: see the section below on what is out of scope.
- **Rehearsal evidence:**
  - The three-valued answer item: the store's census is the same before and after the server
    reads it.
  - The example instance's digest is the same before and after the whole collection.
- **Gap:** the permissions are not yet written as one matrix. Task-0059 gains that table, with a
  test for each row a test can enforce.
- **Pilot:**
  - The pilot's security reviewer reads the data flows and the permission matrix.
  - The instance stays in the pilot's own repositories.
  - No pilot content is pushed to this repository.

### Interoperability

*Can the knowledge leave the platform, and can it come in from the tools the organisation already
uses?*

- **The stack today:** partial.
  - Everything is in open files: the register in TOML, the store as Turtle when it is the in-memory
    store (`KG_RDFLIB_FILE`).
  - Two store kinds give the same record (the deterministic comparator).
  - The register's exports carry a manifest of digests and a reconciliation record.
  - Not yet verified: any of the three import routes from an incumbent architecture tool
    (task-0063), and a round trip through Turtle into the other store kind (task-0070).
- **Rehearsal evidence:**
  - The export manifest item: every digest matches the subject's bytes, and the reconciliation
    record is present.
  - The store kind the run used, in the summary. Run it on both kinds and the gate's verdicts
    agree.
- **Pilot:**
  - The pilot's register content comes in from its incumbent tool through one verified route.
  - The pilot's export manifest reconciles with no unexplained drift.

### Performance and cost

*What does it cost to run, and does it hold at the organisation's scale?*

- **The stack today:** not measured beyond the record's token counts (task-0027) and the times
  below. The scale of a lighthouse is unknown.
- **Rehearsal evidence:**
  - The cost item: wall-clock time per step and the store's size in nodes and relationships, with
    no model call.
  - The arms' token counts are on the page when a run calls a model.
- **Pilot:**
  - The time to load the pilot's documents, run the gate and answer over MCP, at the pilot's size.
  - The model tokens of one real task.
  - The person-hours its owners spent reviewing levels and rulings.

## Out of scope: executing business actions

Step 6 of the assessment's proof-of-concept sequence (criterion 6 in doc-0013) asks whether the platform can carry out business actions, such as
changing a record in an operational system, with transactions and authorisation. knowgov executes
none, and this protocol does not test it, for three reasons:

- **Separate concerns.** The assessment itself keeps governing knowledge apart from running
  operations.
- **What it would take.** Executing actions would need transactions, compensation and operational
  authorisation, and would put knowgov on the operational path.
- **It would break a rule.** It would break the rule that every write is a pull request
  (decision-0001's boundary, and the MCP server's read-only rule).

What knowgov can do instead is gate the *definition* of an action. An action's submission rules
and the decision logic it calls are declared design, read from documents like any decision table.
knowgov can answer "may this change to the action ship?" in the same way it answers for code.

## The pilot checklist

The pilot runs on the lighthouse organisation's own instance (task-0062 chooses the pilot and its
incumbent tool). Each line's evidence goes in the pilot's private record, inside the
organisation's own repositories, and only the line's outcome (done, not done, or the reason)
appears in the maintainer's notes.

- [ ] The instance is built in the organisation's repositories and `tools/check_instance.py` passes on it.
- [ ] The register content comes in from the incumbent tool through one verified route; the export manifest reconciles.
- [ ] Every key of the main delivery task maps to a register node with an owner.
- [ ] The gate runs on that task; every BLOCKED and QUALIFIED key is reviewed by its owner and any wrong level is counted.
- [ ] One real document change is followed to its statements, nodes and code; the person who made it confirms the reach.
- [ ] The assistant uses the MCP server on at least one real task; the verdict it got and what it did are recorded.
- [ ] The security reviewer has read the data flows and the permission matrix.
- [ ] Load time, gate time, model tokens and review hours are recorded at the pilot's size.
- [ ] Nothing from the pilot, and no bank-related data, has been pushed to this repository.
