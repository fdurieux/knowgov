---
id: TASK-0376
title: Re-vendor the register at ieam-register v0.2.15 (decisions 0022 to 0024)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-27T19:15:00Z'
updated_date: '2026-11-27T20:15:47Z'
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
- [x] #1 demo/register is re-vendored with tools/vendor_register.py at v0.2.15, SOURCE.md rewritten, every v0.2.14 pin re-pinned by name, the digest test green
- [x] #2 The vendored checker runs clean (0 errors) and the record does not move: S1-S7 compare identical on rdflib and in the stack job
- [x] #3 tools/connector.py still writes MANIFEST.toml and RECONCILE.json the vendored reconcile.py reads, with the new agent_registry export folder and export_names field read or ignored without error; register_impact and proposal_impact unchanged on the example instance
- [x] #4 CHANGELOG Unreleased names the register tag carried
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Re-vendored at v0.2.15 (756be61) by tools/vendor_register.py, 113 files; every v0.2.14 pin re-pinned by name; the register view reads two inbound warnings (12), 0 errors, pinned date 2026-11-27; demo glossary gains 'inbound reference'. Suite 1396/1398, 0 failed; S1-S7 identical on rdflib; register_impact and proposal_impact equal to v0.2.14's on the example instance; seam_check.py and inventory.py stay outside the path set. knowgov #602; the stack job in CI.
<!-- SECTION:FINAL_SUMMARY:END -->
