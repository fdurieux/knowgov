---
id: TASK-0338
title: The suite digest binds its declared files (decision-0039 §3.5)
status: To Do
assignee: []
created_date: '2026-11-11T22:53:00Z'
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
- [ ] #1 With [oracle] suite listing the acceptance module, editing it moves the suite digest and the gate's attestation finding names it; without the field, behaviour is unchanged; tests
- [ ] #2 subjects/README and the guide document the field; the record holds (or the fallback is stated and proven on the instance); check_subject reads it
<!-- AC:END -->
