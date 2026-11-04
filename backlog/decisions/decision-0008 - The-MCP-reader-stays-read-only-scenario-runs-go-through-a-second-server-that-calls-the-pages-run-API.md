---
id: decision-0008
title: >-
  The MCP reader stays read-only; scenario runs go through a second server that
  calls the page's run API
date: '2026-11-04T20:56:00Z'
status: accepted
---
## Context

doc-0016 item 2: the maintainer asked (2026-11-04) to run a scenario of a subject through MCP. Today
`harness/mcp_server.py` only reads: task-0056 AC #3, `test_five_tools_every_one_marked_read_only`
(no `load_scenario`, every tool `readOnlyHint: true`, `INSTRUCTIONS` ending "This server only
reads"), and `instance/ci/claude/managed-mcp-allowlist.json` admits it by `serverName: knowgov` as a
reader. A run wipes and reloads the one store every subject shares; on Neo4j a read during a load
sees a partial graph (doc-0016 F2). The page already runs scenarios: `POST /api/run`, one `Runner`,
one lock, the token guard of task-0096, the run folder, the banner. A deterministic run takes 2 to
18 s; an Arms run one to two minutes on CargoQuote and up to 1,500 s per arm on J-F, longer than a
client's call timeout. MCP Tasks (experimental in 2025-11-25, an extension in 2026-07-28) are not
verified in any client here.

Options (doc-0016 §4): A, a run tool on `knowgov`; B, a second server that calls the page's run API;
C, a second server that spawns `harness/run.py` itself; D, no run tool; E, MCP Tasks.

## Decision

**B** (maintainer, 2026-11-04, accepting the coordinator's proposal on doc-0016).

- `knowgov` stays a reader. No tool on it loads, runs or writes, and its annotations and allowlist
  entry keep meaning what they say.
- Runs go through a second stdio server, `knowgov-runs`, a client of the page's own run API
  (`KG_PAGE_URL`, `KG_PAGE_TOKEN` from the environment). It reuses the page's runner, lock, token
  rule and run folder; it starts no process of its own.
- Start and poll: `run_options` (read-only), `start_run {scenario, mode, row?, effort?, as_of?}`,
  `run_status {run?}`. Never one blocking call.
- Deterministic by default (`KG_MCP_RUN_MODES=deterministic`); Arms only when the operator names
  it, always at n = 1, on a row whose key variable is set. `start_run` is annotated not read-only,
  destructive (it wipes the store, never the record), not idempotent.
- An organisation that wants runs from an assistant adds `knowgov-runs` to its own allowlist; the
  shipped allowlist admits the reader only.

Rejected: A breaks the reader's contract for every tool on it; C is a second runner with its own
lock, racing the page's; D stays the default for an instance that does not add the second server;
E is revisited once a client supports the Tasks extension, without a change of meaning.

## Consequences

- task-0133 builds `knowgov-runs`; it depends on task-0127 (`run.json`, with
  `by: mcp`) and on the reader re-opening its store handle when a run ends (doc-0016 F6, task-0097).
- task-0126, task-0127, task-0128 and task-0129 do not wait for this decision.
- A run an agent starts changes what every viewer of the page sees; the server's instructions say
  so, and the page's banner names the run's initiator.
