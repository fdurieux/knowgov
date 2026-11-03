---
id: TASK-0065
title: 'Pre-load check: a baseline per kind, failing only on regression'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:04:00Z'
updated_date: '2026-11-03T23:40:00Z'
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
- [x] #1 `tools/preload_check.py --baseline FILE` exits 1 only when a file has a finding the baseline does not hold (a new finding, or a finding at a higher severity); a finding already in the baseline is listed and does not fail
- [x] #2 The command never writes the baseline itself; `-o FILE` produces a report that can be committed as one, and the docs say keeping it is the instance owner's decision
- [x] #3 Where the kind's linter has its own ratchet (pumllint), the baseline uses it rather than a second mechanism, or the task records why not
- [x] #4 harness.yml proves it on the example instance: a baseline recorded with one known finding exits 0; a second, new finding exits 1
- [x] #5 The preload report schema covers the baseline comparison; instance/README.md and docs/guide.md §5 describe the flag
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/preload_check.py --baseline FILE: an earlier report of the command (-o), validated against preload-report.schema.json (else exit 2). A finding is held when the baseline has the same (file, rule, message) at the same severity or worse, counted per finding; lines not compared. Held findings listed, state 'held', exit 0; a new finding or a worse severity exits 1. -o naming the baseline refused (2): the command never writes it.
2. pumllint's own ratchet not used: score --baseline ratchets maturity levels, not lint findings, and writes its file when missing; recorded in the docstring and the guide.
3. Schema additive: optional baseline {file, held, new}, counts.held, state 'held', finding.held.
4. instance/ci/preload-check.sh passes KG_PRELOAD_BASELINE (template env); harness.yml proves it on the example instance with real pumllint; tests/test_preload.py with the stand-in (held, moved line, new, worse severity, new file, self-write refused, bad and missing baseline).
5. instance/README.md and docs/guide.md §5.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified: tests 159/159; harness.yml's new step run locally with pumllint 0.33.0 (record exits 1, held 0, a second SEQ001 1, JSON {held 1, new 1} valid, -o onto the baseline 2, baseline digest unchanged). KG_SUBJECT=subjects/jef_data_load: 158/159, the failure test_gate_cli.test_a_later_version_is_asked_for_coherently_or_the_gate_cannot_run is on main without this change (from task-0049, #96), reported to the coordinator.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/preload_check.py takes --baseline FILE, an earlier report of the command that the instance's owner chose to commit: findings it holds (same file, rule and message, same severity or worse; lines may move) are listed as held and pass, and only a new finding or a worse severity exits 1. The command never writes the baseline and refuses -o naming it; a file that is not a preload report cannot be compared (exit 2). pumllint's score --baseline is not used: it ratchets maturity levels, not findings, and writes its file itself. The schema gains an optional baseline block, a held state and count, and a held flag per finding. The CI template passes KG_PRELOAD_BASELINE; harness.yml proves held 0, new 1, baseline unchanged with real pumllint on the example instance. instance/README.md and guide §5 describe it.
<!-- SECTION:FINAL_SUMMARY:END -->
