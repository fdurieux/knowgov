---
id: doc-0011
title: >-
  knowgov as the governed layer of a declarative twin: the walk, process mining,
  code traceability, completeness
type: specification
created_date: '2026-11-03T22:03:00Z'
updated_date: '2026-11-03T22:04:00Z'
tags:
  - brief
  - digital-twin
  - fit-gap
  - canvas
  - swot
  - impact
---
*2026-11-03. Maintainer register. A study: nothing built, no task created. Read against doc-0010 (knowgov is the governed knowledge layer over the declarative twin, Loop A; not a running twin, Loop B) and pumllint `docs/ea-ontology-stack-evaluation.md` §12, on `main` at `a82f33c`, register v0.2.3 (vendored, decisions 0001–0008; ieam-register 0009 is proposed and not vendored). Decisions in force or proposed that bound the answers: knowgov decision-0002 (proposed: who approves, closes a gap, settles a dispute), ieam-register 0007 (the walk follows approved links only), 0008 (knowledge a person gave).*

*Executed, in a venv with harness.yml's library pins on CPython 3.13 (the harness does not depend on 3.12; the J-F oracle does, and was not run): `tools/example_instance.py` (layout holds); with `KG_STORE=rdflib` on that instance, `gate_cli.py` on S1, S2, S6 and `--baseline record`; `run.py --deterministic --scenarios S6`, once bare and once with the record's `results/S1/run1_G.py` as the derived input, persisted to a Turtle file; the register projected into that store; a scratch walker importing `demo/register/tools/impact.py` and swapping `FORWARD` per proposal (56 nodes, 65 links); a scratch anchor join over the projected store. Read only: the Neo4j adapter, the page, the register's checker. Not executed: Neo4j, an Arms run, any process-mining tool. The maintainer added two constraints while this was written, and both are answered in points 2 and 3. The client's process-mining tool is not chosen (SAP's or ARIS Process Mining are candidates) and must be configurable. The CI/CD integration must plug into GitHub Actions, GitLab CI or another platform. Scratch scripts and outputs stayed in the session's scratchpad; only this doc is committed. Public synthetic content only; no bank data, no real person.*

## Verdict

**doc-0010's line holds, and all four points fit on the declarative side of it once each is cut to what it actually needs.** Three of the four are gaps in the governed layer itself; one (process mining) is a feed from the other side that knowgov should *receive as evidence*, never *produce*.

1. **The walk.** Today it reaches nothing from 28 of the 37 approved non-application, non-process starts measured (every CAP, ENT, PRD and journey step). Adding every relationship in both directions is wrong: measured, it collapses to the connected slice, the same 15 nodes from CAP-0002, ENT-0003, APP-0002, JRN-0003 and PROC-0004 alike, which answers no question. What works is a *dependants* rule per start kind: `crud`⁻¹ and `manages`⁻¹ from an entity, `requires`⁻¹ from a capability, `concerns`⁻¹ and `delivers`⁻¹ from a product, `is_supported_by` forward from a step. It takes zero-reach starts from 28 to 6 (the six are domains and portfolios, which have no links of their own). That table is the register's to adopt under its 0007. knowgov's own share is the join below the register: `maps_to` and anchored citations into the store, measured at anchor grain (ENT-0004 → DT-P → 13 statements, against 39 at document grain).
2. **Process mining.** Fit it in as *conformance evidence on declared statements*, never as an event log in knowgov. The client's tool owns the log, the discovery and the replay. knowgov receives an aggregate result keyed by register ids (`PROC-`), with no case ids. That result can flag a key, never verify it, and divergence becomes a question to the key's owner under decision-0002. The register may want an `observed` evidence class beside `elicited`. Handled this way, the line in doc-0010 moves by one word ("receives"), not by a feed. The tool is not chosen yet (SAP's or ARIS Process Mining are candidates), so the contract is a neutral, schema-pinned aggregate *file*. Each tool gets a small converter on the client's side, chosen by instance configuration. knowgov reads one format and names no vendor, the same pattern as `KG_STORE` and the model endpoint. Do nothing until Loop B's trigger fires in pumllint's ROADMAP. The `event-logs` kind already exists in `instance/kinds.toml` with no mapper, which is the right state.
3. **Code traceability.** A CI hook is the right shape and mostly built: `gate_cli.py` has the exit contract and the store has `register_derived` and `USED_ASSERTION`. Three measured gaps stop it working today:
   - `gate_cli.py` runs stage 1 only, so it never sees S6's change.
   - `stale` and `suspect_derived` are counts in its JSON, not findings, so they never move the exit code.
   - After S6's re-verification the gate reads PROCEED while `derived:S1:G:run1` is still suspect (measured).

   The hook adds the reverse direction by registering each build's output with the assertions it used. A changed digest on a registered file then reaches its statements and documents backwards. The code's identity needs a mapping that nothing holds yet: code path → APP id. GitHub Actions, GitLab CI and others are candidates, so the hook is a platform-neutral command: explicit inputs, the 0/1/2 exit, JSON under a schema. Thin per-platform wrappers are selected by the client, and nothing platform-specific sits in `harness/`.
4. **Completeness.** Of seven properties, provenance is built. Identity, typed relationships, epistemic state, change propagation, the gate and currency are partial, and observed state is out of scope. "Functionally complete" is defined below as eight checks. Five come from doc-0009's milestone, "Capture that moves the gate", plus decision-0002. Two come from points 1 and 3 of this doc. One is the walk's register decision.

The side-chat evaluation: **not received** when this doc was written (see its section).

## 1. The impact walk: making it more complete

### Measured today and per proposal

Scratch walker: `impact.walk` with `FORWARD` extended per row, the register at v0.2.3. Cells: examples as edges/nodes reached (live edges only, per 0007), then zero-reach over every *approved* node of that kind.

| Proposal (added to `FORWARD`) | CAP (CAP-0002, CAP-0007) | ENT (ENT-0003, ENT-0008) | PRD (PRD-0002, PRD-0004) | journey step (JRN-0003, JRN-0006) | module (APP-0002, APP-0006) |
|---|---|---|---|---|---|
| today | 0/0, 0/0; 7 of 7 zero | 0/0, 0/0; 9 of 9 zero | 0/0, 0/0; 5 of 5 zero | 0/0, 0/0; 7 of 7 zero | 5/5, 3/3; 0 of 7 zero |
| A `crud` (process → entity) and `crud`⁻¹ (entity → process) | unchanged | 6/5, 10/8; 3 of 9 zero | unchanged | unchanged | 7/6, 11/8 |
| B `manages`, `manages`⁻¹ | unchanged | 9/8, 7/6; 2 of 9 zero | unchanged | unchanged | 9/8, 3/3 |
| C `requires`⁻¹ (capability → products requiring it) | 1/1, 2/2; 2 of 7 zero | unchanged | unchanged | unchanged | 6/5, 5/5 |
| D `realizes`⁻¹ (capability → processes realising it) | 3/3, 3/3; 2 of 7 zero | unchanged | unchanged | unchanged | 6/5, 4/3 |
| E `concerns`⁻¹, `delivers`⁻¹ (product → journeys, processes) | unchanged | unchanged | 4/3, 5/3; 2 of 5 zero | unchanged | 8/6, 3/3 |
| F `is_supported_by` forward (step → process) | unchanged | unchanged | unchanged | 4/3, 3/3; 0 of 7 zero | 6/5, 4/3 |
| G `owns`⁻¹ (any node → owner unit) | 0/0; 6 of 7 zero | 0/0; 8 of 9 zero | 1/1, 0/0 | 0/0 | 7/6, 3/3 |
| H `maps_to` (entity → physical) | — | 0/0: its target is `target_external`, never a node | — | — | — |
| **R dependants** = A⁻¹ + B⁻¹ + C + E + F | 5/3, 17/8; 2 of 7 zero | 17/10, 29/15; 2 of 9 zero | 4/3, 5/3; 2 of 5 zero | 9/6, 20/11; 0 of 7 zero | 10/6, 21/11 |
| ALL, A to H, both ways | 32/15, 51/21 | 32/15, 51/21 | 6/4, 28/12 | 32/15, 51/21 | 32/15, 52/21 |

The remaining zeros under R are the two capability domains, the two information domains and the two portfolios. They have no links of their own, and the walk does not descend `parent` (decision 0007 is silent on hierarchy).

**Two readings the numbers force.**
- **Direction is the decision, not the relationship list.** Under ALL, every CargoQuote start reaches the same 15 nodes, including ORG-0001 (checked as set equality). The walk has become "the slice this node is in", which a reader already knows. The present walk works because every step points from the thing changed to what *rests on* it. Each addition must keep that property: `crud`⁻¹ (a process that reads the entity rests on it), `requires`⁻¹, `concerns`⁻¹. The realiser direction (D: capability → processes) answers a different question, "what implements this", and belongs in a second, named walk, not mixed in.
- **`owns` and `maps_to` are not walk edges.** `owns`⁻¹ reaches the accountable unit, which the panel should show as an annotation on every reached node (who to tell), not as a reached node. `maps_to` leaves the register by construction (`target_external`). It is the join into the store, and that join is knowgov's.

### What knowgov can do itself, measured

The projection already carries the join. Each `maps_to` link becomes `REG_MAPS_TO` → `RegExternal` with `path`, and each `kit:` evidence entry becomes `REG_CITES {anchor}` → `RegDocument` (`demo/app/register_project.py`). Of the 22 CargoQuote kit citations, 12 carry an anchor (`#DT-P` ×5, `#DT-V` ×2, `#DT-S`, `#REQ-01/04/05/06`), and fragment locators begin with the same anchor (`DT-P/row/P2`). Measured on the store after S6 with the derived input:

| Start | Join | Statements | Derived reached |
|---|---|---|---|
| ENT-0004 Tariff | document grain (cites + `maps_to` path) | 39 | `derived:S1:G:run1`, suspect |
| ENT-0004 Tariff | anchor grain (`maps_to` `#DT-P` → fragments `DT-P/…`) | 13 (P1–P4, v1 and v2) | `derived:S1:G:run1`, suspect |
| APP-0002, CAP-0002, PROC-0004, PRD-0002 | document grain | 33, 39, 69, 71 | the same one, suspect |
| JRN-0003 | document grain | 8 | none |

Anchor grain is three times tighter on the one start where an anchor exists. A saved query can do the same through `REG_CITES.anchor` for the other 11 anchored citations, which this run did not measure. The rdflib adapter has no Cypher, and the scratch join read its graph through the port's helpers. That is doc-0008 finding 2 resolved at anchor grain where the register cites anchors. It still stops at derived code. It does not reach *hand-written* code, which point 3 addresses.

### Canvas

| Box | Content |
|---|---|
| Problem | An architect starts from a capability, an entity or a product; the walk answers only from APP, PROC and JRN-journey, and 28 approved starts walk zero edges. |
| Who | Architects (CAP, PRD), data owners (ENT), journey owners (steps), the gate's reader asking "what does this statement sit under". |
| Today | `impact.py`, the panel and the saved `register-impact`, edge for edge the same (doc-0008); doc-0008's three paste-in Cypher queries. |
| Solution | Register: the R table as a proposal to ieam-register, plus a second named walk for realisers. knowgov: an anchor-grain saved query from a register node to statements and derived outputs, and owners shown as an annotation. |
| Measure | Zero-reach approved starts 28 → 6 (domains and portfolios only). No start reaches the whole slice. The anchor query returns, for ENT-0004 on S6, the 13 statements and the suspect derived output, identical on both stores. |
| Cost | The register's proposal is small (one decision, a `FORWARD` table, its test). The knowgov query is about an hour, plus the stack job's check. |
| Risk | Over-reach: walking in both directions turns the answer into noise. The ALL row is the evidence for keeping direction in the rule. |

### SWOT

- **S.** The rule (approved links only, withdrawn reported) carries over unchanged to new relationship types. The projection already holds anchors.
- **W.** Hierarchy is not walked. Anchors exist on 12 of 22 citations only. `maps_to` has one link in the whole register.
- **O.** The R table is small and testable. The anchor join gives doc-0008's "module → code" at statement grain.
- **T.** The register's 0007 makes this its decision, so knowgov must not fork `impact.py`. A Cypher walk on the page that drifts from `impact.py` would break doc-0008's "edge for edge the same".

### Fit/gap

| Needed | Exists | Gap | Whose |
|---|---|---|---|
| Walk from CAP, ENT, PRD, step | `FORWARD` for 3 taxonomies | the R entries | register (0007) |
| Realiser walk | none | a second named table | register |
| Owner on each reached node | `owns` links, 9 approved | the panel annotation | knowgov page |
| Node → statements → derived | `REG_CITES`, `REG_MAPS_TO`, `SUPPORTED_BY`, `USED_ASSERTION` | a saved query at anchor grain | knowgov |
| Hierarchy | `parent` field, `REG_PARENT` | a rule on whether retiring a parent reaches its children | register |

### Advice

Propose R to ieam-register as one decision, with this table's measures as its evidence and its own test (zero-reach starts, no start reaches the full slice). Keep the realiser direction as a separate walk. Add the anchor-grain query to knowgov's saved queries now: it reads the projection and changes nothing of the register's. Do not walk `owns` or `maps_to`.

## 2. Process mining at the client: how it could fit

### What an event log adds, and what it does not

- **Adds.** Evidence that the *running* process follows the *declared* one. Fitness of the declared PROC (and the kit's BPMN, `kit/quote_process.bpmn`, which `extract_bpmn` reads into `flow|order`) against observed traces. Deviating activities, skipped steps and observed orders. This is §12.1's "Declarative versus Running" gap analysis, keyed on the ids doc-0010 §4 names as the join (`PROC-`, `CAP-`).
- **Does not add.** Truth about the design. A declared statement is prescriptive. 98 % fitness says the estate mostly does what the statement says, not that the statement is right. 60 % says that one of the two is wrong, not which. And, as §12.4 has it, the log does not know what it failed to observe: unlogged activities, cases outside the extraction window, and systems with no event table.

### Where a result could land

| Landing | Fit | Reading |
|---|---|---|
| A verification of an assertion with a validity window (`Verification {method, valid_until}`) | **no** | decision-0002 point 2 keeps *verified* to the oracle, meaning a test that executes the statement. A conformance pass is not that. Using it would put §12.3's "arrives wearing green" inside the gate. |
| Evidence on a process node, joined through `register_map.toml` keys whose `nodes` list a PROC | **yes** | an `Observation` beside the key, carrying tool, version, window, fitness and the deviating activities. It is shown in the bundle, adds a flag (`observed_divergent`) at minor or major, and never changes a level. |
| A declared gap when observed and declared diverge | **only through a person** | under decision-0002 point 3 only the owner may open or close a gap. Divergence is a *question* to the owner (the capture questionnaire's route), not an automatic gap. |
| The register's record | **register's call** | an `observed = {tool, window, record}` block beside 0008's `elicited`, with its own short review. The register decides it. |

### Who owns what

| Piece | Owner |
|---|---|
| The event log, its extraction, case ids, discovery, replay, conformance | the client's process-mining tool (the site names PM4Py conformance for the `event-logs` kind), inside the client's estate |
| The mapping from log activity names to PROC ids | the client, as a file in their instance, reviewed like `register_map.toml` |
| The aggregate result, keyed by PROC id, with no case or person id | written by the client's tool into the instance's `artefacts/event-logs/`, the slot `instance/kinds.toml` already has with no mapper |
| Reading it as evidence, the flag, the question to the owner | knowgov, as a mapper and a rule |
| Whether a link or node may carry an observed record | ieam-register |
| Whether Loop B fires at all | pumllint's ROADMAP first (doc-0010 §6) |

### The tool as configuration: an interface, not an integration

The client has not chosen a tool, and SAP's offering or ARIS Process Mining are both candidates. The answer is yes, it can be abstracted, and it should be. The interface is a *file contract*, not a plugin API. The same split already works twice in this repository: `KG_STORE` picks a store adapter behind the port in `harness/store.py`, and `KG_MODEL_BASE_URL` / `KG_ARMS_MODEL` make the model endpoint instance configuration (`harness/arms.py` `endpoint()`).

| Layer | What it is | Where it lives | Varies with the tool? |
|---|---|---|---|
| Contract | `conformance-result.schema.json`: one result per declared process and window (`process` = a PROC id, `window` from/to, `tool` {name, version}, `fitness`, per activity {PROC id, observed count, skipped, out-of-order}, `min_cell` the suppression threshold used, `record` the path of the tool's own report). Validated by `harness/schema_check.py` as the gate report is. | knowgov, beside `gate-report.schema.json` | no |
| Activity map | log activity label → PROC id, reviewed like `register_map.toml` | the client's instance | per process, not per tool |
| Converter | reads the tool's own export (a conformance or variant report) and writes the contract. One small script per tool: `aris_pm`, `sap`, `pm4py`, or `file` for a hand-written result. | the client's instance or CI, *outside* knowgov | yes: the only part that does |
| Selection | `[conformance] converter = "…"`, `map = "…"`, `min_cell = …` in the instance's configuration | the client's instance | yes |
| Reader | one mapper for the `event-logs` kind that reads only the contract, plus the flag rule | knowgov | no |

**Why the converters stay outside knowgov.** A converter is the only code that touches the tool's export, which may hold case-level data. If it runs in the client's estate, the aggregate rule is enforced before anything reaches an instance repository, and knowgov never needs a vendor's SDK, licence or credentials. A reference converter for PM4Py, which is open and runs on a synthetic log, proves the contract in CI. The SAP and ARIS converters are the client's, written once the tool is chosen, against that tool's actual export format. That format was not checked here, and this doc claims nothing about either product beyond "has a conformance result to export".

**What the abstraction cannot hide.** Tools differ in what "fitness" means (token replay, alignments, a vendor's own score). The contract therefore carries the tool and the method beside the number, and the flag rule thresholds per method, not globally. Two tools' results on one process are two observations, never averaged.

### Privacy

An event log is personal data: case ids, often customer ids, and resources, which means employees. It never enters knowgov, public or private. Only the aggregate does: per activity, counts and fitness over a window, with a minimum count per cell so that a cell cannot single out a case. The client's instance is private (CLAUDE.md), but the aggregate rule holds there too, because the store copies what it reads into fragments. No bank data here, ever. A banking client's run stays in their estate, and this repository receives nothing of it.

### Does it blur the line?

Somewhat, and only at one point. doc-0010 drew the line at *producing* an observed-state feed. Receiving a summarised verdict from a tool that does produce one is what knowgov already does with a linter's report or a test oracle: it records an external judgement with its provenance and refuses to promote it. The line moves from "no observed state" to "no observed state *produced or stored* here; observed verdicts received as flagged evidence". The risk is wording. An adopter reading "process mining" on knowgov's page will hear "running twin". doc-0010 §5's sentence must then gain a clause, not lose one.

### Canvas

| Box | Content |
|---|---|
| Problem | The client's declared processes may not be what runs; nothing joins the two, and the gate cannot see it. |
| Who | The client's process owners and the process-mining team; the gate's reader. |
| Today | Nothing: `event-logs` kind with no mapper; doc-0010 places Loop B outside. |
| Solution | A neutral, schema-pinned aggregate per process and window, keyed by PROC ids. A per-tool converter on the client's side, chosen by configuration. One mapper, a flag and a question to the owner. Never a verification. |
| Measure | On a synthetic log over CargoQuote's BPMN, a planted swap (screen before validate) flags `flow|order` and nothing else, without moving the verdict level. |
| Cost | Medium: a mapper and a rule on both adapters, a synthetic log, and the register's decision if it wants the record. |
| Risk | Observation promoted to truth. A log leaking into the store. The twin wording. |

### SWOT

- **S.** The keys and register ids exist, and the flag and bundle machinery exists. The PROC/BPMN path is already read.
- **W.** One BPMN, and `extract_bpmn` reads a single path. No log, synthetic or real, exists anywhere.
- **O.** It answers §12.1's gap analysis on the client's own terms. It is the client's investigation, already under way.
- **T.** Personal data. Scope creep into a running twin. A client tool's verdict trusted beyond what it can see.

### Fit/gap

| Needed | Exists | Gap |
|---|---|---|
| Join keys | `PROC-` ids, `register_map.toml` rows listing nodes per key | activity-name → PROC map |
| A slot in the instance | `event-logs` kind, no mapper | the aggregate's format; a mapper |
| A non-promoting evidence class | flags (`ambiguous`, `inferred`, `assumed`) | `observed_divergent`; the Observation node |
| Owner routing | questionnaire per owner (task-0009) | divergence as a questionnaire input |
| Privacy rule | instance private; 0008 handles | an aggregate-only rule, written |

### Advice

Tell the client knowgov will *receive* their conformance result, keyed by PROC id and aggregated, and will not hold the log. Do not build until Loop B's trigger fires in pumllint's ROADMAP. When it fires, write a knowgov decision (observed evidence flags, never verifies) and a register proposal (`observed`), then a synthetic-log experiment on CargoQuote. Add a clause to doc-0010 §5's wording.

## 3. Traceability to code changes through CI/CD

### What exists, measured

- `gate_cli.py --scenario S6` on rdflib: PROCEED, exit 0, `stale 0`, `suspect_derived 0`. It loads stage 1 only (`gate_cli.py` "What a deterministic run does before its gate… stage 1"), so the change S6 is about never reaches the command.
- `run.py --deterministic --scenarios S6` with no derived input: 4 invalidated, BLOCKED then PROCEED, nothing suspect (the derived file is read from `<out>/S1/run1_G.py`; absent, no Derived is registered).
- The same with the record's `run1_G.py`: `derived:S1:G:run1` registered with every assertion on the gate's keys, then marked suspect (3 invalidated assertions used). The gate before re-verification is BLOCKED; **after re-verification it is PROCEED with the derived output still suspect.** The verdict judges knowledge. A suspect output is listed in the bundle, but no finding and no exit code carries it.
- `findings()` in `gate_cli.py` turns key levels into findings and nothing else. `stale` and `suspect_derived` are counts in the JSON.
- `register_derived(did, kind, sha, assertion_ids)` is a port method, called only by `run.py`'s stage 2. No command exposes it.
- The register has no application → code relationship. `maps_to` goes from entity to physical form, and APP nodes carry `archi_id`, not a path.

### The hook, sketched (not built)

Two steps in the client's code pipeline, after the instance's load (which reads only the merged tree, doc-0008 §5) and against the store the load filled.

**`knowgov-trace check`** (on every pull request into the code repository)
- *Inputs.* The commit sha; the changed paths with sha256; a `code_map.toml` in the instance mapping path globs to APP ids (module grain) and, per APP, the subject task whose keys it builds on.
- *Does.* For each changed path:
  - If it is a registered Derived and its digest differs, it reports **drift**: the code changed after its registration. It lists the assertions the registered version used, their documents and anchors, and their current status. That is the reverse direction.
  - If a registered Derived is suspect, it reports **suspect**: the file rests on invalidated statements. It lists them and their successors.
  - For each APP touched, it runs the gate for its task, as `gate_cli.py --no-load --task …` does.
- *Exit.* 0: no finding at or above `--fail-on`. 1: a finding at or above it, meaning the task BLOCKED, a suspect Derived changed without the statements re-verified, or a regression against `--baseline`. 2: could not run: no map, a path in no glob, an unreachable store.

**`knowgov-trace register`** (on merge to the default branch, after the build)
- *Inputs.* The commit sha; the built or changed files with digests; the APP id; the task; the gate report's assertion ids (from the bundle the build used).
- *Does.* `register_derived("derived:<repo>@<sha>:<path>", kind, sha256, ids)`, superseding the previous Derived for the same path.
- *Exit.* 0 recorded; 2 could not (store, map). It never fails a build for knowledge: that was `check`'s job.

### Platform as configuration: GitHub Actions, GitLab CI, others

The hook must plug into whichever pipeline the client runs. It can, if the platform-specific part is kept to a wrapper:

| Concern | Platform-neutral core (in `harness/`) | Per-platform wrapper (a template the instance copies) |
|---|---|---|
| Which commit, which files | explicit flags: `--commit SHA`, `--changed FILE` (one path per line) or `--base REF` (the core runs `git diff --name-only`); never reads `GITHUB_*` or `CI_*` variables | maps the platform's variables to those flags (GitHub `GITHUB_SHA` and the pull request's base; GitLab `CI_COMMIT_SHA`, `CI_MERGE_REQUEST_DIFF_BASE_SHA`) |
| Where the store is | `KG_STORE`, `KG_SUBJECT`, `KG_REGISTER`, as today | the platform's secret and variable store |
| Pass or fail | exit 0/1/2, `--fail-on`, `--baseline` | the job's status; branch protection or merge-request approval rules make it required |
| Findings shown to a reviewer | `-f json` under a schema; `-f text` | a step that turns the JSON into the platform's annotation format, or uploads it as an artefact |
| Packaging | `python -m` entry points, pinned like the harness | a composite GitHub Action; a GitLab CI `include:` template; a shell snippet any runner can call (Jenkins, Azure DevOps, Bitbucket) |

The pre-load gate (doc-0008 §5) and `gate_cli.py` need exactly the same split, so one wrapper per platform serves all three gates. This is also the consumer that doc-0009 parked SARIF for. GitHub's code scanning reads SARIF. GitLab's native report formats differ by feature and version, so which format GitLab gets is the wrapper's choice and was not checked here. The core should therefore emit its own JSON and leave format conversion to the wrapper, until a client's platform names the format it reads.

### What it can stop and what it can only report

| Stops (exit 1, before merge) | Reports only |
|---|---|
| A change to a module whose task is BLOCKED (absent, declared gap, disputed, invalidated keys) | That the code does what the statements say: that is the tests and the oracle, not knowgov |
| A change to a suspect Derived while its invalidated statements have no verified successor | Hand-written code that cites nothing: it can be mapped to an APP, not to statements |
| A regression against the recorded baseline (`--baseline record`, as today) | Drift on a registered file: an edit is legitimate, so the hook reports what the edit sits on and asks for re-registration |
| | A code change that contradicts a statement: no mapper reads code semantics |

### Three gates side by side

| | Pre-load gate (doc-0008 §5, proposed) | knowgov gate (`gate_cli.py`) | Code hook (this sketch) |
|---|---|---|---|
| Repository | the instance (documents) | the instance, after load | the client's code |
| Question | is this document well-formed for its kind? | is the knowledge this task needs good enough? | does this code change rest on knowledge that is still good, and what does it sit on? |
| Identity | file path, kind | key, assertion id | commit sha, path digest, APP id |
| Exit | 0/1/2 | 0/1/2 | 0/1/2 |
| Stops | a malformed document | a build on bad knowledge | a change to code on bad or invalidated knowledge |

The three share the contract and nothing else; none replaces another.

### Canvas

| Box | Content |
|---|---|
| Problem | Traceability runs one way. A changed document marks code suspect only in the deterministic harness, and a changed file reaches nothing. |
| Who | The client's developers and reviewers, and the module owner. |
| Today | `gate_cli.py` (stage 1 only, staleness not a finding); `register_derived` reachable from `run.py` only. |
| Solution | `check` and `register` as above, plus `code_map.toml`; a platform-neutral core with GitHub Actions, GitLab CI and shell wrappers. In the gate: stale and suspect as findings, and a load that can bring in a version 2. |
| Measure | On S6: register the S1 output through `register`. After the tariff change, `check` exits 1 naming `derived:S1:G:run1` and P2/P3. After re-verification it still exits 1 until the code is rebuilt and re-registered. Then a hand edit to the file reports drift with its 3 invalidated and 33 live statements. |
| Cost | Medium: two subcommands, one map format, two findings, tests on both adapters, a CI job on the example instance. |
| Risk | A map that rots. Every build registering everything. A team switching the hook off after its first false stop. |

### SWOT

- **S.** The contract, the baseline ratchet, `register_derived` and the S6 traversal all exist, so the hook is wiring, not research.
- **W.** The gate ignores staleness once re-verified. The CLI never sees a second version. Code has no identity in the register.
- **O.** Two-way traceability at derived grain is what doc-0010 gap 3 asks for, and it is what a client's CI already wants: "why did this break".
- **T.** Map maintenance cost. Confusion with the pre-load gate. Claiming the hook knows the code is correct.

### Advice

Build in this order:
1. Make `stale` and `suspect_derived` findings in `gate_cli.py` (suspect: major by default, blocker with a flag), so that the measured PROCEED-with-suspect is visible in the exit.
2. Give the load and the CLI a way to take a later version of an artefact, so S6's stage 2 is reachable by command.
3. Add `code_map.toml` in the instance layout, owned by the instance and not the register, until the register decides an `implemented_by`.
4. Build `register`, then `check`.

Keep the hook in knowgov's `harness/` beside `gate_cli.py`. The client's CI calls it; nothing in knowgov calls the client. Keep the core free of any platform's variables, and ship the GitHub Actions and GitLab CI wrappers as templates proven on the example instance; others get the shell snippet.

## 4. Functionally complete for a declarative twin

### The definition

Taken from doc-0010 §2's property map and §12.3–12.4: the layer is complete when every declared element and every statement about it:
- has a stable identity;
- is joined by typed, directed, approved relationships that a walk can follow from any start kind;
- keeps its provenance;
- carries an epistemic state that only an authorised person or an oracle can raise;
- propagates a change in either direction (document ↔ statement ↔ code);
- is judged by a gate whose exit carries every one of those states;
- and is current within a stated window.

Observed state (Loop B), simulation and write-back stay out of scope.

### Scored today

| Property | Score | Evidence |
|---|---|---|
| Identity | partial | Register ids with four-eyes approval; assertion, fragment and version ids with digests. Persons: handles only, and issued handles (0009) are not vendored. Code: a Derived id and sha in the harness, with no map from APP to code. |
| Typed relationships | partial | 10 types, 65 links. The walk reaches nothing from 4 of 6 kinds (point 1). No realiser walk, no hierarchy. |
| Provenance | built | Activity, agent, fragment and version with digests; `elicited {from, on, record}` on captures (0008). |
| Epistemic state | partial | Statuses, verifications, the three-valued answer, declared gaps and flags. No review record (task-0037). decision-0002 is proposed. Elicited statements are outside the conflict rule (task-0038). |
| Change propagation | partial | Document → statement → derived (S6), harness only. Code → nothing. A register change re-projects but does not invalidate. |
| Gate | partial | Verdicts, exit 0/1/2 and the baseline exist. Stale and suspect are not findings. Stage 2 is unreachable by command. There is no pre-load gate. |
| Currency | partial | Per export with `review_due`. Elicited links are reviewed at 6 months (register). Statements get `valid_until` only on invalidation. The six-month lapse of an approved capture is not built (task-0037, route (b) task-0040). |
| Observed state | out of scope | doc-0010 §4.1. Point 2 adds a received, flag-only form, not a feed. |

### The missing pieces, in dependency order

1. decision-0002 approved, and ieam-register 0009 approved and vendored. *(doc-0009 "Capture that moves the gate", step 1.)*
2. task-0038 (elicited statements in the conflict rule), then task-0039 (may a capture lower a key). *(Same milestone, step 2.)*
3. task-0037: the review record, the closing of a gap and the lapse. Epistemic state and currency become built here. *(Same milestone, step 3.)*
4. Gate findings for stale and suspect, and a CLI load of a later version. *(Point 3, steps 1–2.)*
5. The anchor-grain saved query, and the owner annotation. *(Point 1, knowgov's share; doc-0009 "An adopter can start alone".)*
6. The dependants walk, as an ieam-register decision. Typed relationships become built here. *(Point 1; doc-0009 "propose to ieam-register".)*
7. `code_map.toml`, then the hook's `register` and `check`. Identity and change propagation become built here. *(Point 3.)*
8. The pre-load gate (doc-0008 §5). The gate becomes built here. *(doc-0009 parallel milestone.)*

Point 2 is not on the list. It is out of the definition and waits for its trigger.

### Definition of done

knowgov is a functionally complete governed layer for a declarative twin when, on the public example instance, in CI, on both stores:
1. S2 goes from BLOCKED to PROCEED by command, through capture, a closing and a review, each with its exit code.
2. S4 settles by a ruling, and a one-sided approval leaves it disputed.
3. S6 exits 1 from `gate_cli.py` while `derived:S1:G:run1` is suspect, including after re-verification, until the output is rebuilt and registered.
4. A hand edit to a registered file reports drift, with its statements.
5. The register's walk reaches something from every approved non-domain, non-portfolio node, and no start reaches the whole slice.
6. A saved query goes from ENT-0004 to its 13 statements and the derived output.
7. A malformed document is refused before the load.
8. An approved capture lapses to proposed after six months.

## The side-chat evaluation, corrected

**Not received.** The parent session said it would send the maintainer's earlier side-chat evaluation of these four points. No message carrying it had arrived when every other section was written and checked (notifications read twice, none queued). Nothing here quotes or corrects it. When it arrives, the correction is a new section of this doc, written against the same measurements above.

## Follow-ups proposed (not created as tasks)

1. **Proposal to ieam-register: the dependants walk.** Delivers a decision and a `FORWARD` table (R) with its test: zero-reach approved starts 28 → 6, and no start reaches the full slice. A second named walk for realisers. Depends on nothing. It is the register's decision under 0007.
2. **Anchor-grain saved query: register node → statements → derived.** Delivers a `queries.toml` entry and a stack-job check, plus the same result through the rdflib port, with ENT-0004 → 13 statements → `derived:S1:G:run1`. Depends on nothing.
3. **Owner annotation on the impact panel.** Delivers the `owns` unit beside each reached node. Depends on nothing.
4. **Gate findings for stale and suspect derived outputs.** Delivers two finding classes in `gate_cli.py` and the schema, and fixes the measured PROCEED-with-suspect in the exit. Depends on nothing. It is a schema change (the schema version rises).
5. **A later version by command.** Delivers a `gate_cli.py` / load option that brings in an artefact's next version (S6's stage 2), so the CLI sees an invalidation. Depends on 4 to be useful.
6. **`code_map.toml` in the instance layout.** Delivers path globs → APP id → task, checked by `check_instance.py`. Depends on nothing. It may later yield to a register `implemented_by`, which is the register's decision.
7. **`knowgov-trace register` and `check`.** Delivers the two subcommands sketched in point 3, with a CI job on the example instance and S6 as acceptance. Depends on 4, 5 and 6.
8. **Process mining: a knowgov decision, "observed evidence flags, never verifies".** Delivers the rule, the Observation node, the `observed_divergent` flag and the aggregate-only privacy rule. Depends on Loop B's trigger firing in pumllint's ROADMAP. It needs a register proposal for an `observed` record beside `elicited`.
9. **A synthetic conformance experiment on CargoQuote.** Delivers a generated log (no person), an aggregate result, and a planted activity swap that flags `flow|order` only. Depends on 8.
10. **The conformance contract and a PM4Py reference converter.** Delivers `conformance-result.schema.json`, the instance configuration keys (`converter`, `map`, `min_cell`) and one open converter run on 9's synthetic log. The client's SAP or ARIS converter is theirs, once the tool is chosen. Depends on 8.
11. **Pipeline wrappers for the three gates.** Delivers a GitHub Actions composite action, a GitLab CI include template and a generic shell snippet, each mapping platform variables to the core's flags, run on the example instance. Depends on 7 for the hook; usable by `gate_cli.py` at once.
12. **doc-0010 §5 wording, one clause.** "Observed verdicts are received as flagged evidence; no log is held." Depends on 8 being decided. Until then doc-0010 stands as written.
13. **Correct this doc against the side-chat evaluation.** Delivers the missing section. Depends on its text arriving.
