---
id: TASK-0135
title: >-
  A subject check: the manifest, the keys against the documents' yield, the
  register map, at least one scenario (doc-0018 candidate 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T22:40:00Z'
updated_date: '2026-11-04T23:56:00Z'
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
- [x] #1 On doc-0018's probe subject (REQ-02|txt misspelt, no scenarios.toml, a register_map row naming CAP-9999, an owner outside its node's owners, a [task.codegen] typo) the check names each with its fix, and check_instance.py exits 1
- [x] #2 cargo_quote, jef_data_load and the example instance pass with no finding; the record and the comparator are unchanged
- [x] #3 Report JSON validates against its schema; check_instance.py's output and exit contract are documented in instance/README.md; CHANGELOG line under Unreleased (a layout refusal is a contract change)
- [x] #4 No store is opened and no file is written (a test holds the instance's digest before and after)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/check_subject.py: pure checks on subject.toml (tables, [subject]/[[artefact]]/[tasks.*]/[record] fields, required task fields, key syntax, block levels, share), a scenario for a task, register_map.toml nodes and owners against a register, and the documents' yield from the load's own mappers in a child process (SUBJECT bound at import), did-you-mean on a near key. 2. harness/schemas/subject-check.schema.json. 3. check_instance.py runs it per subject: refusals as layout errors (path and mapper left to check_instance's own), warnings and notes in the text, the report as the subject's check. 4. tools/fixtures/subject_probe with every defect. 5. tests (stdlib and with the mappers), a harness.yml step where the mappers run, instance/README.md, subjects/README.md, CHANGELOG, CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The yield runs in a child process (tools/check_subject.py --yield-only, KG_SUBJECT set, PYTHONDONTWRITEBYTECODE) because harness/extract.py binds SUBJECT at import and imports PyYAML, which the tests job lacks: there the yield reads unchecked with its reason; with a mapper module missing (pumllint) the yield is partial and the keys are not compared, so a key an unchecked artefact would yield never reads as a typo. The did-you-mean compares against the yield minus the task's own required keys (difflib 0.8), so two required keys that differ by a letter never point at each other; both public subjects yield every required key (cargo_quote 93 keys for 57 required, J-F 712 for 163). A did-you-mean is a warning, not a refusal: a near key can be legitimately absent. harness.yml asserts the yield and the did-you-mean where the mappers run; its guards use 'if grep ...; then exit 1; fi', since a negated command never fails a bash -e step. The tool's docstring avoids naming capture.py, which tests/test_clock.py reads as a date-reading command.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/check_subject.py reads a subject root before the load, pure and with no store: unknown tables and fields named with the nearest (F5), a task's required fields and values, key syntax, a scenario for a task (F3), register_map.toml nodes in the register and each owner among its nodes' owners (F4), and the task keys against the documents' yield from the load's own mappers in a child process, a near key a warning with its did-you-mean (F2). Report pinned by harness/schemas/subject-check.schema.json. tools/check_instance.py runs it on every subject: refusals are layout errors (exit 1), warnings and notes listed, the report the subject's check in --json. doc-0018's probe is tools/fixtures/subject_probe: refused with each defect and its fix; cargo_quote, jef_data_load and the example instance pass with no finding; the instance's digest is unchanged by the check and the yield's child imports no store. 413/413 under both default subjects; the check's tests 7/7 with the mappers installed; harness.yml asserts the yield and the did-you-mean. A layout refusal is a contract change, under Unreleased.
<!-- SECTION:FINAL_SUMMARY:END -->
