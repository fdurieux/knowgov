---
id: TASK-0019
title: 'Port pumllint #261 and keep the page''s interface identical to pumllint''s'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T17:09:00Z'
updated_date: '2026-11-01T17:11:00Z'
labels:
  - platform
  - parity
milestone: m-0
dependencies: []
priority: high
type: task
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Before pumllint's copy of the demo is retired, knowgov's must serve exactly what pumllint's does (the maintainer's condition, 2026-11-01). Two things were missing. (1) pumllint #261, merged after the vendoring here: tools/vendor_legible_model.py and its test, the shared describe(paths) in vendor_register.py, and the demo README's 'Keeping the demo current' section. (2) Wording the subject refactor had changed: counts written as digits where the page wrote words (ten mappers, eleven scenarios), the glossary's three subject-sized entries, the footprint's 'decision table', the oracle note the page shows in every scenario, and the saved queries' order. All restored from the subject's data so another subject still gets its own.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Both demos served side by side answer every endpoint identically, apart from absolute paths and fields knowgov adds (store name, model endpoint, stage-2 label)
- [x] #2 A headless browser renders both pages without console errors and with the same report text for every scenario and the register
- [x] #3 tools/vendor_legible_model.py regenerates demo/model/SOURCE.md with the model's and the layout tables' digests, and a test holds it
- [x] #4 The demo README's 'Keeping the demo current' section names every copy and its command for this repository
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Method: pumllint's demo at main (3924aa5) and knowgov's served side by side on one Neo4j, every endpoint fetched from both and compared leaf by leaf (27 endpoints: health, scenarios, cypher, register, impact walks, reference panels, the seven reports plus S6's other sources, the seven footprints, gaps, runs). First pass: 1906 differing leaves, all explained: counts written as digits where the page wrote words, the oracle note shown in every scenario, the glossary's three subject-sized entries, the footprint's 'decision table', the saved queries' order. Restored from the subject's data (number words in views, [page] oracle in subject.toml, stage2 label and short_label, the glossary formatted from the subject's counts with GLOSSARY.md as pumllint wrote it, the subject's queries listed after the first generic one). Second pass: 43 differing leaves, all absolute paths of the two checkouts or fields knowgov adds (store name, model endpoint, stage-2 label). Browser: Playwright over both pages, no console errors, identical report text for all seven scenarios and the register; on knowgov a deterministic run through the page identical to the record and the projection. #261 ported: vendor_legible_model.py with the layout tables' digest in the note, describe(paths) shared, the test, the README's 'Keeping the demo current' adapted to this repository (the subject vendoring and --record-for added). Not exercised in either demo: the Arms call itself, which needs a model key; its code path changed in task-0005 (client built from the endpoint settings) and is covered by unit tests on the settings only. The duplicate PR #8 was closed in favour of #9 (the suggested task's own implementation, merged while this ran) and the branch rebased on it.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov's demo serves what pumllint's serves: 27 endpoints compared leaf by leaf differ only in absolute paths and in fields knowgov adds; a headless browser renders identical report text for every scenario and the register on both, with no console errors. The wording the subject refactor had changed is restored from the subject's data. pumllint #261 is ported (the Legible-model vendoring tool, the shared describe, the chores section). The one path not exercised in either demo is the Arms call, which needs a key.
<!-- SECTION:FINAL_SUMMARY:END -->
