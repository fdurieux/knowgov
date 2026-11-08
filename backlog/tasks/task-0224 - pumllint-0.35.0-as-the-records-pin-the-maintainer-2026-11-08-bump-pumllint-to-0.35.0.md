---
id: TASK-0224
title: >-
  pumllint 0.35.0 as the record's pin (the maintainer, 2026-11-08: bump pumllint
  to 0.35.0)
status: In Progress
assignee: []
created_date: '2026-11-08T13:08:00Z'
updated_date: '2026-11-08T14:02:00Z'
labels:
  - pins
  - record
  - image
  - pumllint
dependencies: []
priority: high
type: task
ordinal: 224000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08: "bump pumllint to 0.35.0". task-0217 (decision-0018 point 1, step 4) needs pumllint trace --features, which first appears in pumllint 0.35.0 (PyPI); the record pins 0.33.0, the library the sequence-diagram mapper imports. Put to the maintainer with its four parts. Canvas: one pumllint across the record, the image and the lint step, so adopters get the feature trace from the image. Fit/gap: G9-4 (the 0.9.0 image runs every feature) fits only with the bump; the record must be proven equal under 0.35.0. SWOT: S one version everywhere; W a rebuild and a full re-proof; O the record on the current pumllint; T a parse difference moves the record, which stops this task and returns to the maintainer. Advice taken: bump first, then build task-0217 on the pin directly, with no side install (option b dropped unless this task finds the record moves). Places that name 0.33.0 on main at 3b931bb: demo/Dockerfile:22, .github/workflows/harness.yml:62 and :139, tests/test_demo.py:259, tests/test_rdflib_split.py:19, CLAUDE.md:81, docs/security.md:207 (and the linters row :209 if it names pumllint), instance/ci/gitlab/knowgov.gitlab-ci.yml:20, instance/ci/preload-check.yml:27. pumllint imports nothing from knowgov and is installed from PyPI; nothing in pumllint changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every place that names pumllint 0.33.0 as a pin names 0.35.0, and tests/test_demo.py holds the new pin
- [ ] #2 The image is rebuilt with 0.35.0 and the stack job runs on it
- [x] #3 The scored record (S1 to S7), the deterministic run and the comparator stay equal on rdflib and Neo4j; the sequence-diagram mapper yields the same statements under 0.35.0 as under 0.33.0, shown by a diff of its yield
- [x] #4 pumllint 0.35.0's trace --features runs from the installed library (a smoke step), for task-0217
- [x] #5 CHANGELOG.md carries the pin change under Unreleased, and CLAUDE.md's pins line is updated
- [ ] #6 If the record or the mapper's yield moves, the task stops and the before and after go to the maintainer before any merge
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Move every pin of pumllint 0.33.0 to 0.35.0 (the places the description lists, plus demo/requirements.txt and two test fixtures' tool_version), grep again.
2. Prove the record equal: the comparator on S1-S7 and J-F on rdflib and on a local Neo4j 5.26; the yield of the two pumllint-backed mappers (sequence, plantuml_realises) and the parser output they read, diffed under 0.33.0 and 0.35.0; the pre-load check's pumllint findings on the example instance and pumllint's findings on every .puml of both subjects, diffed.
3. A CI smoke step: pumllint trace --features from the installed library on the J-F kit.
4. CHANGELOG under Unreleased > Changes; CLAUDE.md's pins line.
5. Checks: run_tests with the pins and without yaml, round trips --chain on both subjects, check_preload_linters, check_mcp_server. Stop and report if anything moves.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08, base main d49ae21. Pins moved: demo/Dockerfile, demo/requirements.txt, .github/workflows/harness.yml (both jobs), tests/test_demo.py (the pin assertion and a fixture's tool_version), tests/test_preload_load.py (fixture), tests/test_rdflib_split.py, CLAUDE.md, docs/security.md (the image's packages row and the pre-load linters row), instance/ci/gitlab/knowgov.gitlab-ci.yml, instance/ci/preload-check.yml. A grep for 0.33.0 outside backlog/ and CHANGELOG.md's released sections finds nothing.

Proof, each under CPython 3.12 venvs with the record's pins, one with pumllint 0.33.0 and one with 0.35.0:
- Comparator, 0.35.0: CargoQuote S1-S7 on rdflib, 0 differing leaves over 7 scenarios (D1 skipped across store kinds); on Neo4j 5.26.0 community (a local tarball, Java 21), 0 over 7, D1 compared. J-F C and D1-D5 on rdflib, 0 over 6; on Neo4j, 0 over 6.
- The mappers' yield (every scenario's extract_all, fragments, entities and assertions, every key and value): CargoQuote 12,634 leaves, J-F 69,135 leaves, 0 differ between 0.33.0 and 0.35.0. The pumllint-backed bags: CargoQuote's sequence mapper 145 statements and 75 fragments over 7 scenarios; J-F's plantuml_realises 1,074 statements and 96 fragments over 6 scenarios (8 diagrams); equal.
- The parser's output the mappers read (diagram_type, participants, messages, blocks, directives, activity_nodes) on every pumllint-mapped document: no value changed or removed; 0.35.0 adds one field, participants' declared_line (42 leaves on CargoQuote, 150 on J-F), which no mapper reads (extract_sequence reads line, kind; extract_plantuml_realises reads diagram_type, directives, participants' names, activity_nodes).
- Pre-load: tools/preload_check.py on the example instance, 0.33.0 and 0.35.0: exit 0 both, 2 pumllint files, 0 findings each, equal but for the version. pumllint -f json on all 12 .puml of both subjects: 5 findings each (quote_flow_bad.puml GEN001, GEN002, SEQ003, SEQ004; data_model.puml GEN009), identical.
- pumllint trace --features on the J-F kit (pumllint.toml, requirements.json, features/, uml/): 163 requirements, all covered by the 8 diagrams and verified by the 12 features (130 scenarios); the CI smoke step in the rdflib-readers job asserts uncovered 0, unverified 0.
- tests/run_tests.py: with the pins and KG_TEST_REQUIRE=rdflib,node,openai 765/766, 1 skipped, 0 failed; without pyyaml (system python 3.13) 729/766, 37 skipped, 0 failed. check_round_trip --chain rdflib,rdflib on CargoQuote exit 0. check_preload_linters exit 0 (Node 22 here; CI uses 24).
<!-- SECTION:NOTES:END -->
