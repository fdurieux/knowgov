---
id: TASK-0160
title: A file artefact's Version digest hashes its raw bytes, as the register's does
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T06:45:00Z'
updated_date: '2026-11-06T13:15:00Z'
labels:
  - store
  - register
dependencies:
  - TASK-0098
priority: low
ordinal: 165000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0098. A file artefact's Version sha256 is taken over sha256(read_text) (harness/load.py, through Subject.artefact_text), and read_text normalises CRLF to LF, so a CRLF file's Version digest differs from a register citation's digest, which demo/app/register_project.py takes over the file's raw bytes; register-cites then reads 'differs' for an unchanged file. task-0098 fixed the same for the files of a directory artefact (part_sha256); this is the file artefact's own digest.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The Version digest of a file artefact is the SHA-256 of its raw bytes, in both adapters and across export_turtle/import_turtle
- [x] #2 A test with a CRLF file artefact: its Version digest equals the raw bytes' digest and register-cites reads it as the same as the tag
- [x] #3 Before any change, a count of the public subjects' file artefacts whose digest would move; if any recorded leaf would move, the change waits for a record decision
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AC #3 first: count the public subjects' file artefacts whose digest would move (raw bytes vs read_text), and check whether any recorded leaf or comparator field holds a Version digest; stop and report if one would move.
2. harness/subject.py: Subject.version_digest(key, text) returns (sha256, bytes). A file artefact whose kit text is the file as read (unplanted) gets the SHA-256 and length of its raw bytes on disk. A planted text, a directory bundle, or an artefact with no bytes keeps its text's UTF-8 digest, as before. This mirrors part_digests (task-0098).
3. harness/load.py: upsert_artefact_version takes version_digest's pair. The adapters store the value they are given, so both carry it, and export_turtle/import_turtle carry the property.
4. Tests: a CRLF copy of tools/fixtures/subject_probe. Its Version digest equals the raw bytes' digest and register_project's citation digest (what register-cites compares), and a planted text keeps the text digest. The rdflib adapter keeps it through export_turtle/import_turtle. The load uses version_digest.
5. CHANGELOG under Unreleased › Contract changes; the 0.8.0 known limit is left as released.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence.
- AC #3, first. The public subjects' file artefacts whose digest would move: 0 of 11 (CargoQuote 10 files plus 1 with no bytes; J-F 1 file and 4 directory artefacts). Every file is LF; git ls-files --eol shows no crlf or mixed file in the repository. No recorded leaf holds a Version digest: sha256 appears in the record only in the constraint text. After the change, the deterministic record on rdflib against the comparator gives 0 differing leaves over the 7 CargoQuote scenarios. No record decision is needed.
- AC #1. harness/subject.py Subject.version_digest(key, text): for a file artefact whose kit text is the file as read, the SHA-256 and length of its raw bytes; otherwise, for a planted text, a directory bundle or no file, its text's UTF-8 digest, as before (the twin of part_digests, task-0098). harness/load.py passes it to upsert_artefact_version, the one caller. Both adapters store the value they are given; the rdflib adapter keeps sha256 and bytes through export_turtle/import_turtle (test). The Neo4j path is the same port write, and the stack's round trip compares it.
- AC #2. tests/test_version_digest.py: a CRLF copy of tools/fixtures/subject_probe. Its Version digest equals sha256(raw) and register_project._digest, the value register-cites compares v.sha256 with ('same as tag'). It differs from the text's digest. A planted text keeps its own digest.
- tests/test_security.py's digest-and-size test is updated to the new call. It still holds that the port write takes a 64-hex digest and an int size and never the text.
- Suites, all 0 failed: stdlib 611/633 (22 skipped); J-F 610/633 (23 skipped); pins with KG_TEST_REQUIRE=rdflib,node 632/633 (1 skipped).
- CHANGELOG: Unreleased › Contract changes. The released 0.8.0 known limit is left as released.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A file artefact's Version digest is now the SHA-256 of its raw bytes, as the register's digest of a cited file is, so register-cites reads an unchanged CRLF file as 'same as tag' rather than 'differs'. Subject.version_digest supplies the digest and size to the load's one upsert_artefact_version call. Planted texts and directory bundles keep their text digests; a directory's files already had raw digests (task-0098). Before the change: 0 of the public subjects' 11 file artefacts would move, and no record leaf holds a Version digest; after it, the deterministic record compares identical (0 differing leaves over 7 scenarios). The new tests cover CRLF, planted text, the public subjects' LF files, the load's call and the rdflib Turtle round trip. It is a contract change (the digest), recorded under Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
