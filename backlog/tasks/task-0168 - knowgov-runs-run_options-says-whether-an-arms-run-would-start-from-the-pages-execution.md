---
id: TASK-0168
title: >-
  knowgov-runs run_options says whether an arms run would start, from the page's
  execution
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T12:03:00Z'
updated_date: '2026-11-06T12:06:00Z'
labels:
  - demo
  - security
dependencies: []
priority: medium
ordinal: 171000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0167 gave the page's status an execution field, {ok, why}, from harness/execution.py refusal(). harness/mcp_runs.py run_options still reports arms_enabled from the page's key count alone, so an agent could start an arms run that the page then refuses for want of a contained worker. This passes execution through and adds arms_ready, additively. The follow-up was agreed with the coordinating session on 2026-11-06.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 run_options carries execution {ok, why} as the page reports it; a page that omits it reads refused, naming task-0167
- [x] #2 run_options carries arms_ready: a key, the operator's allowed modes and execution all hold; arms_enabled and arms_on_page are unchanged
- [x] #3 The tool's description, the module docstring and the server's instructions name the two fields; tests/test_mcp_runs.py proves ok, refused, absent and arms not allowed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence: harness/mcp_runs.py _execution() reads the page's execution (refused when absent or malformed, naming task-0167). run_options adds execution and arms_ready = the page's arms_enabled and 'arms' in the allowed modes and execution.ok; arms_enabled and arms_on_page are unchanged. tests/test_mcp_runs.py test_run_options_says_whether_an_arms_run_would_start_not_only_whether_a_key_is_set covers ok, refused (no worker), a page without the field, and arms not allowed, and checks that the description and the instructions name the fields. Suite: stdlib 603/624, 21 skipped, 0 failed; with the pins and KG_TEST_REQUIRE=rdflib,node 623/624, 1 skipped, 0 failed. No JSON schema under harness/schemas/ pins run_options' output; its contract is the tool's description and the server's instructions, both updated.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov-runs' run_options now says whether an arms run would start. It passes the page's execution {ok, why} through (task-0167), and a page that omits it reads refused. It adds arms_ready, true only when a key is set, the operator allows arms and model output may run. arms_enabled and arms_on_page are unchanged, so the change is additive. The tool's description, the module docstring and the server's instructions name both fields; tests/test_mcp_runs.py proves four cases: ok, refused, absent and not allowed. start_run is unchanged: the page itself refuses an arms run without a contained worker, with the same reason.
<!-- SECTION:FINAL_SUMMARY:END -->
