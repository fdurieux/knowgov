---
id: TASK-0207
title: Runs and trace single fixes (doc-0030 R6, R8, R12)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T14:44:00Z'
labels:
  - review
  - runs
  - trace
dependencies: []
priority: low
type: bug
ordinal: 207000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

R6: the run's seconds ceiling reached mid-stream is recorded as an API error, so --resume re-runs it and spends again. R8: under --baseline, annotate marks the findings the baseline held as errors though the gate exited 0. R12: route (c) records the configured model, not the one that answered. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A run that reaches its seconds ceiling is recorded as the ceiling, not an API error, and --resume does not re-run it
- [x] #2 Gate findings a baseline held carry held, and annotate prints them below error
- [x] #3 Route (c) records the model that answered (usage model)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. R6: agent.run classifies a failed call at or past the monotonic deadline (bounded's TimeoutError, the client's timeout class) as the seconds ceiling, a ceiling trace turn; run.py then records no api_error and --resume keeps the cell. The idle cut stays an api error.
2. R8: gate_cli.report, under --baseline, marks each finding held (false for the regression's own: fallen keys, newly suspect outputs, with a worse verdict the task finding and blockers); schema additive; annotate passes held to level() and titles it.
3. R12: transcript.model_call records the usage model from arms.call; the inference meta names it, falling back to the configured one.
4. Tests failing on the old code first; run_tests with pins, stdlib, J-F; the comparator; CHANGELOG > Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08 evidence (no model called; stub responders and a recorded-style trickling stream only).
- AC1, R6: harness/agent.py _deadline_passed() treats a failed call at or past the monotonic deadline (0.5 s slack) that is a timeout (TimeoutError from bounded, or the client's *Timeout* class at its timeout set to the time remaining) as the seconds ceiling: stopped_by 'ceiling: <n> seconds', a 'ceiling' trace turn, abstain. run.py records api_error only for stopped_by starting 'api error', and --resume re-runs only cells with api_error, so the cell is kept. tests/test_agent.py test_the_seconds_ceiling_reached_mid_stream_is_the_ceiling_not_an_api_error covers a never-ending trickled stream through bounded, a client-timeout class at the deadline, and an idle silence well before the deadline, which stays an api error. It failed on the old code with "api error: the run's deadline passed while the model was answering".
- AC2, R8: gate_cli.mark_held(), under --baseline only. held is false for a fallen key, a newly suspect output, and, with a worse verdict, the task finding and every blocker; true otherwise. gate-report.schema.json gains held on findings (additive, not required). annotate passes held to level() and titles the finding 'held by the baseline'. tests/test_annotate.py test_a_gate_finding_the_baseline_held_is_never_an_error: with no regression, exit 0 and no ::error, SARIF all warning; with one fallen key, exit 1 and exactly that key an error; with no baseline, no held field and the threshold decides (4 errors). Schema-valid each way. It failed on the old code (KeyError 'held').
- AC3, R12: transcript.model_call() records arms.call's usage model; the inference meta names it, falling back to the configured one. tests/test_transcript.py test_the_file_records_the_model_that_answered_not_the_one_configured: run() on CargoQuote S2, rdflib scratch store, arms.call stubbed (usage model answered-model-2026-11-01, KG_ARMS_MODEL configured-alias). It failed on the old code with 'configured-alias'. It skips without rdflib, or on another subject's pass (cargo-quote-subject).
- Checks: pins (rdflib, pyshacl, pumllint, pyyaml, openai) with KG_TEST_REQUIRE=rdflib,node,openai gave 789/790 passed, 1 skipped, 0 failed. Stdlib without yaml: 744/790 passed, 46 skipped, 0 failed. Stdlib with yaml: 750/790. J-F pass: 750/790, 40 skipped, 0 failed. The comparator after KG_STORE=rdflib run.py --deterministic gave 0 differing leaves over 7 scenarios. 0.8.0's CHANGELOG section is unchanged.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Three single fixes from doc-0030.
- R6: an agent run cut by its own seconds ceiling mid-stream, by bounded's deadline or the client's timeout set to the time remaining, now ends as 'ceiling: <n> seconds' rather than an api error, so --resume keeps the cell and does not pay again. An idle silence before the deadline is still an api error.
- R8: under --baseline, every gate finding carries held. It is false only for the regression's own findings: a fallen key, a newly suspect output, and with a worse verdict the task finding and the blockers. annotate shows a held finding as a warning at most, so a gate that exited 0 shows no error annotation. The schema change is additive.
- R12: route (c)'s proposals file names the model that answered (the usage model from the stream), not KG_ARMS_MODEL.
Each test failed on the old code first. Every check passed: the suite with the pins, without yaml, and on J-F, and the comparator (identical, 7 scenarios). CHANGELOG lines are under Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
