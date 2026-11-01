---
id: TASK-0002
title: 'Subject root and manifest: every reference to CargoQuote becomes data'
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - platform
  - subject
milestone: m-1
dependencies:
  - TASK-0001
priority: high
type: feature
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The harness and page know their subject by name in seven places: the kit file list and family map in kitio.py, the plants per scenario in plant.py, the 36 required keys in tasks.py, the key-to-node map register_map.toml, the glossary-held sentences in views.py, and the seven-scenario menu. A platform serving more than one subject reads all of that from a subject root with one manifest (TOML): artefacts with family and mapper, required keys per task, optional scenarios with their plants, the key-to-node map. CargoQuote becomes the first subject under that root and its record is the regression oracle.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A subject manifest format is documented and CargoQuote is expressed in it with no loss
- [ ] #2 No module under the harness or the page names CargoQuote, a kit file or a scenario id outside the subject root
- [ ] #3 The deterministic comparator stays green on CargoQuote
- [ ] #4 A second subject with an empty artefact list loads and the gate reports every required key absent
- [ ] #5 Scenarios are optional: a subject without plants offers replay and deterministic of its own record only
<!-- AC:END -->
