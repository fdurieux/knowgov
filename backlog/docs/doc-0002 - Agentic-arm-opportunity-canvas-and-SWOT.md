---
id: doc-0002
title: 'Agentic arm: opportunity canvas and SWOT'
type: specification
created_date: '2026-11-01T23:25:00Z'
updated_date: '2026-11-02T07:27:00Z'
tags:
  - canvas
  - swot
  - brief
  - arms
---
*2026-11-01. Maintainer register. The brief behind task-0022, written before anything is built: an
opportunity canvas and a SWOT of an agentic, multi-turn arm. The trigger was the maintainer's first
Arms run on the J-F subject (D3, gpt-5.5): both arms abstained in 1 of 1 runs, so the oracle graded
nothing.*

## Verdict

Worth building, as a story in three sized steps, not one feature. It is the one option that makes the
Arms mode match how the J-F record was produced, and the largest build the platform has taken on since
decision 0001. The story stops after its first subtask if the spike says the task exceeds the model on
offer.

## Opportunity canvas

| Element | Reading |
|---|---|
| Problem | The arm is one chat completion: one prompt, one JSON reply, one module (`harness/arms.py` `call()`). On CargoQuote that is the task. On J-F the task is a whole program (the reference rebuild is 716 lines in nine files; J-F's original is about 3,500; a 266,000-character bundle for G, 420,000 characters of documents for B), and on the maintainer's run both arms abstained, so the gate's effect on a realistic build cannot be measured inside the platform. |
| Users | The maintainer, who wants the degradation record reproducible here rather than frozen from an outside tool. Later a client's operator, who runs their own subject through the same loop with their own model (task-0013). |
| How the record did it | The J-F rebuilds were agentic sessions of a coding agent: a pre-registered protocol, hash-pinned inputs, a working directory, the kit's suite to run, about twenty-five minutes of wall time. The harness never ran them; it vendors their output, so the subject's `record_model` is empty. |
| Solution outline | An arm that works in a sandbox directory over several turns: reads the bundle or the documents through tools, writes files, runs the scenario's own suite, iterates, ends with a decision and an assumptions file. The governed arm's tools read the store through the port, so what it consulted is logged per assertion. The oracle, the pristine suite, grades the directory as it grades the reference rebuild today. |
| What stays | The gate, the bundle, the decision vocabulary, the flagged-assumption and resolvable-reference measures (`harness/measures.py`), the oracle, the budget guard, the endpoint as instance configuration (task-0005). |
| What is new | A turn loop with tool calls, a sandbox, a per-run budget, a trace (turns, tool calls, documents or assertions read, cost, wall time), and a subject table saying how the artefact is laid out and how its suite is run (task-0002: nothing in `harness/` names a subject). |
| Value | The J-F arms produce code the oracle can grade; the two subjects then measure the same thing at two sizes; the record's "no arm" becomes "an arm of the same shape as the record's". |
| Cost | Three sized tasks. A run costs model time: the record's rebuilds ran about twenty-five minutes each; the dollar ceiling (`CEILING_USD`) becomes per run, not per session. |

## SWOT

| | |
|---|---|
| **Strengths** | The pieces exist: the store port gives the governed arm a tool surface; the oracle already grades a directory; the budget guard already counts calls and dollars; the subject manifest already holds prompts and the oracle script. The record gives a protocol to copy and a reference to compare against. |
| **Weaknesses** | Largest build since decision 0001. Tool calling differs across OpenAI-compatible endpoints, so "any endpoint" narrows to endpoints with tool support. Runs are long and non-deterministic, so the comparator cannot hold them to a record leaf by leaf. The subject-generic rule means the agent's layout, suite command and tool set are subject data, not code. |
| **Opportunities** | Reproducing the degradation test inside the platform, scenario by scenario, with the planted suite as the agent's feedback and the pristine suite as the oracle, as the record did it. A per-assertion log of what the governed arm consulted, which no outside agent gives. The operator's choice of model or none (task-0013) at the size a client's subject will have. |
| **Threats** | Cost: a few runs can pass the current ceiling; a loop that never converges burns budget without a result. Safety: the arm executes model-written code in the container, in a loop with tool access, so the sandbox has to be real. Comparability: a different agent on a different model is a reference beside the record, never the same experiment. Contamination: the kit has been public since October 2026, which the one-reply arm shares. Scope creep: an agent loop invites endless tuning, and every tuning changes the measure. |

## Shape

1. **task-0022.01, spike, no tools.** Plan turn, one reply per module, assembled into a directory, graded by the oracle. The cheapest way to learn whether abstention is about size or about the task.
2. **task-0022.02, tool loop.** Read, write, run-suite tools over a sandbox, a per-run ceiling, a trace file the page shows, the subject table for layout and suite command.
3. **task-0022.03, governed tools and the page.** The governed arm reads assertions through the port and logs them; the page shows the trace and the consulted set beside the gate.

Each step ends with a scored run on D3, where both arms abstained on 2026-11-01.

## Spike finding, 2026-11-02 (task-0022.01)

One probe of the current one-reply arm on D3 (gpt-5.5, n=1): arm B generated a 664-line module in one reply, graded 2 of 12 features by the oracle; arm G abstained with five questions, all for documents the bundle does not carry verbatim (the packaged TOML files the task says to embed, the parser surface tables of `contracts/cli.md`). So size is not the cause on G: the bundle's content is. The multi-reply shape stays worth testing for B's quality; a verbatim-documents section of the bundle, named by the subject's task table, is the smaller change that answers G, and it is a bundle question before it is an agent question.
