---
id: doc-0016
title: >-
  Scenario runs over MCP: what an agent sees today, a run index and a run tool.
  Fit-gap, canvases, SWOTs
type: specification
created_date: '2026-11-04T19:51:00Z'
updated_date: '2026-11-04T19:51:00Z'
tags:
  - canvas
  - swot
  - brief
  - mcp
  - runs
---
*2026-11-04. Maintainer register. The brief behind the maintainer's ask of the same day: (1) the MCP server should show which scenarios have been run for the subject it serves; (2) an agent should be able to run a scenario of a subject through MCP, after listing the subject's scenarios with their run status per mode (replay, deterministic, arms). The investigation first, then a fit-gap, an opportunity canvas and a SWOT per item, the options weighed, and the items proposed. Nothing is built; no task is created. Evidence: knowgov `main` at `1f14be0`; probes run in the session on rdflib with the record's pins (rdflib 7.6.0, pyshacl 0.40.2, pyyaml 6.0.3, pumllint 0.33.0), the MCP server over stdio; `python tests/run_tests.py` 367 of 367.*

## Verdict

**Visibility: worth doing now, read-only, on the existing server, after one fix.** Today the server knows one thing about runs: the scenario the store holds (`store_status.scenario`), and it does not check that this scenario belongs to its own subject (§2 F1). It reads no run folder and no record listing. It knows nothing of modes, dates or outcomes, and it cannot see a run in progress. The page already computes most of what is asked (`views.sources_for`, `server.list_runs`, `Runner`). The work is to make run folders self-describing (a `run.json` written by the Runner), to move the folder reading into one harness module that the page and the server both read, and to serve it as a sixth read-only tool. "Replay" is not a run. It is the record being shown, and nothing records it, so its status is *the record holds it*, never *it was replayed*.

**Running a scenario: worth doing, not on this server.** A run wipes and reloads the store. task-0056 AC #3 and `test_five_tools_every_one_marked_read_only` pin the server as a reader, and the opt-in managed allowlist admits it by name (`serverName: knowgov`), so a write tool there would be admitted by a policy written for a reader. The honest shape is a second server, `knowgov-runs`, that is a client of the page's own `POST /api/run`: one runner, one lock, one token guard, one run-folder layout, and the page's banner showing the agent's run. The shape is start-and-poll, not one blocking call: an Arms run takes one to two minutes on CargoQuote and up to 1,500 s per arm in J-F's agent loop. Deterministic by default; Arms only when the operator names it, at `--n 1`, on a row whose key variable is set. It needs a decision record first.

## 1. What the MCP offers today

### The surface (`harness/mcp_server.py`)

Five tools, all `readOnlyHint`. The store sits behind `ReadOnlyStore` (the port's reads, `READS`, nothing else). One subject per process (`KG_SUBJECT`, read at import); one `as_of` per process (task-0100). What touches runs:

- `store_status`: `subject`, `store`, `scenario` (the held one: `_held`, the third field of the first `act:extract:<scenario>:<version>`), `as_of`, `scenarios` (the ids of `SUBJECT.order` and nothing else: no title, no record, no runs), the tasks, the three-valued keys.
- `gate_verdict`, `evidence_bundle`, `three_valued_answer`, `register_impact`: take `scenario` as an *expectation* and refuse a mismatch (`_check_scenario`). `baseline: record` reads the record's `deterministic.json`; a path is refused ("a path would let a client read files").
- Nothing reads `runs/` (`KG_DEMO_RUNS`), the record's arms files or the page's `Runner`. Nothing loads: the test asserts `load_scenario` is an unknown tool.

### Probed in the session (rdflib, stdio)

| Probe | Result |
|---|---|
| `run.py --deterministic --scenarios S2` (CargoQuote), then `store_status` | `"scenario": "S2"`, `"scenarios": ["S1", …, "S7"]`. The run took 1.8 s. Nothing in the reply says that S2 was loaded by a deterministic run, when, as of which date, or with what verdict. |
| `gate_verdict {scenario: "S1"}` on that store | `isError`: "the store holds S2, not 'S1'" |
| `tools/call run_scenario` | `-32602 unknown tool 'run_scenario'` |
| J-F `C` loaded (18 s), server started for CargoQuote, `store_status` | `"subject": "cargo_quote", "scenario": "C"`: another subject's scenario reported as held |
| Same store, `gate_verdict {}` (no scenario named) | `isError: false`, `BLOCKED`, "36 required key(s) at a blocking level", labelled `subject: cargo_quote, scenario: C`: CargoQuote's codegen keys resolved against J-F's graph |
| Same store, `evidence_bundle {}` | `isError`: `KeyError: "cargo_quote: no scenario 'C'"` |

### Where run state lives today

| Fact | Where | Read by the MCP server |
|---|---|---|
| The scenario the store holds, its version | the store: `act:extract:<sc>:<v>` | yes (`_held`, `gate_cli.held_version`) |
| When it was loaded | the store: the activity's `at` (in the session's Turtle: `"2026-11-04T19:45:00+00:00"`) | no: `extraction_activities` returns ids only |
| The subject the held scenario belongs to | derivable: scenario ids are the subject's own (`page_subject.scenario_subject`) | not checked |
| What the record holds per scenario | `<record_dir>/<sc>/deterministic.json` and `run*_[GB].json`; the extra sources (`rerun`, `d3check`) in `scenarios.toml` | partly (`deterministic.json`, for the baseline) |
| Demo runs: mode, model, as_of, verdict | `runs/<subject>/<stamp>/<sc>/`: mode inferred from `run*_G.json`, model from the run files' usage, `as_of` and `D6_gate` in `deterministic.json` | no |
| A run's status, start, end, exit code, initiator | `Runner.current` and `Runner.history`, in the page's memory only; lost on restart | no |
| That a scenario was replayed | nowhere: Replay is a GET that the viewer's browser renders | no, and there is nothing to read |

Record coverage, from the files: CargoQuote S1–S7 deterministic and arms (n = 5, `gpt-5.1-2025-11-13`), plus `rerun` for S1 and S6 and `d3check` for S6; J-F C and D1–D5 deterministic only ("the record ran no arm").

### Fit-gap against the ask

| Asked | Today | Gap |
|---|---|---|
| Which scenarios have been run, for the current subject | the held one, not checked against the subject | the list per mode, with dates and outcomes; the subject check |
| List the subject's scenarios | ids only | titles, the card line, the record's sources |
| Run status: replay | none | "replay" is the record: available or not, deterministic and arms, with n and model |
| Run status: deterministic, arms | none | per scenario, runs newest first: id, mode, model, effort, as_of, started, status, gate verdict, the arms' decisions and suite |
| A run in progress | the page's memory | invisible to the agent; on Neo4j, a gate call during a run reads a half-loaded store (F2) |
| Run a scenario | refused by design | a tool, its policy, its asynchronous shape, its server |

## 2. Findings that hold before anything is built

- **F1, a defect.** The store is one database for every subject. The server checks the held scenario against the caller's expectation, never against its own subject. A server for CargoQuote with J-F `C` loaded reports `scenario: C`, and when a call names no scenario, `gate_verdict` returns a well-formed BLOCKED that is CargoQuote's keys read against another subject's graph. instance/README.md's advice (pass `scenario` in every call) turns this into a refusal, but the default call gives a wrong answer that looks right. Fix: `_held` returns the scenario only when it is in `SUBJECT.scenarios`; otherwise `store_status` names the foreign scenario (`held_by_other_subject`) and every scenario-reading tool refuses. Small; a test on a stub store that holds `C`.
- **F2, a hazard.** On Neo4j a run wipes the store and then loads it in steps, so a read during that window sees a partial graph. The page serialises loads, not reads, and the MCP server cannot see a run. rdflib avoids this only because of how it stores: the server reads the previous Turtle file until the run's `close` writes the new one. Once a run is visible (`run.json`, below), the reading tools refuse while a run is loading the store, and name the run.
- **F3, run metadata is volatile.** Status, start, end, exit code and initiator live in `Runner`'s memory. The folder carries a log whose name gives scenario and mode, and files from which mode, model and as_of are inferred. A `run.json` that the Runner writes at start and at end makes the folder self-describing: for the page after a restart, for the MCP server, and for anyone who reads the volume.
- **F4, the contract.** Read-only is task-0056's AC #3. Its test asserts `load_scenario` is unknown, `INSTRUCTIONS` end with "This server only reads", every tool carries `readOnlyHint: true`, and `managed-mcp-allowlist.json` admits `serverName: knowgov`. A run tool on this server makes all of these untrue at once.
- **F5, duration and cost.** Deterministic: 1.8 s (CargoQuote S2) and 18 s (J-F C) on rdflib in the session; about 5 s on Neo4j (the page's note). Arms: "one to two minutes" and "a few cents" on CargoQuote (demo/README.md). J-F's agent arm has a ceiling of 30 calls, 1.5 M tokens and 1,500 s per run (`agent.DEFAULT_CEILING`). A tool call that blocks for 25 minutes outlives any client's timeout, so the shape is start-and-poll. MCP's own answer, Tasks, shipped as experimental in 2025-11-25, and the 2026-07-28 revision moves it out of the core into an extension (`io.modelcontextprotocol/tasks`). Two plain tools work in both protocol eras the server speaks.
- **F6, the handle.** task-0097 (one read-only store handle per process) and instance/README.md's "restart after you load another scenario" both assume that the store changes under the server only from outside. A run that the agent starts must be followed by a re-open: key the handle on the held activity and its `at`, or on the end recorded in `run.json`.

## 3. Item 1: run visibility, read-only

### Opportunity canvas

| Element | Reading |
|---|---|
| Problem | An agent connected to knowgov cannot tell what has been run for its subject. It sees the held scenario's id, but not whether the record covers a scenario, which demo runs exist, in which mode, as of which date, with what verdict, or whether a run is under way. The held id may also be another subject's (F1). So the agent asks the human, or answers on the wrong load. |
| Users | The maintainer who drives the demo from Claude Desktop or Code (task-0117's route, and the phone through Remote Control); an operator's assistant in a private instance, before it calls the gate; the lighthouse evaluator who reads which runs back a claim. |
| How it is done today | The page: `/api/scenarios` (sources per scenario), `/api/runs`, `/api/run`. The agent: `store_status` and refusals. |
| Options weighed | (a) A sixth read-only tool on `knowgov` that reads the record and `runs/<subject>/` through one harness module the page also uses (chosen). (b) The MCP server calls the page's GET routes (rejected: a reader that depends on the page being up, and a host-run server has no page URL). (c) Extend `store_status` with the lists (rejected: its reply is the store's, cheap, and called first; a run index can grow). (d) MCP resources, `knowgov://runs/…` (later, beside (a): clients show resources unevenly, and a tool is what an agent calls). |
| Solution outline | Step 0: F1. Step 1: `run.json` from `Runner.start` and `Runner._wait`, with id, subject, scenario, mode, n, row, model, effort, as_of, started, finished, status, exit_code and `by` (page or mcp). Step 2: `harness/runs_index.py` reads the record's sources and the run folders per scenario (from `run.json`, else inferred as `views.sources_for` does today); the page's `list_runs` and `sources_for` read through it. A tool `scenario_runs {scenario?, limit?}` returns, per scenario, its title and card line, `record` (deterministic; arms n and model; extra sources), `runs` newest first, and `held` (version, stage, loaded at), plus `run_in_progress`; `store_status` gains `loaded_at`. Step 3, optional: `scenario_result {scenario, source}`, what Replay shows, as data (the D6 gate, the keys' levels, the arms' decisions and suite), so "replay" is reachable without a load and is named as not the store. |
| What stays | Read-only. No path argument: the roots are fixed (the subject's record, `KG_DEMO_RUNS/<subject id>`). One subject per process. The as_of rule. The page's routes and their JSON. |
| What is new | A file per run, a harness module, one or two tools, `store_status.loaded_at`, the F2 refusal, a row in instance/README.md's tool table, a check in `tools/check_mcp_server.py`. |
| Value | The agent answers "what has been run, and what did it show" by itself. Wrong-subject and mid-run answers become refusals. The page keeps its run statuses across a restart. |
| Cost | Step 0 about 40 lines, step 1 about 40, step 2 about 200 with tests, step 3 about 100. No dependency. |
| Measures | `scenario_runs` on CargoQuote lists S1–S7 with the record's arms at n = 5 and S6's three sources; after a page run, the run appears with mode, as_of and a verdict equal to its `deterministic.json`; the F1 probe refuses; the page's `/api/scenarios` is unchanged byte for byte in the stack job. |

### SWOT

| | |
|---|---|
| **Strengths** | Every fact is already on disk or in the store. The page's reading of run folders exists and is tested. Read-only keeps the server's contract and what its allowlist entry means. Standard library only. |
| **Weaknesses** | A run folder written before `run.json` is inferred: its status, start and initiator are unknown. The index reads the volume the page writes, so a host-run server sees nothing unless `KG_DEMO_RUNS` points at it. One subject per process stays, so "the current subject" is the server's `KG_SUBJECT`, not the page's drop-down. |
| **Opportunities** | `run.json` is the provenance a lighthouse claim cites (which run, which model, which date). The same index gives the page a runs panel that survives a restart. `by: mcp` lets the reconciliation count agent-initiated runs. |
| **Threats** | The run folders become an interface, and a layout change breaks the tool silently unless the index is their only reader (hence the shared module, and a test that the page and the tool agree). Listing model names and dates widens what an agent learns of the operator's spending: harmless on the public subjects, an operator's choice in an instance. |

## 4. Item 2: running a scenario through MCP

### Options weighed

| Option | What | Reading |
|---|---|---|
| A | `run_scenario` on `knowgov` | Rejected: F4. The annotations and the allowlist entry describe the server as a reader; one write tool makes both untrue for every tool on it. |
| B | A second server, `knowgov-runs`, that calls the page's `POST /api/run` and `GET /api/run` | Chosen. One Runner and its lock, the token guard (task-0096), the run folder, the page's banner; nothing new in the harness. It needs the page up, which the stdio route (`docker compose exec -T app`) gives. |
| C | A second server that spawns `harness/run.py` itself | Rejected: a second runner whose lock is not the page's (two loads race; F2 gets worse), a second folder convention, and the environment assembly (`models.resolve`, `KG_RDFLIB_FILE`, the stage-2 derived copy) duplicated. |
| D | No run tool: visibility only, and the agent asks the human to click | The zero-code route, and Item 1's outcome anyway. Keeps a person on every store wipe. |
| E | MCP Tasks for the long call | Later: experimental in 2025-11-25, an extension in 2026-07-28, client support not verified here. B's start-and-poll moves onto it without a change of meaning. |

### Opportunity canvas

| Element | Reading |
|---|---|
| Problem | The agent can see that S3 is not loaded but cannot load it. instance/README.md tells the human to load it on the page and restart the client. A deterministic load takes 2 to 18 s; the round trip through a person takes minutes and breaks a phone session. |
| Users | The maintainer through Claude Desktop, Code or the phone; an evaluator who walks the seven scenarios. Not an instance's coding assistant by default: it should read the instance as it was loaded. |
| How it is done today | The page's Replay, Deterministic and Arms buttons; `harness/run.py` from a shell; the CI jobs. |
| Options weighed | B chosen; D as the zero-code route; A and C rejected; E later. |
| Solution outline | `knowgov-runs`, stdio, with the page's URL and token from the environment (`KG_PAGE_URL`, default `http://localhost:8080` inside the container; `KG_PAGE_TOKEN`). Tools: `run_options` (read-only: the modes the operator allows, `deterministic_enabled`, `arms_enabled`, the model rows with their availability, never a key); `start_run {scenario, mode, row?, effort?, as_of?}` (n fixed at 1, as on the page; refused while another run is under way, with the page's message); `run_status {run?}` (status, elapsed time, the log's tail, and when done the result summary and the source id that `scenario_result` reads). `KG_MCP_RUN_MODES` is `deterministic` by default; `arms` only when the operator names it. Annotations: `start_run` not read-only, destructive (it wipes the store, never the record), not idempotent, open-world when arms. `INSTRUCTIONS` say that the store is shared with the page. The read-only server re-opens its handle when `run.json` records a run's end (F6). |
| What stays | The record is never written (runs land in `runs/`). The page's token rule. The `knowgov` allowlist entry admits the reader only; an organisation that wants runs adds `knowgov-runs` itself. |
| What is new | A decision record (the reader stays a reader; runs go through the page); a server module, with the protocol layer shared with `mcp_server.py` (`Server` takes a tool table instead of the module's `TOOLS`); `by: mcp` on the Runner's record; a README section; a stack-job step (start a deterministic S1, poll to done, `gate_verdict` on S1 gives PROCEED). |
| Value | The agent closes its own loop: list, load, gate, read. A scenario walk from the phone. The lighthouse rehearsal can be driven by an agent. |
| Cost | About 300 lines with tests, plus the decision. Depends on Item 1 steps 0 and 1. |
| Measures | Tests on a stub page: a mode is refused unless allowed, n is never above 1, a second start is refused with the page's message, the token is passed. The stack job's step. `tools/list` on `knowgov` unchanged: every tool read-only. |

### SWOT

| | |
|---|---|
| **Strengths** | The page's run API already does the hard parts: validation, rows, effort, as_of, token, lock, folder, the stage-2 derived copy. The transports and both protocol eras exist. Deterministic runs take seconds and cost nothing. |
| **Weaknesses** | Depends on the page process. One store means that an agent's run changes what every viewer of the page sees, and wipes the register's projection. Runner history is per process until `run.json` exists. A run reads as of `record` by default and the reader as of today, so an agent that compares the two must name the date. |
| **Opportunities** | An evaluator script over MCP instead of the page. `by: mcp` gives the reconciliation a count of agent-driven runs. Tasks, once clients support the extension. The same server could later carry the register's projection, behind the same guard. |
| **Threats** | Spend and injection: kit or instance text that reaches the agent through `evidence_bundle` could steer it to start Arms runs. Mitigated by arms off by default, n = 1, the client's per-call prompt on a tool that is not read-only, the ceilings (`arms.DEFAULT_CEILING_TOKENS`, 6 M per process; the agent's 1.5 M tokens and 1,500 s), and the one-run lock. A widened page (`KG_BIND` beyond loopback) with its token in the runs server's environment: any client of that server now holds the token. A store-wiping tool approved once with "always allow" becomes a background habit. |

## 5. Proposed backlog items (not created)

1. **The held scenario is checked against the server's subject** (F1). Bug, high: today the default call gives a wrong verdict that looks right.
2. **A run folder describes itself: `run.json` from the Runner** (F3), with `by`.
3. **`scenario_runs`: the subject's scenarios with the record and the runs per mode, as a sixth read-only MCP tool**, through `harness/runs_index.py` shared with the page; `store_status.loaded_at`; the mid-run refusal (F2). Depends on 1 and 2.
4. **`scenario_result`: what Replay shows, as data, read-only.** Optional; depends on 3.
5. **Decision: the MCP reader stays read-only; runs go through a second server that calls the page.** Then **`knowgov-runs`: start and poll a scenario run through the page's run API**, deterministic by default, arms on the operator's word. Depends on 2, and on task-0097 or the re-open rule (F6).

Order: 1, 2 and 3 do not wait for the decision and are useful alone; 5 waits for it.

## Sources

- MCP 2025-11-25, Tasks (experimental): https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks
- SEP-1686, Tasks: https://modelcontextprotocol.io/seps/1686-tasks
- The 2026-07-28 release candidate (Tasks moved to an extension): https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
