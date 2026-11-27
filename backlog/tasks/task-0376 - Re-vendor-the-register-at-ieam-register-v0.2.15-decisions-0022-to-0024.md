---
id: TASK-0376
title: Re-vendor the register at ieam-register v0.2.15 (decisions 0022 to 0024)
status: To Do
assignee: []
created_date: '2026-11-27T19:15:00Z'
labels:
  - 0.10.0
  - register
dependencies: []
priority: medium
ordinal: 365000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ieam-register decision 0022 (approved 2026-11-27) says knowgov's connector re-vendors at the tag that carries it. v0.2.15 carries 0022 (a process node points at its function definition; the register id rides on it in sources.toml register_id_attribute), 0023 (inbound references from an agent registry: exports/agent_registry/<date>/, check_inbound, reconcile's references), 0024 (the name check, only for a system whose export_names is concept) and the inventory format pumllint trace reads (ieam-register #41). The maintainer, 2026-11-27: "tag v0.2.15 and re-vendor it". Follows task-0362 (v0.2.14).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 demo/register is re-vendored with tools/vendor_register.py at v0.2.15, SOURCE.md rewritten, every v0.2.14 pin re-pinned by name, the digest test green
- [ ] #2 The vendored checker runs clean (0 errors) and the record does not move: S1-S7 compare identical on rdflib and in the stack job
- [ ] #3 tools/connector.py still writes MANIFEST.toml and RECONCILE.json the vendored reconcile.py reads, with the new agent_registry export folder and export_names field read or ignored without error; register_impact and proposal_impact unchanged on the example instance
- [ ] #4 CHANGELOG Unreleased names the register tag carried
<!-- AC:END -->
