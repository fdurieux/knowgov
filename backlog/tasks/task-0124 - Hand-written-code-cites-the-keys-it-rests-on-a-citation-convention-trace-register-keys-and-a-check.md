---
id: TASK-0124
title: >-
  Hand-written code cites the keys it rests on: a citation convention, trace
  register --keys and a check
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T19:05:00Z'
updated_date: '2026-11-04T19:37:00Z'
labels:
  - trace
  - gate
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 124000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0015 (2026-11-04, maintainer's go). Hand-written code maps to an APP through code_map.toml but to no statements, so a source or register change never reaches it (doc-0011 §3, 'Reports only'). A citation convention lets it join the stale/suspect chain: a header line naming the keys a file rests on, and knowgov-trace register --keys K1,K2 to register a hand-written file as a derived output resting on those keys' current statements. A check, optional per instance, requires a citation in files under governed APPs. Code semantics stays out: the tests and the oracle judge correctness.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 knowgov-trace register --keys registers a hand-written file; after S6's change it reads suspect on the cited invalidated keys, as a generated file does
- [x] #2 A header citation is parsed in Python and one other language; an unknown key is an error, a missing citation is a finding only where the instance turns the check on
- [x] #3 The trace report schema change is additive; the CHANGELOG names it; the record is unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/citation.py: the header convention (# knowgov-keys: in Python, // in Java; first 30 lines; comma-separated; malformed refused).
2. code_map.toml [citations] require/apps, read and checked in harness/code_map.py (check_instance gets it).
3. trace.py register --keys K1,K2 / --cited: current (not invalidated) statements on the keys through the port's assertions_on_key; unknown key (not in the subject's register map or any task) exit 2; the ledger entry and report row carry keys.
4. trace.py check: unknown_key, malformed_citation (blocker), uncited (major, only where required), uncitable (info); suspect message names the cited keys.
5. Schema additive (registered.keys); CHANGELOG under both Unreleased headings; instance README; CLAUDE.md line.
6. tests/test_citation.py; tools/check_trace_walkthrough.py after S6's change.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Why Java as the second language: most enterprise service code consuming a register is Java, and its // line comment is Kotlin's, C#'s, Go's, JS's and TS's, so each is one more row in citation.COMMENT, not another parser.
Unknown key: a key neither the subject's register map nor any task names. In register it is exit 2 (CannotRun); in check, a file whose header cites one is a blocker finding (unknown_key), since a PR's file is the change's fault, not the tool's.
'Current statements' on a key: every status but invalidated (proposed, validated, verified, approved, disputed), read through the port's assertions_on_key, so both adapters serve it.
Evidence: tests/test_citation.py (5 tests); python tests/run_tests.py 371/371 and with KG_SUBJECT=subjects/jef_data_load 371/371; KG_STORE=rdflib tools/check_trace_walkthrough.py passes (hand/tariff_rules.py --keys P2|surcharge suspect on A:dt:P2|surcharge@v1 after S6 stage 2, hand/Screening.java --cited shipper_id|present clean, an unknown key exit 2); rdflib run.py --deterministic + compare_deterministic: 0 differing leaves over 7 scenarios.
<!-- SECTION:NOTES:END -->
