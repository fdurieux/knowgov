---
id: TASK-0021
title: >-
  Second public subject: the J-F data-load kit from pumllint's recreation
  experiment
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-01T19:43:00Z'
updated_date: '2026-11-01T20:04:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 0021.01: tools/vendor_subject.py reads the path set, destination and note wording from the subject's [vendor] table; subjects/jef_data_load/ vendored from pumllint main (untagged, --allow-untagged) with SOURCE.md and the digest test. 2. 0021.02: mappers for requirements.json, the prose contracts and the component/class/activity/state diagrams; subject.toml, scenarios.toml (S1 pristine + the five degradation arms), plants.toml from the plant bundle; deterministic run on rdflib and Neo4j; the page shows it; harness.yml runs it. 3. 0021.03: the oracle adapter and pins. 4. 0021.04: the register slice in ieam-register, re-vendor, register_map.toml. Each step a PR merged on green.
<!-- SECTION:PLAN:END -->
