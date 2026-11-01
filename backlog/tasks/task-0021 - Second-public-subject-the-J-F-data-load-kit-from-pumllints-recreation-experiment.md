---
id: TASK-0021
title: >-
  Second public subject: the J-F data-load kit from pumllint's recreation
  experiment
status: To Do
assignee: []
created_date: '2026-11-01T19:43:00Z'
updated_date: '2026-11-01T19:47:00Z'
labels:
  - subject
milestone: m-3
dependencies:
  - TASK-0002
type: feature
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A platform proven on one subject is not proven (task-0008). pumllint's recreation experiment (docs/recreate-experiment.md, recreate_experiment/) already holds a second subject with everything the harness needs: a hash-manifested kit (163 EARS requirements in requirements.json, 14 prose contracts, 6 DMN tables, 8 PlantUML diagrams, 130 Gherkin scenarios tagged with the requirement ids they verify, recorded fixtures), a public reference implementation (the codex rebuild of 2026-10-24, 258/258 on the kit's suite; J-F's original code is private and is never vendored), and five planted-defect arms from the degradation test of 2026-10-28 with their graded outcomes, which are scenarios and plants ready-made. The maintainer asked on 2026-11-01 how to add it. It needs no instance mount: the content is public in pumllint, so it is a subject root under subjects/, vendored at a pumllint commit with a SOURCE note and a digest test like cargo_quote. The register is for every subject of an organisation (the maintainer's intent, 2026-11-01): the J-F subject gets its own slice in ieam-register, the second pilot slice beside CargoQuote's, re-vendored at a tag, and a register_map.toml, so the footprint and the impact walk answer on J-F content. First cut deterministic (D1 to D6, rdflib and Neo4j); the oracle adapter and the arms follow.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 subjects/jef_data_load/ loads through KG_SUBJECT and a deterministic run completes on rdflib and on Neo4j with no edit outside harness/extract.py (mappers are the harness's extension point) and the vendor tool
- [ ] #2 The subject's bytes are vendored from a pumllint commit by tools/vendor_subject.py with a SOURCE.md naming the commit, and tests/test_vendor_subject.py holds every file to its digest; J-F's original code is absent
- [ ] #3 The gate's task class names its required keys as JDL requirement ids and the verification map is derived from the scenarios' tags
- [ ] #4 The five degradation arms are the subject's scenarios, with plants.toml reproducing the plant bundle's kit patches and the cards quoting the graded outcomes
- [ ] #5 The page shows the subject with every scenario on the menu, the register entry present, and the footprint and the impact walk answering on J-F content through the subject's register_map.toml
<!-- AC:END -->
