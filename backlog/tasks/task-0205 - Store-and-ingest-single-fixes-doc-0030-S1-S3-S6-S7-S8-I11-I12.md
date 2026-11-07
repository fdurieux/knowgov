---
id: TASK-0205
title: Store and ingest single fixes (doc-0030 S1, S3, S6, S7, S8, I11, I12)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - store
  - load
dependencies: []
priority: medium
type: bug
ordinal: 205000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

S1: an artefact with a mapper and store = false still loads its statements, without a Version. S3: every rdflib publish forces the file to 0644 (store_rdflib.py:265), undoing an operator's chmod 600. S6: the load-memory preflight counts first loads only. S7: a writer that wrote nothing still publishes. S8: invalidated_at means two things. I11: a duplicate short and a duplicated fragment locator are not refused. I12: preload compares a raw-byte digest with a text digest, and a line-1 citation after a BOM is missed. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A store = false artefact's statements are not loaded (or the pair is refused by check_subject), and the counts match the nodes
- [ ] #2 A publish keeps the existing file's mode; the preflight counts stage-2 loads; a writer that wrote nothing publishes nothing, on both adapters; invalidated_at has one meaning
- [ ] #3 check_subject refuses a duplicate short and a duplicated fragment locator, and a document's parse error names the document
- [ ] #4 preload compares raw-byte digests, so an unchanged CRLF document reads checked; citation parsing strips a leading BOM
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
