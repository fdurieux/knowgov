---
id: TASK-0221
title: An attestation bound to the Versions it attests (decision-0019)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T15:35:00Z'
labels:
  - attestation
  - contract
  - load
  - gate
dependencies: []
references:
  - >-
    backlog/decisions/decision-0019 -
    An-attestation-is-bound-to-the-versions-it-attests-decision-0009-option-c-in-0.9.0.md
priority: high
type: feature
ordinal: 221000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0019 (the maintainer, 2026-11-08: Build it in 0.9; decision-0009 option c). [verification] authored and approval list the Version digest of each artefact they attest (raw-byte sha256, task-0160; part digests for a directory, task-0094). An unlisted Version is not attested: its authored statements read proposed and nothing is approved by construction, as the pre-load verdict reads unchecked unless its digest matches (task-0064); the gate names each unattested Version behind its keys with its owner's route (capture.routing). Read rule: a declaration with no digest list attests per load as decision-0009 (a), listed at info as not bound, and tools/check_subject.py notes it naming decision-0019. The public subjects' digest lists are the maintainer's act: a second pull request, held for the maintainer's approval, never merged on green alone, with S6's measured effect stated. A contract change (the subject format, the gate report), for 0.9.0 (doc-0028 G9-13).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A declaration's digest list is read by the load: a listed Version is attested as today, an unlisted one reads proposed with nothing approved by construction, on both stores
- [x] #2 The gate names each unattested Version behind its keys with its owner and route; a declaration without a digest list reads per load and is listed at info as not bound
- [x] #3 tools/check_subject.py checks the list (each digest an artefact Version of the subject) and notes a declaration without one, naming decision-0019
- [x] #4 A probe shows an edited, unlisted Version reading proposed on rdflib and Neo4j, and failing on the old code
- [x] #5 CHANGELOG.md carries the line under Unreleased's contract heading, with the read rule
- [x] #6 The scored record (S1 to S7), the deterministic run and the comparator stay equal
- [x] #7 A second pull request lists cargo_quote's and jef_data_load's attested Versions with S6's measured effect, held for the maintainer's approval
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
load.attested_artefacts reads [verification] authored and approval versions (raw-byte Version digests; a directory's part digests); verify_authored and approve_verified take the attested artefacts on both adapters (None under the read rule); record_attestation keeps the reading per declaration. The gate's attestation finding: info for a declaration with no list, major for each unattested Version behind the keys, owner and route by capture.routing. check_subject: a listed digest that is no Version of the subject is an error, no list a note naming decision-0019. tools/check_attestation_binding.py. Then a held PR listing the public subjects' Versions, with S6 and every scenario measured.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Severity: an unattested Version behind the task's keys is major (its authored statements read proposed and nothing in it is approved by construction, so the keys behind it fall below verified, and the attester or the keys' owner has to act); a declaration without versions is info. The read rule writes nothing to the store (a declaration without versions is read from the manifest by gate.attestation_behind), and the record's D6_gate leaves the attestation entry out (run.gate_summary), so the record S1-S7 and J-F is unchanged. A test's verification of an unattested Version still counts: the probe's edited table reads verified, not proposed, on its execution-verified statements; its authored statements read proposed. AC 7: the held pull request, claude/task-0221-public-digests.

AC 7, the maintainer's approval, 2026-11-08 (relayed by the coordinator, ~13:0x UTC): "list the planted texts too on #355". #355 lists, for cargo_quote and jef_data_load, every artefact Version the scenarios load: the documents as vendored at pumllint v0.35.0 (be737dd, 2026-11-02) and every planted text, stage 1 and stage 2 (cargo_quote 23 digests, jef_data_load 89, a directory's by its files). The at dates and the [provenance] attester are unchanged: the listing records what the maintainer has approved and does not re-date the attestation. Measured: the comparator reads S1-S7 and J-F identical. To keep the census equal, an attestation's reading is kept on the attester's Agent node, not a node of its own (in #354).

Stage 2's reading (the coordinator's answer to the DECIDE, 2026-11-08: option (a)), decision-0019's text, quoted: "An unlisted Version is not attested: its authored statements read proposed, and nothing in it is approved by construction". It covers the unchanged statements of a changed, unlisted Version. So when stage 2 re-reads a subject whose bound declarations do not list a Version it now loads, load.load_verifications withdraws the by-construction acts (ver:review and appr: of that Version's statements, changed or not) through the new port write withdraw_construction on both adapters, then re-runs r_corroborate and r_unverified; a test's verification still counts. tools/check_stage2_reload.py passes on both stores without setting attestation aside. CI's subject-check step admits exactly the read rule's note (grep -v on '(decision-0019)'), failing on any other NOTE, WARNING or ERROR; #355, whose lists make the note disappear, restores the strict form.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An attestation is bound to the Versions it attests (decision-0019). [verification] authored and approval list in versions the digest of each artefact Version they attest (raw-byte SHA-256, task-0160; a directory's file digests, task-0094); an unlisted Version's authored statements read proposed and nothing in it is approved by construction, on both stores. The gate's attestation finding names each unattested Version behind the keys (major) with the owner's route from capture.routing, and a declaration without a list at info (the read rule). check_subject refuses a digest of no Version and notes an unbound declaration, naming decision-0019. tools/check_attestation_binding.py fails 6 checks on the old code and holds on rdflib and Neo4j. On the maintainer's approval of 2026-11-08 (planted texts listed), cargo_quote and jef_data_load list every Version their scenarios load, as vendored at pumllint v0.35.0 and as planted, with their at dates unchanged; the scored record S1-S7 and J-F reads identical.

Merged: #354 (608cf7d, ACs 1 to 6: the binding, the gate's attestation finding, check_subject, the probe, stage 2's withdraw_construction under decision-0019's text, the read rule and the CHANGELOG line) and #355 (5c4e922, AC 7: the public subjects' lists, planted texts included, on the maintainer's approval of 2026-11-08; the strict subject check restored; check_lint_gaps lists its planted Version through example_instance.attest, the one check whose measurement the lists touched). The record S1-S7 and J-F compares identical on main.
<!-- SECTION:FINAL_SUMMARY:END -->
