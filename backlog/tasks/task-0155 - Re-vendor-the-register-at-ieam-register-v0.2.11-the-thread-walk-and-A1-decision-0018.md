---
id: TASK-0155
title: >-
  Re-vendor the register at ieam-register v0.2.11: the thread walk and A1
  (decision 0018)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T23:27:00Z'
updated_date: '2026-11-05T23:29:00Z'
labels:
  - register
milestone: m-8
dependencies: []
priority: medium
type: task
ordinal: 162000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On the maintainer's approval of ieam-register decision 0018 (2026-11-05) and publication of v0.2.11 (7f1680c). The tag adds a third named walk to the vendored impact.py (--walk thread: from a journey step to its process, the process's capability, applications and information, and the applications' information) and a warning-level rule A1 to check_register.py (a product's requires links against what its journeys' steps reach). Re-vendor with tools/vendor_register.py from a clean checkout at the tag; move the tag pins v0.2.10 -> v0.2.11 in tests, demo.yml and the register fixture. The register view counts the checker's warnings: 7 -> 10 with A1's three, listed as findings and never as a coverage line (A1 is not a coverage rule, decision 0018). Nothing in harness/ reads the thread walk; task-0152's slice map will.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 vendor_register.py at v0.2.11 from a clean checkout; SOURCE.md and every digest test pass
- [x] #2 Tag pins v0.2.10 -> v0.2.11 in tests, demo.yml and tools/register_fixture.py; the register view's warnings 10, A1's three listed, coverage lines C1-C3 only
- [x] #3 CHANGELOG line under Unreleased; the record and the comparator unchanged on both subjects (CI)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-vendored with tools/vendor_register.py from a clean checkout at v0.2.11 (7f1680c): 104 files; decision 0018 added, check_register.py and impact.py changed; pinned date 2026-11-01 unchanged. Tag pins moved in tests/test_vendor_register.py (note, earlier copies gain v0.2.10 4149e06 2026-11-05), tests/test_register_view.py, tests/test_register_change.py, .github/workflows/demo.yml and tools/register_fixture.py. The register view's summary reads 10 warnings (7 + A1's PRD-0002, PRD-0004, PRD-0005, check 'A1'); its coverage stays C1-C3. Local: tests/run_tests.py with KG_TEST_REQUIRE=rdflib 493/494, 1 skipped (hook-live); stdlib 490/494, 4 skipped; CargoQuote deterministic on rdflib against the record: 0 differing leaves over 7 scenarios. J-F's record and the stack job are CI's.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov reads ieam-register v0.2.11: the vendored impact.py carries --walk thread and the checker A1 (decision 0018). The register view lists A1's three warnings beside the seven before; nothing in harness/ reads the thread walk yet (task-0152). Records unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
