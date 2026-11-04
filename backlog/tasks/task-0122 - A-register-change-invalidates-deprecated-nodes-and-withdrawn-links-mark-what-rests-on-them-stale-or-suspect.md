---
id: TASK-0122
title: >-
  A register change invalidates: deprecated nodes and withdrawn links mark what
  rests on them stale or suspect
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T18:33:00Z'
updated_date: '2026-11-04T21:04:00Z'
labels:
  - register
  - gate
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 122000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the doc-0011 fit-gap (2026-11-04): a register change re-projects but invalidates nothing, so the gate never sees it (doc-0011 §4, 'Change propagation'). A source-document change reaches the gate today (S6); a register change does not. register_impact (task-0111) reports what retiring a node would touch, read-only; nothing records it when it happens. At a re-vendor (or an instance's register update), compare the register with the previous vendored tag; for every node that became deprecated or retired and every link withdrawn, mark the statements resting on it stale (reason: the register's decision record) and the derived outputs that used them suspect; surface them as gate findings the way a source change does. 'Resting on' follows the map rows plus the register's walk under ieam-register decision 0016 (descent below a withdrawn node, start never counted, the walk named). Depends on 0016 being approved and tagged (v0.2.9).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A fixture register change (CAP-0001 deprecated with its children moved, one link withdrawn) marks the statements on the affected keys stale with the decision as reason, and the S1 derived output suspect; the gate reports them as findings and exits 1
- [x] #2 A register update with no state change invalidates nothing; the record and the comparator are unchanged
- [x] #3 Both adapters agree; the Turtle round trip carries the new staleness; the CHANGELOG names it under Unreleased
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
PR 1 (#204, merged 1f14be0): vendor ieam-register v0.2.9 (decision 0016); the page and Cypher rows mark a to_start edge. PR 2: harness/register_change.py diff(previous, current) -> withdrawn nodes and links with their decision record; resting() lands them on the map rows plus the register's dependants walk on the previous register (node: with children, start never counted; link: rows naming both ends and rows landed only through it); store port invalidate_keys in both adapters; gate_cli --register-previous registers the scenario's record output as derived then invalidates; report register_change (additive schema); check_round_trip --register-previous; tools/register_fixture.py + tools/check_register_change.py in harness.yml and the stack job.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR 1 #204 merged (1f14be0): 19 dependants walks lose their start, as 0016's table says; the lands table and edge counts are unchanged.

PR 2: fixture (CAP-0001 deprecated by decision 0099, children moved to CAP-0006, REL-06001 withdrawn) on S1: 32 keys, 81 statements stale, derived:S1:G:run1 suspect, exit 1, Neo4j 5.26 and rdflib equal; the round trip holds rdflib->rdflib and neo4j->rdflib->neo4j. An update with no state change gives a report equal to the gate without the flag. The record and the comparator are unchanged (CQ 7, J-F 6). tests 374/374 on both subjects.

Maintainer's choice (2026-11-04, via the coordinator, option b): a descendant that the new register re-parented away from a withdrawn node, in any state, is skipped along with its subtree; it was moved, not withdrawn. A descendant still under the node is descended as before (register_change.descent). Fixture: CAP-0001 lands nothing (all four children moved); REL-06001 lands the 8 DT-V keys, 15 statements on S1, the same on Neo4j and rdflib; exit 1; derived:S1:G:run1 suspect. Before: 32 keys, 81 statements.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A register update now invalidates what rested on it. gate_cli --register-previous DIR compares the previous register with KG_REGISTER (harness/register_change.py). Deprecated or retired nodes and withdrawn links land on the subject's keys through the map rows plus the register's dependants walk on the previous register: descent by parent for a node, the start never counted (0016). The live statements on those keys are invalidated through a new port write, invalidate_keys (both adapters), with the register's decision record as the reason, and the record's output for the scenario turns suspect. The gate reports stale and suspect_derived findings and exits 1. The report has an additive register_change section. Proven on a fixture built from the vendored register, which is never edited: both adapters agree, and the Turtle round trip carries the staleness. Risk: landing a deprecated domain stales most of its keys (32 of 36); a narrower reading would be the maintainer's call.
<!-- SECTION:FINAL_SUMMARY:END -->
