---
id: TASK-0240
title: >-
  Re-vendor the register at ieam-register v0.2.13 (decisions 0019 and 0020)
  before 0.9.0
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T00:03:00Z'
updated_date: '2026-11-09T00:03:00Z'
labels:
  - register
  - vendor
dependencies: []
ordinal: 231000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08: "yes, re-vendor the register at v0.2.13 before 0.9.0". knowgov vendored v0.2.11 (7f1680c). v0.2.13 (7980708) adds the register's decision 0019 (four eyes: a session that drafted a change is its author) and decision 0020 (coverage rule C4). Re-vendor with tools/vendor_register.py, re-pin what pins the tag, commit or digests, and say what C4 changes in knowgov without building C4 support.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 demo/register/ and SOURCE.md are rewritten by tools/vendor_register.py from a clean checkout at v0.2.13; no vendored file edited by hand
- [x] #2 Every pin of v0.2.11, 7f1680c or the vendored digests outside CHANGELOG and backlog is re-pinned by name
- [x] #3 Whether knowgov surfaces C4 is stated: the register view and proposal_impact read C1 to C3 by name; no C4 support built
- [x] #4 The record does not move: the comparator on S1 to S7 and J-F, check_round_trip --chain, check_register_change, check_proposal_branch, check_mcp_server and the register-view tests hold
- [x] #5 CHANGELOG carries the line under Unreleased > Changes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-vendored from a clean clone of fdurieux/ieam-register at tag v0.2.13 (7980708): 106 files, 2 added (decisions 0019, 0020), 2 changed (metamodel/lifecycle.toml's four_eyes comment; tools/check_register.py's C4). The pinned checker date stays 2026-11-01. Re-pins: .github/workflows/demo.yml (two tag asserts, lines 211-212); tests/test_register_view.py 34, 232, 242, 266 (tag and commit); tests/test_register_change.py 35, 163; tests/test_vendor_register.py 130-136 (tag row, the note's commit, subject and dates, v0.2.11 joining the earlier copies); tools/register_fixture.py TAG v0.2.13+fixture. Left as history: tests/test_connector.py:134 and tools/connector.py:23 (decision 0017 at v0.2.10), instance/README.md:777 (v0.2.6). C4: demo/app/register_view.py's coverage and coverage_lines, and harness/proposal_impact.py's _cov and coverage, name C1 to C3, so C4 has no coverage line and no new gap; placement runs no coverage. register_view's findings and error count list every checker finding, so a C4 error in an instance register would show there; the vendored register is C4-clean (5/5).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The vendored register moves from ieam-register v0.2.11 to v0.2.13 (7980708), by tools/vendor_register.py, adding the register's decisions 0019 (four eyes) and 0020 (C4). Every pin of the old tag and commit is re-pinned by name. knowgov reads coverage C1 to C3 by name; C4 errors would show only in the register view's generic findings, and the vendored register has none. The record is unchanged: the comparator on S1-S7 and J-F, check_round_trip --chain (rdflib, and Neo4j to rdflib and back), check_register_change, check_proposal_branch and check_mcp_server hold.
<!-- SECTION:FINAL_SUMMARY:END -->
