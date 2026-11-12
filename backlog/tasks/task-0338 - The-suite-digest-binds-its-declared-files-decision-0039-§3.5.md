---
id: TASK-0338
title: The suite digest binds its declared files (decision-0039 §3.5)
status: Done
assignee: []
created_date: '2026-11-11T22:53:00Z'
updated_date: '2026-11-12T01:44:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 330000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.5 (a), doc-0038 §3.5, group A's N-2 on task-0330. Subject.code_parts digests the suite as [oracle] script's bytes only. CargoQuote's expectations live in vendor/tools/acceptance/cargo_quote_suite.py, which the script imports and no digest covers. Build: an optional [oracle] suite list of paths in subject.toml, each digested into the suite digest in sorted path order. When missing, the suite digest is the script alone, as now. The subject format reader (harness/subject.py, formats) and subjects/README document it. load.execution_code, check_subject and the route use it. CargoQuote's subject.toml lists its acceptance module, and its [verification] execution suite digests are re-pinned. If that would move the vendored record, keep CargoQuote on the script alone, say so, and prove (a) on the example instance. A's repro: editing the expectations alone now moves the suite digest, and the gate names it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With [oracle] suite listing the acceptance module, editing it moves the suite digest and the gate's attestation finding names it; without the field, behaviour is unchanged; tests
- [x] #2 subjects/README and the guide document the field; the record holds (or the fallback is stated and proven on the instance); check_subject reads it
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #497 (https://github.com/fdurieux/knowgov/pull/497), merged as 9ecb1e6 on a whole green matrix with stack. [oracle] suite, an optional list of files or directories, joins each file's raw digest to the script's in [verification] execution's suite, in sorted path order; missing, the suite is the script alone. One reading (harness/subject.py code_files) for Subject.code_parts and check_subject; load.execution_code names each unlisted or absent suite file; check_subject and MCP subject_check refuse malformed, escaping or missing paths; attestation_paths.py refuses an assistant write that adds, changes or removes [oracle] suite while [verification] stays. CargoQuote lists its acceptance module and its suite is re-pinned; no vendored byte moved. Re-checked by group A at 9ecb1e6 on rdflib and Neo4j: FIXED on every point (editing the expectations alone blocks and names the file; expectations edited to a wrong implementation never stay PROCEED until both new digests are listed, task-0330's known limit; no field, as before; directory, missing, escape, ordering, duplicates, the hook; the record 0 differ on both subjects). Residues: R1 a file removed from a listed directory goes unseen, R2 the load reads an absolute suite path, R4 re-pointing [oracle] script or [reference] code is unguarded; all fail open, pulled before the cut as task-0340. R3 (the identity does not move when code or suite bytes change) is contract content, put to the maintainer.
<!-- SECTION:FINAL_SUMMARY:END -->
