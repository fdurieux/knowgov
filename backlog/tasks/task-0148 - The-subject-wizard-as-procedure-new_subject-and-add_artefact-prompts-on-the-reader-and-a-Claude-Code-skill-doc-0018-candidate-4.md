---
id: TASK-0148
title: >-
  The subject wizard as procedure: new_subject and add_artefact prompts on the
  reader and a Claude Code skill (doc-0018 candidate 4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:24:00Z'
updated_date: '2026-11-05T23:46:00Z'
labels: []
dependencies:
  - TASK-0146
  - TASK-0147
documentation:
  - >-
    backlog/docs/doc-0018 -
    A-subject-wizard-over-MCP-creating-a-subject-and-adding-its-artefacts-with-an-assistant.-Pipeline-sense-and-nonsense-fit-gap-opportunity-canvas-SWOT.md
priority: medium
type: feature
ordinal: 154000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Onboarding a subject is the lighthouse's first hour. doc-0018 §4 lists the steps and §3 the stop condition; decision-0008 keeps the reader read-only, so the wizard is a procedure the client runs with its own file tools, ending in a pull request a person reviews, never a write through knowgov. Since doc-0018, Claude Code runs an MCP prompt as a slash command, and the 2026-07-28 revision documents elicitation for interactive Claude Code (Claude Desktop unverified). The maintainer's onboarding study (2026-11-05) is the user-experience input. Approved by the maintainer on 2026-11-05.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The reader declares the prompts capability and serves new_subject and add_artefact through prompts/list and prompts/get in both protocol eras; their text is read-only by nature and pinned by a test
- [x] #2 A Claude Code skill under instance/ci/claude/ walks doc-0018 §4: scaffold on a branch with the client's file tools, subject_check or check_instance.py after every write, proposal_impact first for a subject about a new product, and the exits (a pull request, the owners' questionnaires)
- [x] #3 instance/README.md walks a first subject through it in the adopter register; the onboarding study's findings are applied or the departure recorded; CHANGELOG Unreleased carries the line
- [x] #4 Prompt and skill carry the never-list (no content drafted, no attestation written, no key drawn from the yield) and the stop condition, and name only tools that exist; task-0147's hook backs the never-list
- [x] #5 instance/README.md states Claude Desktop's role: asking the gate (gate_verdict, evidence_bundle, the impact tools) until the maintainer's Desktop test on this task's branch shows the prompts listed and subject_check running; onboarding is Claude Code's (maintainer, 2026-11-05, doc-0021 §10.2). MRTR elicitation is not in this task (doc-0021 §10.4)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. One source: instance/ci/claude/skills/knowgov-onboard/SKILL.md in parts; harness/wizard.py serves new_subject <id> <task> and add_artefact <subject> [file] verbatim; reference part generated from kinds.toml and instance/mappers.toml. 2. Server: prompts capability, prompts/list and prompts/get in both eras, Mcp-Name on stateless prompts/get; knowgov-runs none. 3. doc-0021 §8 applied; no elicitation, no resources. 4. README walkthrough and Desktop's role. 5. After #242 and #248 merge: rebase, drop the workarounds B1/B2 retire, add register_nodes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Draft PR fdurieux/knowgov#245; branch claude/task-0148-wizard offered for the maintainer's Desktop test.

Rebased onto main after #242, #248, #249; B1/B2 workarounds removed, register_nodes first; marked ready. run_tests 501/502 (1 skipped), check_mcp_server.py --scenarios S1 every check holds.

Merged as fdurieux/knowgov#245 on a fully green matrix at 54a8207 (tests, stack, rdflib; publish skipped). Evidence: tests/test_wizard.py (both eras and transports with the Mcp-Name check, argument validation, each prompt equal to the skill's parts, the never-list and stop condition, every backticked tool real, mappers.toml equal to harness/extract.py's EXTRACTORS read by ast, knowgov-runs without prompts); check_mcp_server.py --scenarios S1 lists and gets the prompts over stdio and HTTP; run_tests 498/502 stdlib (4 skipped), 501/502 with the pins. doc-0021 §8 applied: items 1 to 12; B1/B2 workarounds retired after #248 and #249; register_nodes first. Departures recorded: none outstanding (register_nodes added once #238 merged). The maintainer's Desktop test is still to run; the README states Desktop's role until then.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The subject wizard as a procedure the client runs, ending in a pull request a person reviews. One text, two carriers: the Claude Code skill `instance/ci/claude/skills/knowgov-onboard/SKILL.md`, and the reader's prompts `new_subject <id> <task>` and `add_artefact <subject> [file]` (`prompts/list` and `prompts/get` in both eras), cut from it verbatim by `harness/wizard.py`, which also generates its reference part (the kinds table and `instance/mappers.toml`'s conventions). It carries the never-list, backed by task-0147's hook, and doc-0021 §6's stop condition. It runs in doc-0021 §8's order: `register_nodes` and `register_impact` (`proposal_impact` first for a new product), documents into their kinds, manifest, keys, the attestation commented out, questionnaires last, reading task-0149's findings and relying on task-0150's rescan. No elicitation, no resources; `knowgov-runs` declares no prompts. `instance/README.md` walks a first subject and states Desktop's role until the maintainer's test. Merged as #245.
<!-- SECTION:FINAL_SUMMARY:END -->
