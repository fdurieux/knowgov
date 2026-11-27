---
id: TASK-0362
title: >-
  Re-vendor the register at the ieam-register tag that carries decision 0021's
  person field
status: Done
assignee:
  - '@claude'
created_date: '2026-11-16T19:16:00Z'
updated_date: '2026-11-27T18:05:14Z'
labels:
  - 0.10.0
  - register
dependencies: []
priority: medium
ordinal: 352000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0047 point 7: who_knows resolves a handle to its holder through the register's person field (ieam-register decision 0021). knowgov vendors the register at a tag; the tag that carries the person field and its check is published by the owner after ieam-register's build merges.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 demo/register is re-vendored with tools/vendor_register.py at that tag, SOURCE.md rewritten, the digest test green
- [x] #2 who_knows on the example instance shows holder null with why for the synthetic handles, which carry no person
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-vendored from a clean clone of fdurieux/ieam-register at tag v0.2.14 (be01dfc, the owner's Release of 2026-11-27): 107 files, 1 added (decisions/0021), 3 changed (metamodel/types.toml's [elicited] person and its comment; people/handles.toml's header; tools/check_register.py's check_handles). The pinned checker date stays 2026-11-01; the vendored checker reads 57 nodes, 65 links, 0 errors, 10 warnings there. Re-pins by name: .github/workflows/demo.yml (two tag asserts); tests/test_register_view.py (tag four times, commit be01dfc twice); tests/test_register_change.py (tag, and the commit in the schema probe); tests/test_vendor_register.py (tag row, the note's commit, subject and dates: commit 2026-11-16, copied 2026-11-27; v0.2.13 joining the earlier copies); tools/register_fixture.py TAG v0.2.14+fixture; instance/README.md's 'the tag it vendors' row. Left as history or fixture values: the 'C1 to C4 at v0.2.13' docstrings (still true), the synthetic NOW dicts in the identity tests, test_dates' input. AC #2: who_knows on tools/fixtures/knowledge_probe at v0.2.14 reports register v0.2.14/be01dfc and, for employee-1 and employee-2, holder null with holder_why naming decision 0021; check_mcp_server's knowledge tools hold the 27 answers equal to the probe's expected reports. Record: compare_deterministic on S1-S7 (rdflib) 0 differing leaves; check_mcp_server --scenarios S1,S2,S6, check_register_change --stores rdflib and check_proposal_branch hold. Locally 4 register-view Cypher-guide tests fail on main as on this branch (this container, not the change); CI is the judge.

Correction: with the record's pins installed (rdflib 7.6.0, pyshacl 0.40.2, pumllint 0.35.0) the suite reads 1387/1389 passed, 2 skipped, 0 failed; the four register-view failures noted above came from rdflib being absent from this container, on main as on the branch.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The vendored register moves from ieam-register v0.2.13 to v0.2.14 (be01dfc) by tools/vendor_register.py, carrying the register's decision 0021: a handle is one person in one role, its holder recorded as the optional person field (a directory identifier) or in the directory, checked by the vendored checker. Every pin of the old tag and commit is re-pinned by name. who_knows already read person; the synthetic handles carry none, so holders stay null with holder_why. The record does not move: S1-S7 compare identical, and the MCP, register-change and proposal-branch checks hold.
<!-- SECTION:FINAL_SUMMARY:END -->
