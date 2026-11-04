---
id: TASK-0135
title: >-
  A subject check: the manifest, the keys against the documents' yield, the
  register map, at least one scenario (doc-0018 candidate 1)
status: To Do
assignee: []
created_date: '2026-11-04T22:40:00Z'
labels:
  - subject
  - check
milestone: m-8
dependencies:
  - TASK-0134
priority: medium
type: feature
ordinal: 135000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0018 §6 candidate 1, on the maintainer's go of 2026-11-04. `tools/check_subject.py`: pure, no store. It checks (F5) the manifest's tables and fields against what `Subject` reads, naming an unknown table (`[task.codegen]`, `[[artefacts]]`); each `[[artefact]]`'s fields and its mapper in the registry; (F3) at least one scenario when a task is declared; key syntax; (F2) the documents' yield per artefact (`extract.extract_all` with no store) against every task's required keys, with a did-you-mean for a required key the yield lacks; (F4) every `register_map.toml` node in the register and every `owner` among its nodes' owners. JSON under a schema in `harness/schemas/`, checked by `harness/schema_check.py`. Its refusals join `tools/check_instance.py` (exit 1, layout); a key the yield lacks is a finding with its did-you-mean, not a silent absent. `SUBJECT` is bound at import (F6): the check runs the extraction in a subprocess per subject, or takes the subject as a value; no store either way. Both public subjects pass unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 On doc-0018's probe subject (REQ-02|txt misspelt, no scenarios.toml, a register_map row naming CAP-9999, an owner outside its node's owners, a [task.codegen] typo) the check names each with its fix, and check_instance.py exits 1
- [ ] #2 cargo_quote, jef_data_load and the example instance pass with no finding; the record and the comparator are unchanged
- [ ] #3 Report JSON validates against its schema; check_instance.py's output and exit contract are documented in instance/README.md; CHANGELOG line under Unreleased (a layout refusal is a contract change)
- [ ] #4 No store is opened and no file is written (a test holds the instance's digest before and after)
<!-- AC:END -->
