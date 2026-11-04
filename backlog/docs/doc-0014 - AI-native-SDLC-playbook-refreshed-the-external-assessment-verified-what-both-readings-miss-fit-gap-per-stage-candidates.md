---
id: doc-0014
title: >-
  AI-native SDLC playbook refreshed: the external assessment verified, what both
  readings miss, fit/gap per stage, candidates
type: specification
created_date: '2026-11-04T09:23:00Z'
updated_date: '2026-11-04T10:45:00Z'
tags:
  - canvas
  - fit-gap
  - brief
  - sdlc
  - swot
---
*2026-11-04. Maintainer register. A study: nothing built, no task opened here (the coordinating session mints the ids). Trigger: the maintainer supplied two texts on this date, Anthropic's "The AI-Native SDLC Playbook" (L. Claxton, 54 pp., PDF, not vendored) and an external assessment, "KnowGov as a Knowledge-Assurance Layer for an AI-Native SDLC" (dated 2026-11-04, read at `main` 4810262; not vendored). Read on `main` at `6a1bb48` (0.2.0 released, 0.3.0 in flight as #167), pumllint `main` at `a39d800`. Playbook pages are cited by the printed page number at each page foot, which equals the PDF page (page 1 is the cover). No sentence of the playbook is quoted beyond a phrase.*

**Supersedes doc-0004** (2026-11-02) in three places and keeps the rest: (1) its capability inventory ("How it is done today", the fit/gap's "Here today" column), which predates the gate CLI, the MCP server, trace, the pre-load check and the review lapse; (2) its exit-code adapter, "cannot-run 2 → a non-blocking error", replaced by §5 C1 below (fail closed for a mandatory check); (3) its "Shape", replaced by §7. doc-0004's verdict (the playbook leaves the deterministic layer out upstream of build), its sense/nonsense reading and its Backlog.md mapping stand as written. One record per thing: the market scores stay doc-0012's, the permission matrix doc-0013's candidate 5 (folded into task-0059), the twin reading doc-0010/doc-0011's.

## Verdict

**The assessment is accurate on the code and right in its main recommendations; it is incomplete in three places that matter, and the playbook carries more for knowgov than either it or doc-0004 used.** Of its checkable claims, every factual one holds at `6a1bb48` except one that is incomplete in knowgov's favour (§6.1: the CLI and CI route already use an independently maintained scope; only MCP's `keys` lets an agent choose) and two that understate the gap (§6.3: stale and lapsed findings, not only QUALIFIED, pass the default threshold; §8: the 20-of-20 figure measured an *advisory* arm, so it measures obedience to a label, not enforcement, which is the strongest argument for the assessment's own fail-closed recommendation). What both texts miss in the playbook: where a mandatory hook must live to be mandatory (managed settings, pp. 42–43), that a build-time hook must be fast and file-scoped (p. 27), so knowgov's gate belongs at stage transitions and not on every edit, and that a block must name its route to approval (p. 40). Eight candidates come out: four new, three covered in part, one conflicting with doc-0004 and decided here. Six proposed tasks; two points only the maintainer can decide.

## 1. The assessment verified

Marks: **correct**, **incorrect**, **outdated** (true at 4810262, not at `6a1bb48`), **incomplete** (true but missing what changes the reading).

| § | Claim | Mark | Evidence at `6a1bb48` |
|---|---|---|---|
| 1, 3 | Statement-level provenance and state, a task gate, evidence bundles, read-only MCP, capture and review, invalidation, trace from code to statements exist | correct | `harness/gate.py` `evaluate`; `harness/mcp_server.py` (four tools, `READ_ONLY` view); `harness/capture.py`, `harness/review.py`; `harness/change.py`; `harness/trace.py` `register`/`check` |
| 1 | Value across a full enterprise SDLC needs a real pilot; outcome a hypothesis | correct | pumllint `docs/neo4j-governed-knowledge-evaluation.md` l. 45–47 ("supported for the mechanism and unproven for the outcome"); task-0057 To Do |
| 3 | PROCEED: required keys verified/approved, unflagged; QUALIFIED: under the bar, some below verified or flagged; BLOCKED: a blocking level or the share below verified over the bar | correct | `harness/gate.py` l. 65–75 (`block_levels`, `max_unverified_share`) |
| 3 | A suspect derived output can fail the gate under PROCEED; integrations must read findings and exit code | correct | `harness/gate_cli.py` `_findings`: `suspect_derived` is `blocker`; docstring "PROCEED with a suspect derived output exits 1" |
| 3 | The five-against-ten-seconds conflict is exposed once both map to the same key; no discovery in arbitrary prose | correct | conflicts are `R-CONFLICT` on a shared key (store port `mark_conflict`); mappers per kind (`instance/kinds.toml`) |
| 4 | Both public subjects configure `codegen` | correct, incomplete | `subjects/cargo_quote/subject.toml` and `subjects/jef_data_load/subject.toml` `[tasks.codegen]`, and so does `subjects/minimal`. Incomplete: `codegen` is the *only* task class anywhere, though `subjects/README.md` allows one table per class |
| 5 | Four read-only MCP tools: `store_status`, `gate_verdict`, `three_valued_answer`, `evidence_bundle` | correct | `harness/mcp_server.py` `TOOLS` |
| 5 | The built-in agent loop uses Python functions, not MCP | correct | `harness/agent.py` tools through the store port (task-0022.03); MCP is the external route (task-0056) |
| 5 | MCP alone leaves compliance to the assistant; enforcement must come from the environment | correct | the server serves reads only; `instance/ci/knowgov-gate.sh` is the enforcing route |
| 6.1 | A mandatory check needs an independently maintained scope so the agent cannot omit a key | incomplete | true of MCP: `gate_verdict` `keys` resolves "these … keys instead of the task's" and the report then names the task `keys`. Not true of the CLI or CI: `gate_cli.py` has no `--keys`; the scope is the subject's `[tasks.*]` table, changed only by pull request. The gap is that nothing refuses a `keys` report where a mandatory check expects a task class |
| 6.2 | `gate_verdict` defaults `as_of` to today, `evidence_bundle` to the record date | correct, current | `harness/mcp_server.py` `gate_verdict`: `args.get("as_of") or "today"`; `evidence_bundle`: `or "record"` (its docstring: "the date the arms resolve on") |
| 6.2 | The stage-to-stage record needs integration | correct, incomplete | the trace ledger already holds per derived file `commit`, `sha256`, `task`, `assertions` and `as_of` (`harness/trace.py` `register`); the bundle holds `assertion_ids`, `as_of`, the verdict. Missing: the verdict and threshold at registration, the register tag and subject digest (the "policy version"), the task-profile digest |
| 6.3 | Exit 0 / 1 / 2; QUALIFIED passes the default `--fail-on` | correct, incomplete | `gate_cli.py` default `blocker`; docstring "PROCEED and QUALIFIED pass". Incomplete: `stale` and `lapsed` findings are `major` too (`_findings`), so a lapsed review on a required key also passes by default. CI already fails closed on exit 2: `knowgov-gate.sh` exits with the core command's code and every wrapper treats non-zero as failure |
| 6.4 | Consistent documentation can still be wrong; the evaluation shows a defect across all documents escaping | correct | J-F scenario D3 (every layer consistently wrong) is in the CI subset (`KG_JF_SCENARIOS=C,D3`); doc-0004's "no false-assurance case" (J-F #309) |
| 6.5 | The store holds one scenario at a time; loads replace it | correct, incomplete | store port `wipe`; `--no-load` and MCP's `scenario` argument refuse a store holding another scenario (`_check_scenario`), so a mismatch fails closed. Isolation already exists one store per process (`KG_STORE=rdflib` with its own `KG_RDFLIB_FILE`; one compose project per subject, task-0031). What is missing is a recipe and a check for one store per worktree, not a multi-tenant store |
| 7 | task-0063 (connector) depends on task-0062; both To Do | correct | `backlog task view TASK-0063`: depends on TASK-0062, both To Do |
| 7 | MCP is read-only; write-back goes through the incumbent's own integration | correct | `mcp_server.py` header: writes stay pull requests; doc-0013 decision 4 (knowgov executes no action) |
| 7 | doc-0004 maps intent/spec/plan onto backlog records, avoiding a second record | correct | doc-0004 "Fit with Backlog.md" |
| 8 | doc-0004's inventory predates MCP, trace and others | correct | doc-0004 dated 2026-11-02, before task-0051, task-0056, task-0064, task-0068 merged |
| 8 | doc-0004 recommends a non-blocking hook when the gate cannot run, a fail-open path | correct | doc-0004 "Exit codes": "cannot-run 2 → a non-blocking error". No hook was ever built (no `.claude/` in the repository) |
| 8 | No code generation in 20 governed runs with a BLOCKED verdict; one model, synthetic content, n = 5 | correct, incomplete | pumllint evaluation l. 35–37 and §6.7 (l. 826–827): 20 of 20 cells across S2, S4, S5, S7 at `gpt-5.1-2025-11-13`, n = 5, "toy-scale". Incomplete on two counts the report itself states (l. 1189–1196): the governed arm was **advisory**, given the content under BLOCKED on purpose, so the figure is the model's obedience to a label and "does not transfer to another model without re-measurement"; and designer, planter and grader were one context. The architecture withholds; the measurement did not test that |
| 8 | task-0057 To Do, dependent on the lighthouse selection | correct | depends on TASK-0062 |
| 9 | A pilot must measure false blocks, owner delay and cost as well as benefit | correct, partly covered | `docs/lighthouse-evaluation.md` pilot checklist: owner review of every BLOCKED/QUALIFIED key with wrong levels counted; review hours recorded. Not there: missed blocks, owner-resolution time, an unavailable-gate case |

Nothing is incorrect. Nothing is outdated: the 21 commits since 4810262 (tasks 0093–0098, #161–#166) move none of the claims.

## 2. What the playbook offers that both doc-0004 and the assessment miss

1. **Where a mandatory hook lives (pp. 40, 42–43).** Team hooks go in the repository's settings; non-negotiable ones in managed settings that engineers cannot switch off, with only managed hooks and only allowlisted MCP servers permitted, and a sandbox that refuses to start when unavailable (pp. 42–43). That is the playbook's own fail-closed pattern. Both texts say "fail closed"; neither says that a hook in the repository's `.claude/settings.json` is still one an engineer can disable, so the knowgov hook recipe needs a managed-settings variant to be mandatory, and the knowgov MCP server needs to be an allowlisted one.
2. **A build-time hook must be fast and file-scoped (p. 27).** Heavier checks belong at commit or PR. The gate with a load takes seconds to minutes (task-0097: about 4 s per J-F MCP call on rdflib), so its hook points are stage transitions (plan accepted, spec committed, PR), not `PreToolUse` on every edit. Neither text places the gate on the hook timeline.
3. **An approval prompt belongs at Deploy, not Build (p. 27),** because it puts a person on the critical path of every parallel session. A BLOCKED verdict that asks an owner mid-session is that anti-pattern; the owner route is asynchronous (questionnaire, task-0009/0015), and the session should end with the finding, not wait on it.
4. **A block explains itself and names the route to approval (p. 40, step 4).** knowgov's findings name the blocking key and level but not the key's owner, though `register_map.toml` holds one owner unit per key (task-0043). The assessment's scenario 3 ("escalated to its owner") assumes a routing the report does not yet carry.
5. **Gate decisions as telemetry (pp. 44, 29, 33).** Every hook decision is exported with a timestamp and verdict, and the wait per gate is the leading measure. knowgov's report is JSON with a schema; nothing maps it to the OpenTelemetry export an adopter already collects. This is also the cheapest source for the pilot's false-block and owner-wait measures.
6. **The Maintain stage has a knowledge analogue already built.** The playbook's loop is a deterministic detector, versioned tier config, then an agent writing the next intent (pp. 48–50). knowgov's review lapse (decision-0005, `harness/cadence.py`) is the deterministic detector, the task's `block_levels` and `max_unverified_share` are the versioned tiers, and route (b), the questionnaire from reviews falling due (task-0040), is the "next intent" written to the owner. Neither text maps Maintain onto it; the assessment lists "production signals" as remaining work.
7. **The design pass is the natural hook point (p. 16).** The playbook automates spec writing as a job that fires on the merge of `intent.md`, and asks the model to flag contradicting policies. knowgov's deterministic conflict on a mapped key is the check that job lacks, and the merge trigger is where a mandatory gate fits without touching the build loop.
8. **Separation of duties (p. 39):** the agent that wrote the code cannot approve it. decision-0002 already holds this for knowledge (an approver is never the author; a model may only propose `inferred`). Worth stating in the hook recipe so that a session cannot write a review file that renews its own key.
9. **Evals on configuration changes (pp. 34–35),** 20–50 real tasks, on any change to `CLAUDE.md`, skills or hooks, and nightly; each incident becomes a case. knowgov's comparator and arms are this shape for knowgov's own subjects; nothing gives an *instance* the same for the knowledge its assistant reads (the assessment names it, doc-0004 called it a hypothesis; neither gives the shape).
10. **Skill versions in force are logged with the spec (p. 17).** That is the "policy version" in assessment §6.2, and the playbook already asks for it per stage.

## 3. Opportunity canvas: knowgov as the knowledge confidence gate of an AI-native SDLC

| Element | Reading |
|---|---|
| Problem | The playbook moves the bottleneck to the stages around build and gives deterministic controls only from build onward; the design pass is one agent session whose policy check is the model's own flagging (p. 16). Nothing deterministic says whether the knowledge a stage consumes is supported, current and consistent. |
| Users | The platform engineer who owns hooks and managed settings (pp. 40–43); the product owner who accepts the spec (p. 16); the knowledge owner who answers a block; the coding agent, through MCP. |
| How it is done today | In the playbook: skills (advisory, p. 26), a human review of `spec.md`, evals after the fact. In knowgov: the gate CLI and CI wrappers (fail closed on exit 2), MCP reads, trace check on code changes, review lapse. No hook recipe, no managed-settings variant, one task class. |
| What a user gets | A mandatory check at each stage transition that fails closed, names the key, its owner and the evidence, with one `as_of` for the whole run; a record of what each stage relied on. |
| Measures | Correct, missed and false blocks; owner-resolution time; wait per gate from the decision log; escaped defects and rework against the pre-registered baseline (task-0057). |
| How it starts | A fail-closed hook recipe and its managed-settings variant (C1), one `as_of` per MCP session (C2), owner routing in findings (C7); then a design task profile on one public subject (C3); then the lighthouse pilot on the design-to-build transition (C6). |
| Risks | Coupling the gate contract to one vendor's hook protocol (doc-0004's risk, still live: the adapter stays outside the contract). False blocks making the gate the next bottleneck. A second record of intent/spec/plan. Over-claiming the 20-of-20 figure. |
| Gains | A named slot in a lifecycle adopters already read; the fail-closed argument made with the playbook's own words and its own managed-settings pattern. |
| Cost | Recipes and a script: S. Task profiles: S–M per subject (each needs keys and a rationale). Pilot: owned by m-8. |

## 4. SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** deterministic gate with a pinned contract (exit 0/1/2, schemas, version 2); CI route already fails closed; read-only MCP with a scenario check that refuses a wrong context; trace ledger already records statements per derived file; review lapse and route (b) are a working Maintain loop for knowledge; separation of duties in decision-0002. | **W:** one task class (`codegen`) in every subject; MCP lets an agent pick its keys; the two MCP tools default to different dates; findings carry no owner; no hook recipe, no `.claude/` anywhere; the behavioural evidence is advisory, one model, toy scale; gate latency unfit for a per-edit hook. |
| **External** | **O:** the playbook names the slot (an independent confidence gate between stages, p. 48) and the enforcement point (managed hooks, allowlisted MCP servers, pp. 42–43); the design pass on `intent.md` merge is an automation adopters will build anyway (p. 16); hook decisions already flow to OpenTelemetry (p. 44). | **T:** adopters may take skills plus model self-flagging as "enough" for design; the vendor's hook protocol may change (exit-2 semantics); a gate that blocks often will be switched to advisory; the playbook's speed measures (pp. 13, 17) reward skipping the gate. |

## 5. Fit/gap per playbook stage, against what runs today

| Stage | Playbook mechanism | knowgov today | Gap | Reading |
|---|---|---|---|---|
| Plan (pp. 10–13) | `intent.md` from a brainstorm, reviewed by the product owner, committed | capture and questionnaires per owner (task-0009/0015), declared gaps, route (c) transcript to `inferred` (task-0041) | no task class for planning; an intent's open questions are not keys | Fit for the knowledge an intent rests on; an intent itself stays a backlog record (doc-0004). |
| Design (pp. 14–17) | one agent session writes `spec.md` under skills, flags conflicting policies; automated on intent merge | the gate on mapped keys: conflicts, gaps, lapse, invalidation; pre-load lint per kind (task-0045/0066/0082) | no `design` task class; the gate is not offered as the design job's check | **Best fit.** The design job is where a deterministic conflict check is missing in the playbook. C3, C1. |
| Build (pp. 18–29) | plan mode, `CLAUDE.md`, skills, hooks (fast, file-scoped), parallel worktrees | `codegen` gate; MCP bundle and verdict; agent loop with governed tools | MCP key choice (C4); two default dates (C2); no hook recipe (C1); no store-per-worktree recipe (C5) | Fit at plan acceptance, not per edit. |
| Test (pp. 30–35) | feedback loop; evals on config change; incident to eval | comparator, oracle, record, arms per model (task-0028/0029); D3 in CI | nothing for an instance's own assistant config | C8. The record pattern transfers; the cases do not. |
| Deploy (pp. 36–46) | PR review passes; hooks as approval gates; agent up to the production gate; managed settings | CI wrappers for preload, gate, trace (task-0052); SARIF and annotations (task-0083); hosted sessions cannot tag | no managed-settings recipe; findings carry no owner route | Fit; trace-check on the PR is the deploy-side gate. C1, C7. |
| Maintain (pp. 47–52) | deterministic detector, versioned tiers, agent writes the next intent | review lapse by date (decision-0005), route (b) questionnaires (task-0040), stage-2 invalidation and suspect derived output (task-0048/0049) | no production signal; nothing writes a backlog item from a lapse | Fit for knowledge decay; production signals are out of scope (no service here). |

## 6. Quadrant

**No new placement.** doc-0012 scored the stack against a market (Vision 16–17.3, Execute 3; Visionary, deep), and nothing since moves Execute: no installation has met the stack (task-0062 To Do). A quadrant against the playbook would place knowgov among SDLC tooling, where it is a component of one stage transition and not a lifecycle product; scoring it there against Claude Code or a review service is a category error and would read as a lower Vision for the wrong reason. The playbook adds coherence to doc-0012's V3 (delivery-time enforcement) as an argument, not as evidence; it moves no score.

## 7. Candidates

Checked against every task (To Do, In Progress, Done) and decisions 0001–0005.

| # | Candidate | Against the record | Mark |
|---|---|---|---|
| C1 | A fail-closed mandatory hook: recipe for Claude Code (`.claude/settings.json` and a managed-settings variant), mapping gate exit 1 and 2 both to a block, placed at stage transitions | task-0007/0016/0052 give the CLI and CI wrappers (fail closed); doc-0004 recommends cannot-run → non-blocking | **conflicting** with doc-0004; decided below |
| C2 | One explicit `as_of` across MCP calls | task-0080 set `evidence_bundle` to `record` "as the arms read it"; task-0075 the clock rule | **conflicting** in part with task-0080's default; decided below |
| C3 | Task profiles for plan, design and review | `subjects/README.md` allows any `[tasks.*]`; none but `codegen` exists; task-0069 rehearses `codegen` only | **new** |
| C4 | An independently maintained key scope for a mandatory check | CLI has none to bypass; MCP `keys` (task-0056/0080) lets an agent choose | **conflicting** in part with task-0080's `keys`; decided below |
| C5 | Instance isolation for parallel sessions | task-0031 (one compose project per subject), `KG_RDFLIB_FILE`, `_check_scenario`; task-0097 (one handle per process) is compatible | **covered in part**: needs a recipe and a test, not a store change |
| C6 | The design-to-build pilot and its six scenarios | scenarios 1–5 are S1, S4, S2, S5, S6 of CargoQuote, rehearsed by task-0069; the pilot checklist (docs/lighthouse-evaluation.md) has one main task and MCP on a real task; task-0057 pre-registers measures | **covered in part**: scenario 6 (gate unavailable) and the missed-block, owner-time and wait measures are new |
| C7 | A finding names its key's owner and the route to approval (playbook p. 40) | owners per key in `register_map.toml` (task-0043); the impact panel shows the owning unit (task-0047); the gate report does not | **new** |
| C8 | Regression suites for changes to instructions, skills and models | the comparator and record for knowgov's subjects; arms per model (task-0028/0029); doc-0004 named it a hypothesis | **new** for an instance; covered for knowgov's own subjects |
| C9 | A stage-to-stage decision record | the trace ledger (task-0051/0093), the bundle's `assertion_ids`; doc-0004 rules out `intent/`, `spec/`, `plan/` folders; "one record per thing" | **covered in part**: extend the gate report and ledger, never a new store; decided below |

### C1: the hook when the gate cannot run

| Element | A. doc-0004: cannot-run → non-blocking | B. Fail closed: exit 1 and 2 block |
|---|---|---|
| Problem solved | a gate outage does not stop every session | a mandatory control cannot be bypassed by breaking it |
| Who bears the cost | the organisation, silently, when a session builds on unknown knowledge | the engineer, visibly, when the gate is down |
| Consistency | contradicts the CI route, which fails closed today, and the playbook's own `failIfUnavailable` (p. 43) | matches the CI route, the gate contract and p. 43 |
| Evidence | the 20-of-20 figure is obedience under an advisory arm; it does not license trusting the agent when the gate is silent | the architecture withholds for this reason (pumllint evaluation l. 43–45) |
| Escape hatch | none needed | an *advisory* hook profile, labelled so, for teams that choose it; the mandatory one ships in managed settings |

**Decision: B.** The mandatory hook blocks on 1 and 2 and says which; doc-0004's adapter survives only as the advisory profile, named as fail-open. The contract does not move: the mapping lives in the hook script.

### C2: one `as_of`

| Element | A. Keep the defaults (today; record), document "pass `as_of` to both" | B. One `as_of` per server process (`KG_AS_OF`, else today), echoed by every tool; an explicit argument still wins |
|---|---|---|
| Arms and lighthouse evidence | unchanged | unchanged: `tools/lighthouse_evidence.py` and `tools/check_mcp_server.py` already pass `as_of: record` on every call |
| Risk | a client that omits it gets a verdict and a bundle on different dates, silently | a contract change: the bundle's default moves; a minor version under decision-0003 |
| Clock rule (task-0075) | unchanged | the server reads `today()` once at start, as one decision point |

**Decision: B,** with the date in both results and `store_status` naming it. Default-today matches the gate CLI and the CI route; `record` stays an explicit choice for evidence runs.

### C4: who chooses the keys

| Element | A. Keep MCP `keys` as is | B. `keys` stays for exploration; a mandatory check refuses a report whose task is `keys`; the server can be started with `KG_MCP_TASKS_ONLY=1` to refuse `keys` |
|---|---|---|
| Exploration | unchanged | unchanged by default |
| Mandatory check | an agent can omit a key and get PROCEED | the hook and `knowgov-gate.sh` require a task class; the managed server can forbid free key sets |
| Contract | none | additive (a flag; the report already names `keys`) |

**Decision: B.**

### C9: where the stage-to-stage record lives

| Element | A. A new artefact per stage (`intent/`, `spec/`, `plan/` plus a decision file) | B. The gate report and the trace ledger carry what was relied on: verdict, threshold, task-profile digest, register tag, subject digest, `assertion_ids`, `as_of` |
|---|---|---|
| One record per thing | a second record beside the backlog and the incumbent (doc-0004) | the record stays where it is; knowgov records only what it decided on |
| Playbook p. 22 | conflicts with "one source of truth per artefact" | linkage: the report carries the ids, the incumbent keeps the artefact |
| Cost | M, and a format to maintain | S: additive fields in two schemas |

**Decision: B.** The intent, spec and plan stay in the backlog or the incumbent; knowgov's part of the "decision record" is what the gate saw.

## 8. Proposed tasks

Not created; the coordinator mints the ids. Order: P1 and P2 first (they unblock the hook), P3 and P4 next, P5 with the lighthouse, P6 parked until a pilot asks.

**P1. A fail-closed hook recipe for the gate, with a managed-settings variant** (C1, C4; supersedes doc-0004's adapter). *Description:* `instance/ci/claude/` gains a hook script and two settings snippets: a repository `.claude/settings.json` and a managed-settings fragment (only managed hooks, the knowgov MCP server allowlisted). The script calls `knowgov-gate.sh gate` with a task class, maps exit 1 and 2 to the vendor's blocking exit with a message that names the cause (finding or gate unavailable), and refuses a `keys` report. It is placed at stage transitions (plan accepted, spec committed, before push), never on every edit (playbook p. 27). An advisory profile, labelled fail-open, is offered separately. *AC:* (1) a test runs the script against a PROCEED, a BLOCKED, an unreachable store and a missing subject, and only PROCEED lets the action through; (2) the instance README states where each settings file goes and that only the managed one is mandatory; (3) doc-0004's exit-code paragraph is cited as superseded in the recipe's header.

**P2. One `as_of` per MCP server process** (C2). *Description:* `harness/mcp_server.py` reads `KG_AS_OF` (YYYY-MM-DD, `record` or `today`) once at start, defaulting to today; `gate_verdict` and `evidence_bundle` use it unless the call names its own; both results and `store_status` carry the date read. `check_mcp_server.py` and `lighthouse_evidence.py` already pass `record` explicitly and are unaffected. Contract change, minor version (decision-0003). *AC:* (1) with no argument the verdict and the bundle of one session carry the same `as_of`; (2) `tests/test_clock.py` names the new read and holds it pinned; (3) the CHANGELOG names the changed default.

**P3. A `design` task class on one public subject, rehearsed** (C3). *Description:* add `[tasks.design]` to `cargo_quote` (the keys a requirements and design pass rests on, with a stated rationale and `block_levels`), leaving `codegen` and its frozen record untouched; the lighthouse rehearsal and `store_status` show both classes. A `plan` or `review` class follows only if the pilot asks. *AC:* (1) the gate runs `--task design` on S1–S7 and the verdicts are recorded in the task notes; (2) the comparator and the codegen record are unchanged; (3) `docs/lighthouse-evaluation.md` names which class each pilot transition uses.

**P4. Findings name the key's owner and the route** (C7). *Description:* each `key`, `stale` and `lapsed` finding gains the owner unit from the subject's `register_map.toml` and the route (the owner's questionnaire, task-0009); gate-report schema minor bump, additive. *AC:* (1) S2's blocking finding names `ORG-0001` (or the unit the map gives) and the questionnaire command; (2) the schema validates both versions' reports; (3) the page's gate box shows the owner.

**P5. The pilot adds a gate-unavailable case and the block measures** (C6, C9). *Description:* `docs/lighthouse-evaluation.md` gains a rehearsed scenario where the store is unreachable and the hook stops the transition, and the pilot checklist gains missed blocks, owner-resolution time and wait per gate; task-0057's pre-registration is pointed at them. The gate report gains the task-profile digest and the register tag, so a retained report is the stage's decision record. *AC:* (1) the rehearsal shows exit 2 stopping the hook on both subjects; (2) the checklist lists correct, missed and false blocks and owner time with their source; (3) the report carries the two digests and the round trip holds them.

**P6. An eval recipe for an instance's assistant configuration** (C8; parked until a pilot asks). *Description:* an instance template workflow that, on a change to `CLAUDE.md`, `.claude/**` or the arms' model row, reruns a fixed set of the instance's governed tasks and fails on a worse verdict-obedience or oracle score than its recorded baseline, as the record does for the public subjects. *AC:* (1) the recipe runs on the example instance with the public subjects as cases; (2) a baseline is recorded by a deliberate act, never by the workflow.

C5 (isolation) needs no task: P1's recipe states one store per worktree (`KG_RDFLIB_FILE` per worktree, or one compose project) and that MCP's `scenario` argument is to be set; task-0097 is compatible.

## 9. For the maintainer to decide

- **P2's default:** whether the MCP default becomes today for every tool (a minor-version contract change), or stays split with documentation only. Recommended: today, as the CLI.
- **Whether knowgov dogfoods P1 here:** doc-0004 proposed hooks on this repository's own protected paths (vendored files, backlog through the CLI). It is still unbuilt and still the cheapest proof of the recipe; it is the maintainer's call whether a `.claude/` directory belongs in the public repository.

## 10. What would reopen this

A new playbook edition; the vendor changing hook exit semantics; a pilot whose false-block rate makes a mandatory gate unworkable; a re-measurement of the governed arm under withholding at a second model.

## 11. The maintainer's decisions, 2026-11-04

The maintainer took the advice given on §9 ("go with your advice"). Tasks 0099–0104 already carry P1–P6 (#169); the coordinating session mints any new id.

1. **The MCP date default: today for both tools, a minor version.** task-0100 as proposed: one `as_of` per server process (`KG_AS_OF`, else today); `evidence_bundle` loses its `record` default, which stays an explicit choice. A contract change under decision-0003, named in the CHANGELOG. The split default is not kept as documentation: a client that omits the date would still get a verdict and a bundle on different dates.
2. **Dogfood the hook here, small.** This repository gains a `.claude/` with two hooks on its own protected paths: a vendored file or its `SOURCE.md` edited by hand, and a backlog markdown file written other than through the CLI. They reuse task-0099's exit mapping (block on 1 and 2) and call nothing else; the knowledge gate is not wired to this repository's own commits, since no subject describes it. A new task, after task-0099.
3. **Order:** task-0099 and task-0100 together (the hook is honest only once the dates agree); then task-0102 (a block without an owner route invites an override); then task-0101; task-0103 with the lighthouse; task-0104 parked.
4. **No outcome claim** from the 20-of-20 figure in any recipe, README or release note: advisory arm, one model, toy scale. The claim is a deterministic, fail-closed check.
