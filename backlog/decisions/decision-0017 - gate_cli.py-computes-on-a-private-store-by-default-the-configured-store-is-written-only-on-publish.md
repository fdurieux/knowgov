---
id: decision-0017
title: >-
  gate_cli.py computes on a private store by default; the configured store is
  written only on --publish
date: '2026-11-06T18:38:00Z'
status: accepted
---
## Context

task-0184 (#326). `harness/gate_cli.py` without `--no-load` opens the store `KG_STORE` names for writing (`open_store(access="write")`), wipes it, loads the scenario (`_load`) and publishes the load on `commit()` once the report is made; its docstring states it: "A load wipes the store first, as a run does." On a stack host that store is the shared one, read by the page and its viewers, `knowgov-runs` and the read-only MCP reader. `demo/README.md` ("The gate as a command") and `docs/guide.md` tell a person to run the command there, so following them replaces the scenario every reader sees, without a warning. The record is never written; a reload restores the scenario.

task-0183 (#325, `2a443f4`) moved `capture.py questionnaire`/`review` and `transcript.py` onto `store.scratch_store()`, an rdflib graph in the process's memory, and left this command out of scope because its load is its documented contract.

## Options

- **A.** Docs only: warn, and point to `--no-load` or `KG_STORE=rdflib`.
- **B.** Compute on `store.scratch_store()` by default; load into and publish to the configured store only on an explicit flag.
- **C.** Keep the load, and refuse with exit 2 when the configured store already holds another scenario, unless a flag says to replace it.

## Decision

Option B, on the maintainer's word of 2026-11-06: "go for option B on task-0184".

1. Without `--no-load`, `gate_cli.py` loads the scenario into `store.scratch_store()` (task-0183), evaluates there, and publishes nothing. For each subject, scenario, task and `as_of`, the report (JSON and exit code) is the one the loading command gives today.
2. `--publish` loads into the store `KG_STORE` names and publishes the load once the report is made, as the command does today. The Neo4j load-memory forecast (task-0176) stays on this path. `--publish` with `--no-load` is refused (exit 2), as `--stage 2` with `--no-load` is.
3. `--no-load` is unchanged: it reads the configured store as it is.
4. `--stage 2` and `--register-previous` act on the store the load went to: the scratch store by default, the configured one with `--publish`.
5. Where rdflib cannot be imported, the default path exits 2 and names the install, as task-0183's commands do.
6. The flag's name is this record's. A conflict found while building is raised with the maintainer before the code lands.

## Consequences

- **Callers that need the publish pass `--publish`**:
  - `.github/workflows/demo.yml`'s stack steps, which load and then read through the MCP server and the saved queries;
  - `tools/check_mcp_server.py`, which loads with `gate_cli.py` and then asks the server;
  - `instance/ci/knowgov-gate.sh` and its wrappers (the GitHub action, the GitLab template, the Claude hook), where a later step reads the store. `KG_PUBLISH=1` sits beside `KG_NO_LOAD`.
  - `harness.yml`'s steps, where a later step reads the file store.
  In-process callers of `gate_cli._load` (`tools/check_round_trip.py`, `tools/check_capture_pairing.py`) pass their own handle and are unaffected.
- **One rule across the harness.** A command that computes an answer for one person never writes the shared store. The shared store's writers are a run, `gate_cli.py --publish`, `trace.py register` and the register projection; `harness/store.py`'s docstring follows.
- **The adopter docs** (`demo/README.md`, `docs/guide.md`, `instance/README.md`) say which store the command writes. A hand-run gate on a stack host no longer changes what the page shows. `--no-load` stays the way to ask about the scenario the page holds.
- **A contract change after 0.8.0.** Under decision-0016 it gathers for 0.9.0, with its `CHANGELOG.md` line under Unreleased's contract heading. Built as task-0184.

## Fit/gap

| Must satisfy | B |
|---|---|
| Exit contract 0/1/2 | Fit: no new code; a refused flag pair exits 2 |
| Report shape (`harness/schemas/gate-report.schema.json`) | Fit: equal reports across adapters, held by `tools/check_round_trip.py --chain` |
| The deterministic record | Fit: the load is the same `_load` |
| Callers that read after the load | Gap, closed by `--publish` at each caller listed above |
| The Neo4j load-memory forecast (task-0176) | Gap on the default path, since a scratch load never forecasts the server's transaction memory; kept on `--publish` |
| decision-0016 | A contract change: it gathers for 0.9.0 |

## Opportunity canvas

| Block | Content |
|---|---|
| Users | An adopter or owner running the gate by hand on a stack host; the page's viewers and the MCP clients sharing that store; instance CI |
| Problem | The documented command silently replaces the shared scenario |
| Solution | A private store by default, the configured store only on `--publish` |
| Value | The gate's answer with no side effect on anyone else's view; one rule for every command that computes for one person |
| Metric | A shared store's held scenario and generation unchanged after a documented command, held by a test on both adapters |
| Cost | One flag, the listed callers, the docs and tests |
| Risk | A caller that relied on the publish reads a stale store |

## SWOT

- **Strengths.** It reuses task-0183's mechanism, so one rule holds across the harness.
- **Weaknesses.** The default path needs rdflib, which the image pins in `demo/requirements.txt`, and the Neo4j forecast is lost on that path.
- **Opportunities.** The docs' hand-run gate becomes safe on any host, and CI and the hook keep their behaviour by passing the flag.
- **Threats.** A caller that relied on the publish could silently read a stale store. *Response:* every caller is listed and tested, and `--no-load` already refuses when the store holds another scenario.

## Advice

B. It removes the hazard at its source, as task-0183 did for the capture commands. C would still let a hand-run gate replace a scenario once someone passes the flag, and a caller that loads several scenarios in turn on one store (demo.yml's S2, then S1) would need the flag on every call. A leaves the hazard for anyone who does not read. A's doc lines land with B's build.

## Amendment A1 (2026-11-06)

On the maintainer's word of 2026-11-06: "go for (a)+(b), merge when green". Raised under point 6 while building task-0184: point 1 holds the report equal to the loading command's, and the report's required `store` field named the configured adapter, which the default path no longer computes on.

1. (a) The report's `store` names the adapter the gate computed on. That is `rdflib` on the default path, whatever `KG_STORE` names, and `KG_STORE`'s adapter with `--publish` or `--no-load`.
2. (b) An optional `published` boolean in `gate-report.schema.json`: true only with `--publish`, false on the default path, and absent with `--no-load`, which loads nothing. The MCP server's `gate_verdict` report stays equal to `--no-load`'s.
3. Point 1 reads: for each subject, scenario, task and `as_of`, the report equals the loading command's but for `store` and `published`. The verdict, findings, levels, keys, conflicts and exit code are unchanged.

**Opportunity canvas.** The problem is that a report would misstate where its answer was computed, or a reader could not tell a published load from a private one. The users are pipelines and people reading a report or its `-o` file. The solution is (a)+(b), and the measure is a report that says where it was computed and whether the shared store moved. The cost is one schema field and its tests.

**Fit/gap.** It fits schema version 2, which is additive: an older report still validates. It fits the MCP server's equality with `--no-load`, since `published` is absent there. And it fits `check_round_trip`'s adapter equality, which already ignores `store`. Gap: on a Neo4j host `store` changes from `neo4j` to `rdflib` on the default path. A reader that keyed on it sees the change, and the changelog names it.

**SWOT.**
- **Strength:** the report tells the truth about its origin and its effect.
- **Weakness:** one more field.
- **Opportunity:** a pipeline can assert `published` before a step that reads the store.
- **Threat:** a reader comparing `store` across runs. *Response:* the field is documented, and no shipped caller compares it.

**Advice.** (a)+(b), as taken. Reporting the configured adapter's name would misstate where the answer was computed, and leaving `published` out would leave a reader unable to tell whether the shared store moved.
