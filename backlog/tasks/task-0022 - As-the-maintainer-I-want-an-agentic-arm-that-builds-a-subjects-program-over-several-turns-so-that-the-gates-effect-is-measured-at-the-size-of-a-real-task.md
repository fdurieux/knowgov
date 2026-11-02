---
id: TASK-0022
title: >-
  As the maintainer, I want an agentic arm that builds a subject's program over
  several turns, so that the gate's effect is measured at the size of a real
  task
status: To Do
assignee: []
created_date: '2026-11-01T23:23:00Z'
updated_date: '2026-11-02T09:19:00Z'
labels:
  - story
  - arms
milestone: m-3
dependencies:
  - TASK-0021
  - TASK-0005
references:
  - subjects/jef_data_load/prompts/system.md
  - harness/arms.py
  - harness/measures.py
  - subjects/jef_data_load/oracle/jef_suite.py
  - >-
    subjects/jef_data_load/vendor/recreate_experiment/rebuilds/codex-2026-10-24/README.md
documentation:
  - backlog/docs/doc-0002 - Agentic-arm-opportunity-canvas-and-SWOT.md
priority: medium
type: story
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The arm is one chat completion: one prompt, one JSON reply, one module (harness/arms.py call(); the system prompt fixes the JSON). On CargoQuote that is the task. On the J-F subject the task is the whole jef.data program (the reference rebuild is 716 lines in nine files; J-F's original is about 3,500) with a 266,000-character bundle for G and 420,000 characters of documents for B, and on the maintainer's first Arms run (D3, gpt-5.5, 2026-11-01) both arms abstained in 1 of 1 runs, so the oracle had nothing to grade. The J-F record's rebuilds were agentic sessions of a coding agent (a pre-registered protocol, hash-pinned inputs, a working directory, the kit's suite to run, about twenty-five minutes each); the harness never ran them and vendors their output, so the subject's record_model is empty and its Arms mode measures nothing. An arm that works in a sandbox directory over several turns, reads the bundle or the documents through tools, writes files, runs the scenario's own suite and ends with a decision and an assumptions file would make the Arms mode match how the record was produced, and the two subjects would then measure the same thing at two sizes. What stays: the gate, the bundle, the decision vocabulary, the flagged-assumption and resolvable-reference measures (harness/measures.py), the oracle (the pristine suite grades a directory as it grades the reference rebuild), the budget guard, the endpoint as instance configuration (task-0005, task-0013). What is new: a turn loop with tool calls, a sandbox, a per-run budget, a trace (turns, tool calls, documents or assertions read, cost, wall time), and a subject table saying how the artefact is laid out and how its suite is run, since nothing in harness/ may name a subject (task-0002). Known limits to record, not to solve: tool calling differs across OpenAI-compatible endpoints; runs are long and non-deterministic, so the comparator cannot hold them to the record leaf by leaf; a different agent on a different model is a reference beside the record, never the same experiment; the kit has been public since October 2026. The story stops after its first subtask if the spike shows the task exceeds the model on offer. Spike finding 2026-11-02 (task-0022.01 notes): B generates a 664-line module in one reply (oracle 2 of 12); G abstains because the bundle carries no verbatim document the task names (the packaged TOML files, the parser tables), which is a bundle-content question before it is an agent question.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A scored Arms run on the J-F subject's D3 yields code the oracle grades for at least one arm, with its trace (turns, tool calls, what was read, cost, wall time) in the run folder and on the page
- [ ] #2 The governed arm's trace names the assertions it consulted through the store port, so the page can show the consulted set beside the gate
- [x] #3 Every run is bounded by a per-run ceiling in calls, dollars and wall time, recorded in the run folder; a run that hits it ends with a decision of abstain and says why
- [x] #4 The CargoQuote subject still runs its one-reply arm unchanged and its deterministic record compares identical; the agentic loop is selected by the subject's manifest, and nothing in harness/ or demo/ names a subject
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Spike task-0022.01 closed 2026-11-02 (the maintainer: route 'bundle first', then 'close and start 02'). Three D3 probes of the one-reply arm, gpt-5.5, n=1 each, est. $1.1 in all: B generated 664- and 811-line modules in two draws (oracle 2 and 1 of 12 features) and abstained in the third; G abstained three times, twice for verbatim documents the bundle lacked (closed by #30: the task table names them and the bundle carries them after the knowledge), once because the QUALIFIED isolation rule read as too onerous across every module and for want of an executable oracle to iterate against. Both arms, in the last draw, asked for iteration against the suite. The story continues with task-0022.02, the tool loop with the scenario's suite as feedback, and the multi-reply arm without feedback is not built; the QUALIFIED wording in harness/policy.md is to say what isolation costs, as part of 0022.02.

task-0022.02 Done 2026-11-02 (knowgov #31, #32): the agent arm ran both arms on D3 to a finish with graded sandboxes and traces; the story's criteria 1, 3 and 4 hold; criterion 2 (the governed arm's consulted assertions through the store port) is task-0022.03.
<!-- SECTION:NOTES:END -->
