---
id: TASK-0134
title: >-
  README lines: the gate needs a scenario, and an authored document loads
  approved by default (doc-0018 candidate 9)
status: To Do
assignee: []
created_date: '2026-11-04T22:40:00Z'
labels:
  - docs
  - subject
milestone: m-8
dependencies: []
priority: medium
type: docs
ordinal: 134000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0018 §6 candidate 9, on the maintainer's go of 2026-11-04. Two facts an adopter meets today, documented now while their fixes come: (1) the gate needs at least one scenario: `subjects/README.md` lists `scenarios.toml` as not required, yet `gate_cli.py` exits 2 on a subject with none (doc-0018 F3); an instance subject declares at least the pristine scenario `subjects/minimal/` declares (`S0`). (2) Until the F1 decision (decision-0009, proposed) lands, a document a mapper reads as `authored` loads verified and approved by the subject's default human agent, `agent:maintainer`, whether or not the manifest declares `[verification]` (doc-0018 F1): an adopter who drafts a requirements file with an assistant gets it read as approved. Adopter register in `instance/README.md`, maintainer register in `subjects/README.md`; flags named are real flags (`tests/test_docs_flags.py` style guards where they exist).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 subjects/README.md says the gate needs at least one scenario and shows the minimal S0 pattern
- [ ] #2 instance/README.md says, in plain words, what an authored document reads as today and that declaring [verification] and [provenance] names who attests; it points to decision-0009 as proposed
- [ ] #3 Both suites pass; no code changes
<!-- AC:END -->
