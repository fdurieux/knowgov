---
id: TASK-0195
title: >-
  A subject-stamped held state: the store records whose load it holds, read by
  one port read (doc-0030 F1, H1, S5)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-07T08:35:00Z'
labels:
  - review
  - store
  - contract
dependencies:
  - TASK-0194
priority: high
type: feature
ordinal: 195000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

H1 (high, three reviewers): the extraction activity is `act:extract:<scenario>:<version>` with no subject, and five readers parse it alike (gate_cli.py:389, mcp_server.py:489, proposal_impact.py:820, demo/app/server.py:428 and 463). Two subjects sharing a scenario id answer each other's gates, breaking decision-0013 A1 and known limit U1's refusal. S5: the held version comes from the tags' lexical order when a stage-1 and a stage-2 load tie on `at`. The fix records the subject at load and replaces the parsers with one port read. A contract change (the activity or a meta node, store_status), so under decision-0016 it gathers for 0.9.0; doc-0028 G9-11.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The load records its subject; with two subjects declaring one scenario id and A's load held, every store-backed reader tool for B, gate_cli --no-load --subject B and the page for B refuse, on both adapters
- [ ] #2 One port read held() returns the subject, the scenario, the current version per artefact (from the CURRENT edges, not activity order) and loaded_at; a stage-2 tag sorting before v1 still reads as current
- [ ] #3 The five split(":")[2] parsers are gone, and the round trip carries the subject
- [ ] #4 CHANGELOG.md has the line under Unreleased's contract heading
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. The load records its subject. create_activity takes keyword-only subject and scenario, on the port and both adapters. load_scenario passes SUBJECT.id and the scenario on the extraction activity. Its id is unchanged, because the record's run files name it. Export and import carry the properties.
2. One port read, held(), in store.READS and the MCP view's READS. Both adapters read the extraction activities and each artefact's CURRENT version with its HAS_VERSION count. store.held_from returns {subject, scenario, version, versions, loaded_at}. version is the current tag of an artefact loaded more than once (stage 2), else the one tag, never activity order (S5). The one parse of an activity id is held_from's, for a store loaded before the subject was recorded.
3. harness/held.py, the rule every reader applies: owner, scenario_for, foreign and refusal. An absent subject reads as unknown and fails closed, except for the instance's only subject when it declares the held scenario (the coordinator's suggestion).
4. Replace the readers: gate_cli --no-load and held_version; mcp_server _held_any, _held, _foreign, _check_scenario, _held_detail and list_subjects; proposal_impact.with_levels; the page's store_status and store_gaps; check_snapshots' snapshot.
5. tools/check_held_subject.py --disposable runs on both adapters. Two subjects share S1, and A's load is held: held() and its Turtle round trip; B's gate_cli --no-load exits 2; every store-backed tool for B refuses; the page for B serves no gaps; A answers. It runs in harness.yml (rdflib-readers) and demo.yml (the stack).
6. Stdlib tests (tests/test_held_subject.py) and the stubs updated. CHANGELOG under Unreleased › Contract changes. The record, the deterministic run, the comparator, the round trips, check_mcp_server and the snapshot checks run on both stores.
<!-- SECTION:PLAN:END -->
