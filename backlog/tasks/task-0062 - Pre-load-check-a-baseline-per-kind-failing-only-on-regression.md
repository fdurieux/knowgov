---
id: TASK-0062
title: 'Pre-load check: a baseline per kind, failing only on regression'
status: To Do
assignee: []
created_date: '2026-11-03T23:04:00Z'
labels:
  - instance
  - gate
milestone: m-6
dependencies:
  - TASK-0045
references:
  - backlog/docs/doc-0008
priority: medium
type: feature
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tools/preload_check.py (task-0045) fails on every finding at or above the threshold. An organisation adopting it over an existing corpus of documents would see its first pull request red on findings nobody introduced, and would either raise the threshold or switch the check off. The gate contract (fdurieux.github.io) asks for a baseline and a ratchet: record today once, fail only on regression, never update the baseline from inside the gate. harness/gate_cli.py already has `--baseline record|FILE` on that model; the pre-load check has none. doc-0008 §5 proposed it: "a baseline per kind, the linter's own where it has one (pumllint's ratchet, vacuum's score, buf breaking)".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `tools/preload_check.py --baseline FILE` exits 1 only when a file has a finding the baseline does not hold (a new finding, or a finding at a higher severity); a finding already in the baseline is listed and does not fail
- [ ] #2 The command never writes the baseline itself; `-o FILE` produces a report that can be committed as one, and the docs say keeping it is the instance owner's decision
- [ ] #3 Where the kind's linter has its own ratchet (pumllint), the baseline uses it rather than a second mechanism, or the task records why not
- [ ] #4 harness.yml proves it on the example instance: a baseline recorded with one known finding exits 0; a second, new finding exits 1
- [ ] #5 The preload report schema covers the baseline comparison; instance/README.md and docs/guide.md §5 describe the flag
<!-- AC:END -->
