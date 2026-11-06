---
id: TASK-0183
title: >-
  Capture questionnaire, review and transcript compute on a scratch store, never
  the shared one
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T18:06:00Z'
updated_date: '2026-11-06T18:10:00Z'
labels:
  - store
  - capture
dependencies: []
references:
  - harness/capture.py
  - harness/transcript.py
  - harness/store.py
priority: high
type: bug
ordinal: 183000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## The finding

`harness/capture.py questionnaire` and `capture.py review` open the store `KG_STORE` names for writing, wipe it and load their scenario (`gate_cli._load`), and publish that load on exit. `harness/transcript.py` does the same. On an instance whose stack runs Neo4j, that store is the shared one: the page, its viewers, `knowgov-runs` and the read-only MCP server all read it. An owner following the gate's own route (`capture.questionnaire_route`: "python harness/capture.py questionnaire --scenario S4 --task codegen --out DIR") would replace the scenario everyone reads with the one the questionnaire needed, with no warning. Found on 2026-11-06, when the maintainer's local Claude Code avoided it only by choosing `KG_STORE=rdflib` by hand. The onboarding skill already carries that workaround (`KG_STORE=rdflib` before the command), which shows the hazard was known in one place and not fixed at its source.

These three commands compute an answer for one person (a questionnaire, a review's check, a transcript's candidates). Their load is a means, never a result: what they write is files (`DIR/questionnaire-*.toml`, `captures/reviews/*.toml`, `captures/inferred/*`), and every later load reads those files. The shared store's writers by design are a run (`run.py`, the page's run button, `knowgov-runs`'s `start_run`), the gate command (`gate_cli.py`, whose load is its documented contract and whose `--no-load` reads the held store), `trace.py register` (derived outputs, with its ledger) and the register projection.

## Opportunity canvas

- **Problem.** A person's step on the capture route silently replaces the scenario the whole instance reads. The page then shows a scenario nobody chose; a gate verdict read over MCP answers for another scenario, or refuses (`held_by_other_subject`); a run in progress is not protected.
- **Users.** Key owners answering questionnaires, reviewers ruling, whoever runs route (c); and everyone reading the shared store at that moment.
- **Solution.** A scratch store: an rdflib graph in this process's memory, never a file and never the store `KG_STORE` names. `questionnaire`, `review` and `transcript.py` load into it. What they compute is unchanged, because the gate's report is the same on either store (`tools/check_round_trip.py --chain`, the comparator).
- **Measure.** The shared store is byte-for-byte and generation-for-generation unchanged after each command, held by a test on a persisted rdflib file. The questionnaire, review and transcript outputs are unchanged, held by the existing walkthroughs (`harness.yml`'s capture step, `check_review_walkthrough.py`, `check_transcript_route.py`, `check_capture_pairing.py`).
- **Cost.** One helper in `store.py`, three call sites, docs. rdflib becomes required for these three commands where a Neo4j-only host had none. It is pinned in `demo/requirements.txt` and in the image.

## Fit/gap

Must satisfy:
- **The store port's read/write separation (task-0141.02).** Fits: the scratch store is a writer on nothing shared, so nothing is published to anyone.
- **Generations (task-0141.06, decision-0014).** Fits: no publication lands on the shared store, so no reader sees `StoreChanged` because of a questionnaire.
- **The gate contract.** Fits: no flag or exit code changes. `capture.py` already exits 2 on `CannotRun`; a host without rdflib now gets that exit with the install line, where before it loaded whichever store was configured.
- **Determinism and the record.** Fits: the scratch load is `gate_cli._load`, the deterministic load, so the outputs are the same files.
- **`review`'s check against "what the store holds".** Fits: it reads the scenario as loaded with the captures and reviews already written, which is exactly what the scratch load gives. The shared store never held the reviews being checked anyway, since `review` writes its file after its load.

Gaps:
- **No private Neo4j database on Community.** A scratch store is necessarily rdflib, so a Neo4j-specific behaviour would be invisible to the capture commands. The round-trip checks hold that none affects a gate report.
- **`gate_cli.py` without `--no-load` also reloads the store `KG_STORE` names.** That is its documented contract and CI's use, and it is out of scope here. Recorded as a follow-up to weigh, not changed.

## SWOT

- **Strengths.** The fix is at the source, not in the route text: every caller (the route, the skill, a person typing the command) is safe without knowing about the hazard. No flag to forget, no environment variable to set. The outputs are unchanged.
- **Weaknesses.** It adds an rdflib requirement for three commands. Each load parses in memory: S4 takes seconds, the same as the rdflib job.
- **Opportunities.** One named place (`store.scratch_store`) for every future "compute, don't publish" command. The skill's `KG_STORE=rdflib` workaround can go.
- **Threats.** Someone might rely on the side effect, expecting the page to show the questionnaire's scenario afterwards. Unlikely, since no doc says so, and the changelog names it. A future command might call `open_store` for a private computation again; a test holds the three commands to the scratch store, and `store.py`'s docstring states the rule.

## Advice and conclusion

Do it at the source: `store.scratch_store()` for the three commands, no opt-out. The alternatives:
- **Warn only.** A band-aid: the route still tells the owner to run a command that wipes the shared store.
- **`--no-load`, reading the held store.** Wrong: the held store may hold another scenario, or another subject, and lacks the captures just written.
- **A flag defaulting to scratch.** An opt-in to a hazard with no use.

The rule this records: *a command that computes an answer for a person loads into a scratch store; only a run, the gate command, a trace registration and the register projection write the shared store.* No decision record: this applies the store port's existing separation (task-0141.02) to three commands and chooses nothing new. The four parts are kept here, as for task-0182.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 harness/store.py has scratch_store(): an rdflib graph in this process's memory, never a file and never the store KG_STORE names; without rdflib it raises a clear error naming the install
- [x] #2 capture.py questionnaire, capture.py review and transcript.py load into scratch_store(); with rdflib absent they exit 2 with that message; their outputs are unchanged (the walkthroughs in harness.yml stay green)
- [x] #3 A test runs questionnaire and review with KG_STORE=rdflib and KG_RDFLIB_FILE pointing at a published store holding another scenario, and holds the file's bytes, its generation and its held scenario unchanged
- [x] #4 A test holds the three commands to scratch_store: none of them calls open_store
- [x] #5 Docs: instance/README.md's capture section says the commands load a private copy and leave the shared store as it is; the onboarding skill drops its KG_STORE=rdflib workaround (wizard --check stays fresh); CHANGELOG under Unreleased > Changes
- [x] #6 python tests/run_tests.py passes with rdflib installed
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. store.scratch_store(): rdflib in memory, ScratchUnavailable without rdflib. 2. capture questionnaire/review and transcript.py load into it. 3. tests/test_scratch_store.py: AST guard, unchanged published file, neo4j configured and unreachable, the missing-rdflib message. 4. instance/README capture section, onboarding skill, CHANGELOG. 5. Full suite with rdflib required; the review, transcript, pairing walkthroughs and harness.yml's capture step.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified: KG_TEST_REQUIRE=rdflib python tests/run_tests.py 669/671, 2 skipped (openai, hook-live), 0 failed. tests/test_scratch_store.py fails on the old capture.py (shared store changed; open_store named; Neo4j unreachable refused) and passes on the new. Walkthroughs green on rdflib: check_review_walkthrough.py, check_transcript_route.py, check_capture_pairing.py, harness.yml's capture step run verbatim. wizard.py --check fresh. Follow-up to weigh, not done: gate_cli.py without --no-load also reloads the configured store (its documented contract, CI's use); a person running it on a stack's host replaces the shared scenario too.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
capture.py questionnaire and review and transcript.py now load into store.scratch_store(), an rdflib graph in this process's memory, instead of wiping and reloading the store KG_STORE names (the stack's shared Neo4j). The gate's own resolution route therefore no longer replaces the scenario the page and the MCP servers read. Outputs unchanged; without rdflib the commands exit 2 naming the install. The opportunity canvas, fit/gap, SWOT and advice are in the description. Follow-up to weigh: gate_cli.py's default load has the same effect, by contract.
<!-- SECTION:FINAL_SUMMARY:END -->
