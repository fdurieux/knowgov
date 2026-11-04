---
id: TASK-0119
title: A synthetic CargoQuote ARIS export (AML and BPMN) for the ARIS connector
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T16:54:00Z'
updated_date: '2026-11-04T17:00:00Z'
labels:
  - aris
  - connector
milestone: m-8
dependencies: []
priority: high
ordinal: 119000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0006 makes ARIS the lighthouse incumbent; task-0063, the connector that reads an ARIS export into an instance as a dated mirror, needs a public test export. The maintainer chose (2026-11-04) to generate one from public CargoQuote material only: the vendored kit under subjects/cargo_quote/vendor and the vendored register under demo/register. No private export may enter this repository.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A deterministic generator writes one AML file and BPMN 2.0 files for CargoQuote's processes from the public CargoQuote material only (the vendored kit under subjects/cargo_quote/vendor and the vendored register under demo/register); two runs give byte-identical output
- [x] #2 Every process and capability object carries its register id (PROC-/CAP-) in an attribute, and every object a GUID stable across runs
- [x] #3 A second, later export variant drops one process and renames one function, for task-0063's append-only and stale-id criteria
- [x] #4 A test parses the AML (stdlib xml.etree) and checks the counts, ids and GUID stability; BPMN with no lint findings is preferred, and if bpmnlint is not available that is recorded
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/aris_export.py reads the vendored kit BPMN and the register nodes whose [source] system is kit (processes, capabilities, application modules, process owners) plus realizes/supports; hand table maps kit tasks to PROC ids.
2. Builds one MT_EEPC (PROC-0001's model) by turning the kit flow into events/functions/XOR rules, plus register links on definitions; renders AML by hand (DOCTYPE) and a BPMN 2.0 file with DI.
3. Variants first (2026-11-04) and later (2026-11-18: PROC-0005 dropped, PROC-0004 renamed).
4. Committed fixtures under tools/fixtures/aris_cargo_quote/<variant>/; --check mode; tests/test_aris_export.py; harness.yml step runs --check and bpmnlint.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Placement decision: committed fixtures beside the generator (tools/fixtures/aris_cargo_quote/{first,later}/), NOT placed into the example instance. Reason: example_instance.py's output is the record's instance; a second BPMN under bpmn-process-models would be read by the bpmn mapper into the store and move the record, and aris-epc files would change check_instance/preload outputs and digests. task-0063 decides whether its connector copies the fixtures into the example instance (or into register exports/aris/<date>/).
Register id attribute: AT_ID (ARIS's Identifier attribute, filled by hand), on PROC, CAP, APP and ORG objects; step functions, events and rules carry none. The name is to be connector configuration.
GUIDs: uuid5 of a fixed namespace (uuid5(NAMESPACE_URL, https://github.com/fdurieux/knowgov/aris-fixture/cargo_quote)) and a stable key; every Group, ObjDef, CxnDef, Model, ObjOcc and CxnOcc has one, its ID is <Tag>.<guid>.
UNVERIFIED: the type, symbol and attribute names (MT_EEPC, OT_*, ST_*, CT_*, AT_*) follow public descriptions of ARIS's XML export and are not checked against any ARIS method filter or installation; the docstring and the AML header comment say so. Connection reading: CT_LNK_2 process->capability (register realizes), CT_CAN_SUPP_1 app->process (supports), CT_EXEC_1 person type->process (owner). Capability hierarchy not restated.
Counts: first 41 ObjDef / 45 CxnDef / 44 ObjOcc / 43 CxnOcc; later 38/39/38/37 (PROC-0005's function and the two events only it followed are gone).
bpmnlint 12.0.0 with instance/ci/bpmnlintrc (recommended): 0 problems on both BPMN files (the kit's own BPMN: 105). The tests job has no bpmnlint, so the test runs it only when installed; harness.yml's Node step now runs it on the fixtures.
python tests/run_tests.py 343/343; KG_SUBJECT=subjects/jef_data_load 343/343. Example instance, its digests and the record untouched.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/aris_export.py generates a synthetic ARIS export of CargoQuote from the vendored kit BPMN and the vendored register only: one AML (MT_EEPC of PROC-0001, register objects with AT_ID, uuid5 GUIDs on every element) and one BPMN 2.0 file with DI per variant, committed under tools/fixtures/aris_cargo_quote/{first,later}/. later drops PROC-0005 and renames PROC-0004, GUIDs unchanged. tests/test_aris_export.py parses with xml.etree: byte-identical regeneration equal to the fixtures, counts, ids, GUID uniqueness and stability, reference resolution, the variant diff, the BPMN's ids; bpmnlint when installed. harness.yml runs --check and bpmnlint 12.0.0 (0 problems). Risks: ARIS type names unverified; fixtures not placed into the example instance (task-0063 decides).
<!-- SECTION:FINAL_SUMMARY:END -->
