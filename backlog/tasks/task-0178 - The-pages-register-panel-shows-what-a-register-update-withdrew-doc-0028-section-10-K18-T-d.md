---
id: TASK-0178
title: >-
  The page's register panel shows what a register update withdrew (doc-0028
  section 10 K18, T-d)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T13:27:00Z'
updated_date: '2026-11-06T14:59:00Z'
labels:
  - register
  - page
dependencies: []
priority: low
type: task
ordinal: 179000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gate reads a register change only when given the previous register (--register-previous, task-0122). The page's register panel never reads one, so a reviewer on the page cannot see what an update withdrew, deprecated or retired, nor the keys it staled (0.7.0 Known limits; no module under demo/app reads a previous register). When the instance names a previous register, the panel lists those changes as harness/register_change.py computes them. With none, it says the panel shows the current register only. Drafted by the v1.0 session (task-0173), minted under doc-0029.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With a previous register configured, the panel lists the withdrawn, deprecated and retired nodes and links, and the keys they stale, equal to the gate's register-change block for the same pair, which a test compares
- [x] #2 With none configured, the panel says so in one line; nothing else changes
- [x] #3 The setting is read once at start, read-only, and a missing or unreadable path is reported on the page, not raised
- [x] #4 The Known limit's page half is removed with its CHANGELOG line
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/register_change.py block(change, landed): the gate's block less its writes; gate_cli uses it.
2. demo/app/register_view.py: KG_REGISTER_PREVIOUS read once at import; register_change() calls diff, resting, block; errors reported; build() carries register_change with one controlled sentence.
3. index.html registerChange() in the Register view: one line when none, the error, or two tables.
4. tools/check_register_change.py compares the page with the gate's report per store, both pairs, and a missing path.
5. tests in test_register_view; README, instance overlay env, CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented as planned. The page's block and the gate's come from one function (register_change.block), and tools/check_register_change.py compares the page's register_change() output field by field with the gate's JSON report on each store it runs (rdflib in harness.yml, neo4j and rdflib in demo.yml). Local: KG_STORE=rdflib check_register_change.py all hold, page changed 1 node, 1 link, 8 keys as the gate's, same pair empty as the gate's, missing path reported. python tests/run_tests.py 632/656, 0 failed; with the pins (rdflib required) 654/656, 0 failed. The register projection and the impact panel are unchanged. demo/docker-compose.instance.yml passes KG_REGISTER_PREVIOUS through (empty by default).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page's Register view shows what a register update withdrew, when KG_REGISTER_PREVIOUS names the register as it was before it: the deprecated or retired nodes, the withdrawn links, each with its reason, and the subject's keys resting on them, with owner and cause. The view uses harness/register_change.py's diff and resting through a new block(), which gate_cli's --register-previous block now uses too. tools/check_register_change.py holds the page equal to the gate's report on each store. The setting is read once at start and the page writes to neither register. Without it, one line says the view shows the current register only. A missing or non-comparing path is shown on the page, not raised. /api/register carries it as register_change. Docs: demo README, the instance overlay, CHANGELOG (lifts the page half of 0.8.0's known limit). Tests: test_register_view (equality with register_change, nothing else changes, errors, the panel drawn in node).
<!-- SECTION:FINAL_SUMMARY:END -->
