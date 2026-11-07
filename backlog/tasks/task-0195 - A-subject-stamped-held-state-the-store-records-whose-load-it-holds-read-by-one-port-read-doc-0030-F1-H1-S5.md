---
id: TASK-0195
title: >-
  A subject-stamped held state: the store records whose load it holds, read by
  one port read (doc-0030 F1, H1, S5)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-07T09:26:00Z'
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
- [x] #1 The load records its subject; with two subjects declaring one scenario id and A's load held, every store-backed reader tool for B, gate_cli --no-load --subject B and the page for B refuse, on both adapters
- [x] #2 One port read held() returns the subject, the scenario, the current version per artefact (from the CURRENT edges, not activity order) and loaded_at; a stage-2 tag sorting before v1 still reads as current
- [x] #3 The five split(":")[2] parsers are gone, and the round trip carries the subject
- [x] #4 CHANGELOG.md has the line under Unreleased's contract heading
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-07 evidence (local: Neo4j 5.26.0 Community tarball and file-backed rdflib, disposable; no model call; the clock pinned; rebased onto task-0193's F7, cae9648).
- AC #1. tools/check_held_subject.py --disposable reports 'every check holds' on rdflib and on Neo4j. Two subjects (cargo_quote and a twin copy) share S1, and cargo_quote's S1 is published:
  - for twin, gate_cli --no-load exits 2 ('the store holds S1 of subject cargo_quote, not of twin');
  - all 8 store-backed MCP tools for twin refuse, naming cargo_quote (gate_verdict, three_valued_answer, evidence_bundle, register_impact, proposal_impact, held_keys, derived_outputs, document_statements), and store_status reports scenario None and held_by_other_subject S1;
  - the page for twin reports loaded_subject cargo_quote and serves 0 gaps (match False);
  - for cargo_quote, gate_cli and gate_verdict answer (PROCEED) and the page serves its 35 gaps.
  The check runs in harness.yml (rdflib-readers) and demo.yml (the stack, Neo4j).
- AC #2. held() is a port read on both adapters, in store.READS and the MCP view's READS. store.held_from gives {subject, scenario, version, versions, loaded_at}, with versions from the CURRENT edges and HAS_VERSION counts. tests/test_held_subject.py holds S5: stage-2 tags a2, v2 and z9, tied on 'at' with v1, each read as current.
- AC #3. The five split(':')[2] parsers and held_version's [3] are gone (tests/test_held_subject.py scans harness, demo/app and tools). The one remaining parse is store.held_from's, for a store loaded before task-0195. The subject travels on the activity's properties through export_turtle/import_turtle. check_round_trip's answers() now includes held(), so F7's differences() compares it by construction (tests/test_round_trip.py asserts a lost subject is reported). The round trips: CQ neo4j,rdflib,neo4j and rdflib,rdflib, and J-F neo4j,rdflib,neo4j --expect-parts on C and D3, every answer survives.
- AC #4. CHANGELOG Unreleased › Contract changes.
- AC #5. Deterministic runs against the comparator: CQ on rdflib and on Neo4j, 0 differing leaves over 7 scenarios; J-F on rdflib, 0 over 6. check_mcp_server holds every check on rdflib and on Neo4j. check_snapshots holds every check on both.
- A store loaded before task-0195 has no subject, and I took the coordinator's suggestion: harness/held.py reads it as unknown and refuses every subject, except the instance's only subject when it declares the held scenario.
- Suites, all 0 failed: stdlib 673/705, J-F 673/705, pins with KG_TEST_REQUIRE=rdflib,node 704/705.
  - Tests changed: the stubs (test_mcp_server's Stub and test_store_generations' _Moving) gain held(), and the two tests that hand-built an old, subject-less extraction activity (test_impact_mid_run, test_mcp_runs) now record a subject as a load does.
  - test_rdflib_split gains ADDED for the new step. test_round_trip's part list gains held.
- test_http_limits' test_limit_07 failed only in suite runs made beside other heavy local load (it did so on task-0176's branch too). It passed alone and in every quiet full run.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The store now records whose load it holds. The load stamps the subject and the scenario on the extraction activity, whose id is unchanged because the record's run files name it. One port read, held(), returns the subject, the scenario, each artefact's current version from the CURRENT edges (S5) and loaded_at, on both adapters. harness/held.py is the one rule every reader applies: gate_cli --no-load, the MCP reader's store-backed tools, proposal_impact, the page and the snapshot check. The activity-id parsers are gone. A store loaded before this reads as unknown and fails closed, except for an instance's only subject. tools/check_held_subject.py proves on rdflib and Neo4j that a twin subject sharing S1 is refused everywhere while the owner answers, and both workflows run it. The round trip carries and compares held(). The record, the deterministic runs, check_mcp_server and the snapshot checks are unchanged. A contract change for 0.9.0 under decision-0016.
<!-- SECTION:FINAL_SUMMARY:END -->
