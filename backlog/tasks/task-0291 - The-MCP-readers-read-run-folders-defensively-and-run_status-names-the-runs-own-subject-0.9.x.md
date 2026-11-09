---
id: TASK-0291
title: >-
  The MCP readers read run folders defensively, and run_status names the run's
  own subject (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T15:37:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 284000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the independent spot check (decision-0032 point 5, task-0256) at main 9861953. Fix-only.

SR-1: one run folder whose `run1_G.json` has `"usage":{"model":5}` makes every source of that scenario unreadable, record included: "could not answer: TypeError: sequence item 0: expected str instance, int found", from `runs_index.sources_for`'s `", ".join(models)`. A run folder whose `deterministic.json` is `[]` makes `scenario_runs` fail (AttributeError).

SR-2: values in a run's deterministic.json pass to structuredContent unchecked, so the answer breaks `scenario-result.schema.json`: `D6_gate.verdict: 5`, `as_of: 20261030` and `gate_keys.k.level: 7` give ints; `stage2.gate_before_reverification.verdict: [..]` gives a list; `D6_gate: [1]` and `gate_keys: {"k":"x"}` give AttributeError.

RS-1: after a minimal run, `run_status {"subject":"cargo_quote"}` returns minimal's run (the page's latest run, as documented), but its `next` names `scenario_runs {"scenario": "S0", "subject": "cargo_quote"}`, another subject's scenario under the asked subject. Minor: the same run reads `elapsed_s` 1 when latest and null from the list.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each run file is read defensively: an unreadable or malformed source is skipped or flagged in the answer, and never fails the scenario or the record's source.
- [ ] #2 Every answer of `scenario_result` and `scenario_runs` validates against its schema on the malformed folders in the description, held by tests.
- [ ] #3 `run_status`'s `next` is built from the run's own subject and says when the latest run is another subject's; `elapsed_s` reads the same both ways.
<!-- AC:END -->
