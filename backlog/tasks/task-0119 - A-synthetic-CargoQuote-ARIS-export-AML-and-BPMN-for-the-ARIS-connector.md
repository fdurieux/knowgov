---
id: TASK-0119
title: A synthetic CargoQuote ARIS export (AML and BPMN) for the ARIS connector
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T16:54:00Z'
updated_date: '2026-11-04T17:12:00Z'
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

Revision after the coordinator's evidence (2026-11-04): the maintainer imported a generated BPMN into ARIS 10.0 (exporterVersion 10.0.0.320027101) and exported it again.
- Observed: process ids, the collaboration id, participant names, element types and names, element <documentation> (verbatim, plus textFormat="text/plain"), flow topology and names, and DI bounds were kept. Every other element, participant, flow and DI id became ID-<time-based uuid>, Shape_ID-... or Edge_ID-.... calledElement, process-level documentation, isExecutable and the multi-instance id were dropped, and timeCycle was emptied. The root became Definitions_ID-..., with targetNamespace http://www.softwareag.com/aris/bpmn2 and exporter ARIS. Elements use the semantic: prefix. ARIS added the aris, arisebpmn, color, deco and i18n namespaces, arisebpmn:type=MT_ENTERPRISE_BPMN_COLLABORATION, colours, aris:port, BPMNLabel with a font style, and xml:lang.
- This was observed on ARIS 10.0, for BPMN only. Whether ID-... values stay stable across two exports has NOT been observed. The fixture therefore gives each variant different ID-... values, so a reader that matched them across exports would fail.
- Changes: the BPMN process @id is now PROC-0001. Each activity's register id is its <documentation> text. No register id is an element id, and nothing relies on calledElement, timeCycle or process-level documentation. Both dialects carry a collaboration (collab_cargo_quote) whose participant is named CargoQuote.
- New per variant: quote_process.aris.bpmn, the same model in ARIS's dialect. Its ID-... values are derived (uuid5 bytes stamped version 1). The aris, arisebpmn, color, deco and i18n namespace URIs are synthetic stand-ins (urn:knowgov:synthetic:aris-dialect:*), because the real ones were not in the evidence; the aris:port value is invented. A test holds the dialect's model (types, names, register ids, flow topology with ids dropped) equal to the knowgov dialect's.
- bpmnlint 12.0.0 (recommended): 0 problems on all four BPMN files.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/aris_export.py generates a synthetic ARIS export of CargoQuote from the vendored kit BPMN and the vendored register only. Per variant it writes one AML file and the same process as BPMN 2.0 with DI in two dialects: knowgov's own and ARIS 10.0's observed export dialect. They are committed under tools/fixtures/aris_cargo_quote/{first,later}/.
- AML: an MT_EEPC of PROC-0001; register objects carry AT_ID; every element has a uuid5 GUID.
- BPMN: PROC-0001 is the process @id and each activity's PROC id is its documentation text, which are what survived ARIS's round trip.
- later drops PROC-0005 and renames PROC-0004; GUIDs are unchanged.
- tests/test_aris_export.py (xml.etree) checks byte-identical regeneration, counts, ids, GUIDs, reference resolution, the variant diff, that both BPMN dialects hold the same model, and the ARIS dialect's ids and dropped fields. It runs bpmnlint when installed. harness.yml runs --check and bpmnlint 12.0.0, which reports 0 problems.
- Risks: the AML type names are unverified; the ARIS-dialect namespace URIs are stand-ins; ID-... stability across ARIS exports is unobserved; the fixtures are not placed in the example instance (task-0063 decides).
<!-- SECTION:FINAL_SUMMARY:END -->
