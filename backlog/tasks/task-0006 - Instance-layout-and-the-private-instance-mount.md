---
id: TASK-0006
title: Instance layout and the private-instance mount
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-02T23:11:00Z'
labels:
  - instance
milestone: m-2
dependencies:
  - TASK-0002
priority: medium
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A client's instance is private and never reaches this repository. It is a git repository with a declared layout: the register's trees (taxonomies, relationships, decisions, exceptions, glossary, exports), artefacts/<kind>/ for authored artefacts keyed by the rows of the artefact table on fdurieux.github.io, exports/<system>/<date>/ with manifests, and record/ for its results and digests. The platform vendors a public subject at a tag and mounts a private one through the compose override, the route docs/ieam-register-demo-integration.md already proposed for a live register checkout. One stack per instance; the page stays read-only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The instance layout is documented, with the artefact table's rows and which have a mapper
- [x] #2 A directory in that layout mounted through the compose override runs replay and deterministic without any file written back
- [x] #3 An artefact kind with no mapper is reported as absent, never silently skipped
- [x] #4 ieam-register's public test case, plus the CargoQuote artefacts, is a valid instance
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Layout as built since task-0006.01 and 0032.02, not the description's register-at-root: <instance>/register/ (an ieam-register checkout, its exports/<system>/<date>/ inside it), artefacts/<kind>/, subjects/<id>/ (manifests naming ../../artefacts/... paths), record/<subject>/. Documented in instance/README.md (adopter register).
2. instance/kinds.toml: one row per artefact row of the site's table (fdurieux.github.io, read 2026-11-02), the folder name, and the mappers that read it; a test holds every harness mapper to exactly one kind.
3. tools/check_instance.py <dir>: the layout, every subject loads, every artefact path exists, an unknown kind folder is an error, a file of a kind with no mapper or a store artefact with no mapper is reported absent, a file no subject names is listed; exit 0/1/2, --json.
4. load_scenario reports a store artefact with no mapper as unmapped (absent), never skipped silently; the page's ingest panel lists it.
5. run.py SHA256SUMS labels a path outside the repository (an instance subject) and digests the artefacts it read.
6. tools/example_instance.py <out>: the vendored register plus CargoQuote's artefacts in artefacts/<kind>/, its subject and record; the checker passes on it.
7. Proof of no write-back: harness.yml runs S1-S7 from the example instance on rdflib, compares to the record and holds a digest of the instance tree; the stack job remounts it read-only through docker-compose.instance.yml and runs replay and deterministic.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built: instance/README.md and instance/kinds.toml (20 kinds from the site's table read 2026-11-02, every harness mapper in exactly one, test-held); tools/check_instance.py (exit 0/1/2, --json; ABSENT for a stored document no mapper reads or a file of a kind no mapper reads, UNREAD for a file no subject names); tools/example_instance.py (vendored register + CargoQuote's ten documents by kind + subject + record); load_scenario returns unmapped when a stored document has no mapper and the ingest panel lists it; run.py SHA256SUMS labels instance paths <subject>:<relpath> and digests the artefacts it read. Layout deviates from the description's register-at-root: register/ as task-0006.01 and 0032.02 already mount it.
Verified locally (rdflib, no Docker daemon here): S1-S7 from the example instance 0 differing leaves against its record/ copy, instance tree digest unchanged; the page with KG_SUBJECTS/KG_REGISTER at the instance lists one subject, replays S6 (PROCEED, 4 invalidated), register 56/65, a deterministic S1 through /api/run compares identical, digest unchanged. Tests 112/112, also with KG_SUBJECT=J-F. CI: harness.yml runs the instance and the unmapped case; the stack job remounts the instance read-only (a touch is refused) and repeats replay and deterministic.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Merged in #67. instance/README.md (adopter register) and instance/kinds.toml document the layout (register/, artefacts/<kind>/, subjects/<id>/, record/<subject>/) with the site's 20 artefact rows and the mappers that read each (every mapper in exactly one, test-held). tools/check_instance.py checks a folder (exit 0/1/2): ABSENT for a document no mapper reads, UNREAD for one no subject names. The load reports a stored document with no mapper as unmapped and the ingest panel lists it. tools/example_instance.py builds ieam-register's public case plus the CargoQuote artefacts; it checks clean. Evidence, CI on #67: harness.yml ran S1-S7 from the example instance on rdflib with 0 differing leaves and the tree digest unchanged; the stack job remounted it read-only (a touch refused), replayed S6, read the register, ran S1 deterministically through /api/run, compared identical and found the digest unchanged. Layout deviates from the description's register-at-root: register/ as task-0006.01 and 0032.02 mount it.
<!-- SECTION:FINAL_SUMMARY:END -->
