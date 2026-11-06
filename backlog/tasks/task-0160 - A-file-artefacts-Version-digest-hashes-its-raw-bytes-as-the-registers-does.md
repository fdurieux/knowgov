---
id: TASK-0160
title: A file artefact's Version digest hashes its raw bytes, as the register's does
status: To Do
assignee: []
created_date: '2026-11-06T06:45:00Z'
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
- [ ] #1 The Version digest of a file artefact is the SHA-256 of its raw bytes, in both adapters and across export_turtle/import_turtle
- [ ] #2 A test with a CRLF file artefact: its Version digest equals the raw bytes' digest and register-cites reads it as the same as the tag
- [ ] #3 Before any change, a count of the public subjects' file artefacts whose digest would move; if any recorded leaf would move, the change waits for a record decision
<!-- AC:END -->
