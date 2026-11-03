---
id: TASK-0050
title: 'code_map.toml: code paths to register applications, in the instance layout'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T23:39:00Z'
labels:
  - instance
  - traceability
milestone: m-7
dependencies:
  - TASK-0045
priority: medium
type: feature
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 6: nothing maps a code path to the register application or module it implements, so a code change cannot reach the knowledge. An instance file maps path globs to APP ids, checked by tools/check_instance.py. It may later yield to a register implemented_by link, which would be the register's decision.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The instance layout documents code_map.toml (globs → APP id); the example instance carries one for CargoQuote's reference code
- [x] #2 check_instance.py refuses an unknown APP id or an overlapping glob and lists unmapped code paths
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. code_map.toml, optional, at the instance root: [code] roots (dirs relative to the instance) and include globs; [[map]] rows glob -> app (APP id), note.
2. check_instance.check reads it: an APP id not in register/applications is an error; two rows matching one file, or one glob's text matched by another's, is an overlap error; a code file no row matches is listed UNMAPPED; a row matching nothing is listed UNMATCHED. Own glob translation (** across segments) so 3.12 runs it.
3. example_instance.build writes one: CargoQuote's reference_impl.py -> APP-0001.
4. instance/README.md and docs/guide.md document it; note that a register implemented_by link may replace it (the register's decision).
5. tests/test_instance.py: example maps clean; unknown id, overlap, unmapped, unmatched, malformed.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
code_map.toml is optional and additive (decision-0003's instance contract: no existing field changes; CHANGELOG left to the release PR). Ids are checked against the instance's register/applications (application and module rows, both APP-). Overlap is refused statically (one glob's text matched by the other's pattern) and on the files (two rows matching one file). Own glob translation so CPython 3.12 (harness.yml) runs it. The example maps the subject's [reference] code, left in place, to APP-0001: QuoteAPI, TariffEngine and ScreeningService are classes in that one file. A register implemented_by link may later replace the file; that is ieam-register's decision, noted in instance/README.md only. Verified: python tests/run_tests.py 161/161; example_instance prints the map, layout holds.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Adds code_map.toml to the instance layout: [code] root and include say what code is; [[map]] rows map path globs to register APP ids. tools/check_instance.py refuses an unknown id, a malformed file, a missing root, and overlapping rows (exit 1), and lists UNMAPPED code files and UNMATCHED rows as findings. tools/example_instance.py writes one for CargoQuote's reference_impl.py -> APP-0001. Documented in instance/README.md ('Mapping code to the register') and docs/guide.md section 4. Four tests in tests/test_instance.py. Feeds TASK-0051 (not started). Risk: the static overlap test is conservative on pattern text; two globs that share files only through character classes are not a case the syntax allows.
<!-- SECTION:FINAL_SUMMARY:END -->
