---
id: TASK-0184
title: >-
  gate_cli.py without --no-load replaces the shared store's scenario on a stack
  host: compute privately by default, publish only when asked
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T18:33:00Z'
updated_date: '2026-11-06T22:19:00Z'
labels:
  - gate
  - store
  - contract
dependencies: []
references:
  - harness/gate_cli.py
  - harness/store.py
  - backlog/tasks/task-0183
priority: medium
type: task
ordinal: 184000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`harness/gate_cli.py` without `--no-load` opens the store `KG_STORE` names for writing (`open_store(access="write")`), wipes it, loads the scenario (`_load`) and publishes the load on `commit()` once the report is made. Its docstring states this as the contract: "A load wipes the store first, as a run does." On a stack host that store is the shared one. The page and its viewers read it, and so do `knowgov-runs` and the read-only MCP reader. The adopter docs tell a person to run the command there: `demo/README.md` "The gate as a command" (`docker compose exec -T app python harness/gate_cli.py --scenario S2`, and `--scenario S6 --stage 2`), and `docs/guide.md` (`python harness/gate_cli.py --scenario S2`). Following them replaces the scenario every reader sees, without a warning. The record is never written; a reload restores the scenario.

Found by task-0183's session on 2026-11-06 (#325), which moved `capture.py questionnaire`/`review` and `transcript.py` onto `store.scratch_store()` and left this command out of scope as a contract. Related, out of scope: `knowgov-runs`'s `start_run` wipes the shared store by design (decision-0008, marked destructive). On 2026-11-06 an assistant called it to *show* S3 and replaced S4 unasked; that session's improvements plan covers the client's route.

Callers that rely on the load publishing today (to be kept working, with an explicit flag if the default changes):
- `.github/workflows/demo.yml`'s stack steps (gate loads on the stack's Neo4j, then the MCP and saved-query steps read it);
- `tools/check_mcp_server.py` (loads with `gate_cli.py`, then asks the server);
- `instance/ci/knowgov-gate.sh` and its wrappers (GitHub action, GitLab template, the Claude hook), which load unless `KG_NO_LOAD=1`;
- `harness.yml`'s `KG_STORE=rdflib` steps.
In-process callers of `gate_cli._load` (`tools/check_round_trip.py`, `tools/check_capture_pairing.py`) pass their own handle and are unaffected.

**Opportunity canvas.** Users: an adopter or owner running the gate by hand on a stack host; the page's viewers and MCP clients sharing that store. Problem: the documented command silently replaces the shared scenario. Solution space: (A) docs only: warn, and point to `--no-load` or `KG_STORE=rdflib`; (B) compute on `store.scratch_store()` by default, and publish to the configured store only on an explicit flag; (C) keep the load, but refuse with exit 2 when the configured store already holds another scenario, unless an explicit flag says to replace it. Value: the gate's answer without a side effect on everyone else's view. Metric: a shared store's held scenario and generation unchanged after a documented command. Cost: A small; B and C about one flag, the callers above and tests. Risk: a contract change to a CI-facing command.

**Fit/gap.**
- The exit contract 0/1/2: A, B and C all fit; C adds a refusal at exit 2.
- The report shape: fits for all three. task-0183 relies on equal reports across adapters (`tools/check_round_trip.py --chain`).
- The deterministic record: fits for all three. The load is the same `_load`.
- The callers above: A needs nothing; B and C each need the flag where a caller wants the publish (demo.yml, check_mcp_server.py, knowgov-gate.sh when a later step reads the store).
- The Neo4j-only load-memory forecast (task-0176): B gaps on it, since a scratch load never forecasts the server's transaction memory. It can be kept on the publishing path.
- decision-0016: B and C change a CLI contract after 0.8.0, so they gather for 0.9.0, or wait for 0.10.0 if they miss the cut. A is a docs fix and is not bound by the freeze.

**SWOT, for B.** Strengths: the same mechanism as task-0183, so one rule ("a command computing for one person never writes the shared store") holds across the harness. Weaknesses: needs rdflib for the default path, which the image pins (`demo/requirements.txt`); and the Neo4j forecast is lost on the default path. Opportunities: the docs' hand-run gate becomes safe on any host; the hook and CI keep their behaviour by passing the flag. Threats: a caller that relied on the publish silently reads a stale store. *Response:* every caller above is listed and tested; and `--no-load` already refuses when the store holds another scenario.

**Advice.** B, with A's doc lines now as a fix. B removes the hazard at its source, as task-0183 did for the capture commands. C still lets a hand-run gate replace a scenario once someone passes the flag, and a caller that loads several scenarios in turn on one store (demo.yml's S2, then S1) would need the flag on every call. A leaves the hazard for anyone who does not read. The choice is the maintainer's before any code. B lands in the 0.9.0 gathering under decision-0016.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The maintainer's choice among A, B and C is recorded with its four parts before any code (in this task's notes, or a decision record if it changes the gate's contract), and its release follows decision-0016
- [x] #2 Run as the adopter docs show on a store holding another scenario, the gate command leaves that store's held scenario and generation unchanged unless an explicit flag asks to replace it; a test proves it on both adapters
- [x] #3 For each subject, scenario, task and as_of the report (JSON and exit code) equals the one the loading command gives today
- [x] #4 Every caller listed in the description still passes, with the explicit flag where it needs the publish: demo.yml's stack steps, tools/check_mcp_server.py, instance/ci/knowgov-gate.sh and its wrappers, harness.yml
- [x] #5 demo/README.md, docs/guide.md and instance/README.md say which store the command writes, in the adopter register; the module docstring and CHANGELOG.md (under its contract heading if the contract changes) follow
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate_cli.py: --publish; default loads into store.scratch_store() and publishes nothing; --publish = today's path (open_store write, load-memory forecast, commit); --publish --no-load exit 2; ScratchUnavailable exit 2; stage 2 and --register-previous on the store loaded. 2. Report: store names the adapter computed on; additive optional 'published' (schema). Raised with the coordinator under decision-0017 §6. 3. Callers that read the store after the load pass --publish: demo.yml, harness.yml, check_mcp_server, check_snapshots, lighthouse_evidence, check_trace_walkthrough, knowgov-gate.sh KG_PUBLISH=1 (+ wrappers' docs). 4. Tests: shared rdflib file (and Neo4j where reachable) unchanged without --publish; report equal to --publish's but store/published; the flag pair refused; no rdflib exit 2. 5. Docs: demo/README 'The gate as a command', docs/guide.md, instance/README, docstring, store.py writer list, CHANGELOG contract changes. 6. Suite with rdflib; check_review_walkthrough, check_trace_walkthrough, check_mcp_server and lighthouse on rdflib; harness.yml gate steps.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the maintainer chose option B ("go for option B on task-0184"). Recorded as decision-0017, accepted, with its four parts: the default computes on store.scratch_store(); --publish loads into and publishes to the configured store, as today; --publish with --no-load exits 2; --no-load is unchanged; the callers that read after the load pass --publish (knowgov-gate.sh: KG_PUBLISH=1 beside KG_NO_LOAD). A contract change after 0.8.0: it gathers for 0.9.0 under decision-0016. A's doc lines land with the build.

Callers found while building, beyond the description's list, each given --publish where a later step reads the store: tools/lighthouse_evidence.py (each scenario's gate, then --no-load and the MCP reads; stage 2 and its re-verification), tools/check_trace_walkthrough.py (S6 and its stage 2, then trace reads the store), tools/check_snapshots.py (task-0176's forecast refusal, which exists on the publish path only; SNAP-04 loads in process and is unaffected), tools/check_ci_wrappers.py and harness.yml's action steps (S6 and its stage 2 before trace-register and trace-check: KG_PUBLISH=1, the action's publish input). Callers that only read the report stay unflagged: check_review_walkthrough, check_gate_after_change, check_register_change, harness.yml's gate step, the Claude hook. Raised under decision-0017 point 6: the report's store names the adapter computed on (rdflib by default), and an additive optional published (true with --publish, false by default, absent with --no-load so the MCP server's gate_verdict stays equal to --no-load's); awaiting the maintainer.

Verified locally: KG_TEST_REQUIRE=rdflib KG_HOOK_LIVE=1 python tests/run_tests.py 679/680, 1 skipped (openai), 0 failed. tests/test_gate_publish.py on the rdflib file store: a default run leaves the published file byte for byte and the held scenario (--no-load still answers S1), --publish replaces it, the reports differ only in published, stage 2 on the store loaded, the flag pair exit 2, Neo4j unreachable and the default still answers, no rdflib exit 2. The Neo4j half of AC2 is demo.yml's stack step (held scenario and generation read before and after a default S2), which gates this PR's merge. Callers green on rdflib: check_trace_walkthrough, check_gate_after_change, check_register_change, check_ci_wrappers, check_mcp_server (S1,S2,S6 and J-F C,D3), lighthouse_evidence (the PR subset), harness.yml's gate step run as written. check_snapshots needs a disposable Neo4j: the stack job runs it. Amendment A1 appended to decision-0017 on the maintainer's word.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
gate_cli.py now loads into store.scratch_store() by default and publishes nothing, so the documented hand run no longer replaces the shared store's scenario; --publish keeps the old path (load-memory forecast included) for pipelines whose later step reads the store; --publish --no-load exits 2. Report: store names the adapter computed on, optional published true only with --publish, absent with --no-load (decision-0017 A1). Callers that read after the load pass --publish (demo.yml, check_mcp_server, lighthouse_evidence, check_trace_walkthrough, check_snapshots, the CI wrappers via KG_PUBLISH and the action's publish input); the Claude hook needs nothing and no longer replaces a developer's store. Contract change, gathering for 0.9.0.
<!-- SECTION:FINAL_SUMMARY:END -->
