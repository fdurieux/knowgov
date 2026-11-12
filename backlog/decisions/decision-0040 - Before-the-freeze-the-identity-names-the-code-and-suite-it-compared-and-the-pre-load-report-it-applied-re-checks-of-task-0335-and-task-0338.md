---
id: decision-0040
title: >-
  Before the freeze: the identity names the code and suite it compared and the
  pre-load report it applied (re-checks of task-0335 and task-0338)
date: '2026-11-12T08:04:00Z'
status: accepted
---
## Context

decision-0038 N2 and decision-0039 §3.2 promise that the gate report "names every input that decided it", so that `--baseline` names the identity field that moved whenever the verdict, the findings or the exit move. Group A's re-checks found two inputs that still decide the outcome outside every identity field.

- R3 (re-check of task-0338, at 9ecb1e6, and again at fbf886f): the bytes of the `[reference] code`, `[oracle] script` and `[oracle] suite` files. The load compares each file's raw digest with `[verification] execution`'s `implementation` and `suite` (`load.execution_code`, decision-0038 N-b, task-0338, task-0340). An edit to the suite's expectations moves the verdict from PROCEED to BLOCKED, yet `baseline.differs` is `[]`. `attestations` names the declared digests, not the files' current bytes, and `configuration` (task-0335) names the manifests and maps, not the code.
- Q1 (re-check of task-0335, at fbf886f): the pre-load report the load applied (`harness/preload.py`, `KG_PRELOAD_REPORT` or `<instance>/preload-report.json`). On the example instance, with the report the findings go from 0 to 6 and `--fail-on minor` exits 1; without it they stay at 0 and it exits 0. Every identity field is equal in both runs. The verdict does not move ("form, not knowledge"), but the findings and the exit do.

Both are contract-bearing: the identity is part of the gate-report contract, so closing them adds fields. Under decision-0032 they are put to the maintainer before the cut.

## Options and choice

- (a) Two additive identity fields, recorded at the load through decision-0038 N2's `record_inputs` and `inputs` on both adapters, compared whole by `gate_cli.differs`, and carried by the CLI report, MCP `gate_verdict` and the trace report's gate block:
  - `code`: the raw sha256 of each `[reference] code`, `[oracle] script` and `[oracle] suite` file the load compared, by path, in the load's part selection (`subject.code_files`);
  - `preload`: the sha256 of the pre-load report the load applied, with its path, or null with `why` when none was applied.
- (b) Fold both into `configuration`: one field, but it would mix configuration files with code bytes and a report that is not configuration, so a reader of `differs` could not tell which kind of input moved.
- (c) Name both as known limits of 0.9.0: no build, but the freeze would encode an identity that misses inputs it promises to name.

**Chosen: (a)**, by the maintainer on 2026-11-12: "R3 + Q1: add digests for the code and suite bytes and the pre-load report to the identity". It makes decision-0038's promise true for an execution verification and for the pre-load verdict, through the mechanism task-0335 proved. It is additive, with no version change.

## Opportunity canvas

- Problem: a replay can change the outcome while the identity says nothing changed: a code or suite edit flips the verdict, and a present or absent pre-load report changes the findings and the exit.
- Users: an auditor comparing two gate reports with `--baseline`; an adopter's CI holding a baseline; knowgov's comparators.
- Solution: two additive digest fields, `code` and `preload`, recorded at the load and named by `differs`.
- Value: `baseline.differs` names every input that moved the verdict, the findings or the exit, so a reviewer sees why a replay differs without diffing the trees.
- Cost: one narrow build on task-0335's mechanism (the load, both adapters, `differs`, the two schemas, the trace gate block, the round-trip and MCP checks).
- Risk: the comparators learn two more fields; a false "differs" on a byte edit, never a false "same".

## Fit/gap

- Fit:
  - The load already computes every code digest (`Subject.code_parts`, `subject.code_files`) and reads the pre-load report's digest (`harness/preload.py`).
  - `record_inputs` and `inputs` already carry `attestations`, `captures` and `configuration` on both adapters; `differs` compares a field whole, and a missing or null field reads as unknown (A-N1).
  - The gate-report and trace-report schemas already take additive identity fields without a version change (task-0307, task-0320, task-0335).
- Gap: none in mechanism. The record holds no `code` or `preload`, so `baseline=record` reads them as unknown, as it does `configuration`.

## SWOT

- Strengths: closes the last two inputs the re-checks found outside the identity; reuses a proven mechanism; additive.
- Weaknesses: two more identity fields for every reader; a whitespace or comment edit to a code file moves `code`.
- Opportunities: an adopter's CI can hold a baseline across a code change and see which file moved; a later 0.9.x can make the stderr line name the moved file once for every map field.
- Threats: a reader that compares identities by a fixed field list must learn the new fields; the build lands the night before the cut, so it gets the same fresh re-check as every other.

## Advice

Choose (a). It makes decision-0038's promise, which decision-0039 §3.2 restated, true, and it shuts the two cases the re-checks reproduced. It costs one build on the mechanism task-0335 proved. (b) blurs what moved, and (c) freezes a known blind spot into 0.9.0.

## Decision

Accepted 2026-11-12 by the maintainer: (a). The build is task-0341, re-checked by a fresh reviewer before the cut.
