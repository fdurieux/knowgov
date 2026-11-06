---
id: TASK-0098
title: Per-file digests hash each part's raw bytes
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T08:46:00Z'
updated_date: '2026-11-06T07:03:00Z'
labels:
  - store
milestone: m-6
dependencies:
  - TASK-0094
priority: low
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0094: part_sha256 hashes the part as bundled, and the bundler adds a newline to a file that lacks one, so a raw file and its digest could disagree; every J-F file matches the register today.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 part digests hash the file's raw bytes in both adapters and across export/import_turtle
- [x] #2 register-cites still reads 14 same, 0 differ on J-F C; a test covers a file without a final newline
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. subject.py: bundle_files (the bundle's own file walk, shared) and Subject.raw_part_digests(key), sha256 of each file's bytes on disk. 2. load.py part_digests(path, text, subject): a part equal to its file as bundled takes the raw digest; a planted part keeps its text's. The adapters store strings unchanged, so both and the Turtle round trip carry it as before. 3. Tests: a file without a final newline and one with CRLF keep their raw digests; a planted part its text's; every J-F file raw == bundled. 4. Proofs: both comparators 0 differ; check_round_trip --expect-parts on J-F, rdflib,rdflib and neo4j,rdflib,neo4j; register-cites on J-F C on Neo4j; the suites both ways.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06, on main at 7f13676 (S2 merged). The digest is computed in harness/load.py only; store_neo4j.py and store_rdflib.py (as S2 left them) store and return part_sha256 strings, unchanged here. Besides the added newline, the bundle reads with universal newlines, so a CRLF file differed too; both are covered. No committed digest moves: every file of a directory artefact in cargo_quote (none), jef_data_load (47) and minimal (none) has raw == bundled. Evidence: demo/tools/compare_deterministic.py 0 differing leaves for cargo_quote (7 scenarios) and jef_data_load (6); KG_SUBJECT=subjects/jef_data_load tools/check_round_trip.py --expect-parts, rdflib,rdflib and neo4j,rdflib,neo4j (Neo4j 5.26 tarball, Java 21): every scenario equal, 47 file digests each; register-cites on J-F C on Neo4j: 15 documents, 13 files of a directory artefact, 14 same as tag, 0 differ; tests/test_part_digests.py test_a_file_without_a_final_newline_keeps_the_digest_of_its_raw_bytes and test_every_committed_jef_file_matches_its_raw_digest_and_its_bundled_one; run_tests.py stdlib 561/578 and KG_SUBJECT=jef 560/578, pinned 577/578 and 576/578, 0 failed. A file artefact's own digest (sha256 of read_text) is outside this task and unchanged.

2026-11-06, #282's first CI run: the tests job (stdlib, no yaml) failed test_a_file_without_a_final_newline_keeps_the_digest_of_its_raw_bytes with ImportError: the test imported harness/load.py, which imports extract (yaml). Reproduced locally with yaml blocked. Fixed by moving the rule to Subject.part_digests(key, text) in harness/subject.py (stdlib), which load.py calls; the test calls it on its temporary subject. Re-proved: both comparators 0 differ; J-F round trip rdflib,rdflib --expect-parts equal; run_tests.py in a bare venv (no yaml) 561/578, pinned 577/578 and with KG_SUBJECT=jef 576/578, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A directory artefact's part_sha256 now hashes each file's raw bytes on disk (Subject.raw_part_digests over the bundle's own file walk), so a file without a final newline or with CRLF line ends keeps the digest the register computes; a part a scenario's plant changed keeps its text's digest. The adapters and the Turtle round trip carry the strings unchanged. No recorded digest moves (every committed file already matches), both comparators show 0 differ, register-cites reads 14 same, 0 differ on J-F C, and check_round_trip --expect-parts holds on rdflib and Neo4j. CHANGELOG Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
