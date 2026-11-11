---
id: TASK-0320
title: >-
  decision-0038 build: attestations, captures and register files in the gate's
  identity; differs on both readers; canonical corpus lines; the review records
  its giver; one key rule on single-key tools; execution bound to the
  implementation and suite
status: Done
assignee:
  - '@claude'
created_date: '2026-11-11T08:27:00Z'
updated_date: '2026-11-11T09:20:00Z'
labels:
  - contracts
  - 0.9.0
dependencies: []
priority: high
ordinal: 313000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0038 (accepted 2026-11-11, "(a) as advised for all six", with the coordinator's three refinements). One narrow contract build before the 0.9.0 cut. Every change is additive or unreleased; the record must not move.

1. N2: gate report v3 gains optional `attestations` (the canonical JSON of [verification], [provenance] and [capture] as the load read them, sha256), `captures` (the answers and reviews the load applied, sha256) and register file digests beside its tag and commit. Each comes from what the load used, not files on disk; equal on both stores; held by check_round_trip and check_mcp_server.
2. N3: a `differs` list (the identity fields that differ, none for unknown) in the CLI report's baseline object and in MCP gate_verdict's baseline, computed in one place; the stderr lines stay.
3. N4: corpus = sha256 over one canonical JSON array [artefact, version, sha256] per loaded Version, sorted; null and "" distinct; tab and newline cannot collide.
4. G1+G2: `capture.py review` records the ruled answer's giver, read from the capture's content (its signed [answered] handle), never from the file name; the load binds a review by it. A review without the field keeps today's fail-closed rule. The refusal message names decision-0038, not "decision pending".
5. N7: three_valued_answer, derived_outputs and key_nodes take `key` under the same KEY_ITEM pattern and raw-or-NFC refusal as `keys`; -32602 with the value as sent.
6. N-b: `[verification] execution` lists the digests of the reference implementation and of the suite that judged it, each digested as a directory artefact is (the load's own part selection, task-0319); a changed implementation or suite voids the execution verification, named by the not-attested finding and by check_subject. The public subjects and the claim probe list theirs.
Also: reviewer A's N1 from the task-0307 re-check (a partly unknown identity object is named as differing): compare only sub-fields known on both sides.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 N2: editing [verification], a capture or review file, or a vendored register file moves its named field; a skipped capture file does not; equal on both stores; tests
- [x] #2 N3: --baseline and MCP gate_verdict report the same differs list; a test holds them equal
- [x] #3 N4: the corpus line is canonical JSON; tab, newline and null/empty cases differ; a test
- [x] #4 G1+G2: with handles X and X-n, X-n's answer can be approved and its dispute settled; the giver comes from the capture's content; a legacy review keeps the fail-closed rule; tests
- [x] #5 N7: the three single-key tools refuse what keys refuses, -32602, the value as sent, on both transports; a test
- [x] #6 N-b: editing the reference implementation or the suite voids its execution verification and is named; the public subjects list their digests; tests
- [x] #7 A-N1: a sub-field unknown on either side is never named as differing; a test
- [x] #8 The record holds (both comparators 0 differing leaves); schemas validate earlier v3 reports; CHANGELOG lines under Contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. N4: store.corpus_digest over canonical JSON lines [artefact, version, sha256], sorted.
2. N3 + A-N1: gate_cli.differs(identity, report) the one function; identity_drift compares an object's sub-fields known on both sides; evaluate() puts baseline.differs on the CLI's and MCP gate_verdict's report; stderr lines kept.
3. N2: load records on agent:harness the digests of what it used: [verification]/[provenance]/[capture] as read (load_scenario), captures applied (load_captures), reviews applied (load_reviews); port write record_inputs, read inputs, both adapters; report attestations and captures; register.files beside tag and commit.
4. G1+G2: review.check reads a captured answer's giver from the capture's content and capture.py review records it; bind binds by it; a ruling without it keeps the fail-closed rule; the message names decision-0038.
5. N7: KEY_ITEM on the single-key tools' key.
6. N-b: [verification] execution lists implementation and suite digests (the load's part selection); the load compares them with the code it records as evidence; a mismatch or a missing list voids execution, named by the gate's attestation finding and by check_subject; public subjects and the claim probe list theirs.
7. Schemas, instance/README, CLAUDE.md, CHANGELOG; tests per AC; checks.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built all seven parts. N2: load records attestations/captures/reviews digests on agent:harness (record_inputs/inputs, both adapters, READS); report attestations, captures, register.files. N3/A-N1: gate_cli.differs one function, baseline.differs on CLI and MCP gate_verdict; _moved compares object sub-fields known on both sides. N4: canonical JSON corpus lines. G1/G2: review.check reads giver from the capture index (the capture's [capture] from) at write time, review_toml writes it, bind binds by it; without it the stem rule stands, message names decision-0038. N7: KEY_ITEM on three_valued_answer, derived_outputs, key_nodes. N-b: Subject.code_parts, load.execution_code voids execution on an unlisted implementation/suite file, gate code_finding, check_subject check_execution_code; cargo_quote, jef_data_load and claim_probe list theirs. Record: 0 differing leaves on both subjects (rdflib) and CargoQuote on Neo4j 5.26; round trips rdflib,rdflib and neo4j,rdflib,neo4j equal.

Proofs (tests/test_decision_0038.py unless named; each fails on ad7ee17): AC1 test_n2_each_input_moves_its_own_field_and_a_skipped_file_moves_none, test_n2_the_inputs_survive_export_and_import_and_are_a_read_of_the_port, check_round_trip (rdflib,rdflib and neo4j,rdflib,neo4j) and check_mcp_server; AC2 test_n3_the_command_and_the_mcp_reader_report_one_differs_list, check_mcp_server differs_held; AC3 test_n4_the_corpus_line_is_canonical_json_so_tab_newline_and_null_never_collide; AC4 test_g1_the_review_records_the_giver_from_the_captures_content_and_binds_by_it, test_g2_a_dispute_raised_by_x_n_is_settled_by_a_review, test_g1_a_ruling_without_its_giver_keeps_the_fail_closed_rule_and_names_decision_0038, check_act_binding x_n_cases (rdflib and Neo4j); AC5 test_n7_the_single_key_tools_refuse_what_keys_refuses_with_the_value_as_sent; AC6 test_n_b_the_load_voids_execution_when_the_implementation_or_suite_changed_and_the_gate_names_it, test_n_b_a_changed_implementation_or_suite_is_named_by_check_subject, test_n_b_the_public_subjects_and_the_claim_probe_list_their_implementation_and_suite; AC7 test_a_n1_a_sub_field_unknown_on_either_side_is_never_named; AC8 test_n3_the_schema_admits_differs_and_earlier_v3_reports_still_validate, compare_deterministic 0 differing leaves (cargo_quote rdflib and Neo4j 5.26, jef_data_load rdflib), CHANGELOG Contract changes. Suites: bare 1065/1133 passed, 68 skipped, 0 failed; pins 0 failed after fixing test_gate_identity. check_subject (3), check_attestation_binding, check_act_binding, check_gate_after_change, check_claim_probe, complexity --check: hold.

Coordinator's review of #473: register.files now covers what a load reads (register_impact.loaded_files: every file the register's own load_register opens, recorded as it opens them, plus the issued-handles list types.toml names), proved by test_n2_register_files_cover_what_the_load_reads_and_nothing_else; check_mcp_server single_key_refused calls three_valued_answer, derived_outputs and key_nodes with an astral key over stdio (both eras) and HTTP (handshake): -32602 naming the value as sent. Whole suites on the final head: pins 1132/1134 passed, 2 skipped, 0 failed; bare 1066/1134, 68 skipped, 0 failed; check_register_change, check_mcp_server (S1,S2,S6) and check_round_trip hold.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0038 built: the gate report names attestations, captures and register.files from what the load used (stored on agent:harness, both adapters); baseline.differs computed once for the CLI and MCP gate_verdict, sub-fields unknown on either side never named; canonical JSON corpus lines; a review ruling on a captured answer records its giver from the capture's content and binds by it, so X-n's answers can be approved and their disputes settled, a ruling without it keeping the stem rule; three_valued_answer, derived_outputs and key_nodes take key under KEY_ITEM; [verification] execution lists implementation and suite digests, a change voiding execution, named by the gate and check_subject. All additive under schema v3; the record does not move. Adopter impact (CHANGELOG): an instance must list its implementation and suite digests or its execution verifications lapse.
<!-- SECTION:FINAL_SUMMARY:END -->
