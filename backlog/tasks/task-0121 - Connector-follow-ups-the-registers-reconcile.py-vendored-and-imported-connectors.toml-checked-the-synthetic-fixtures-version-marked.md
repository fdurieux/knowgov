---
id: TASK-0121
title: >-
  Connector follow-ups: the register's reconcile.py vendored and imported,
  connectors.toml checked, the synthetic fixture's version marked
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T18:23:00Z'
updated_date: '2026-11-04T18:38:00Z'
labels:
  - aris
  - connector
milestone: m-8
dependencies: []
priority: low
ordinal: 121000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0063 (#196) landed `tools/connector.py`; its report proposed three follow-ups. The connector restates the comparison of ieam-register's `tools/reconcile.py`, which the demo does not vendor (task-0063 read it from a v0.2.8 clone), so the two can drift; `connectors.toml` is read but never checked, so a misspelt system fails late; and the synthetic ARIS fixture's `exporterVersion` lands verbatim in a MANIFEST's `source_version`, so a landed manifest reads like a real ARIS export.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `tools/vendor_register.py` vendors `tools/reconcile.py` with the register's tools at tag v0.2.8, which is unchanged. `tools/connector.py` imports its comparison instead of restating it, and the connector's tests are unchanged.
- [x] #2 `tools/check_instance.py` validates `connectors.toml`: every `[system.<name>]` exists in the register's `metamodel/sources.toml`, and `id_attribute` is a string. Tests cover a good file and each bad case.
- [x] #3 In the synthetic ARIS fixtures, the BPMN keeps `exporterVersion="10.0.0.320027101"`, because that fidelity is the point of the fixture. A landed MANIFEST's `source_version` reads as synthetic, for example "synthetic, mimicking ARIS 10.0.0.320027101", so a reader of a landed manifest is never misled. The generator stays byte-deterministic, and the fixtures are regenerated.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add tools/reconcile.py to vendor_register.py's PATHS; re-vendor from a clean v0.2.8 clone (tag unchanged). 2. connector.reconcile calls the vendored REC.reconcile on the landing folder, then applies its own additions: GUID-carried ids, deleted-id stale, unknown_ids. 3. check_instance.connectors(): systems against sources.toml, id_attribute a non-empty string; tests for a good file and each bad case. 4. aris_export: exporter='synthetic, mimicking ARIS', exporterVersion kept; regenerate; test that the landed source_version reads synthetic.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Vendored from a clean v0.2.8 clone (f8fb17e): 101 files, 1 added (tools/reconcile.py), 0 changed; SOURCE.md rewritten by the tool. The vendored reconcile() keys stale on MANIFEST ids alone; ARIS nodes carry aris_guid, which the connector records under [guids], so the connector drops the register-rule stale entries whose external id is a carried GUID: the same result as task-0063's carried = ids | guids. tests/test_connector.py is unchanged and passes. test_vendor_register's mini register gains tools/reconcile.py (18 -> 19 files). The marker went into the BPMN's exporter attribute, which test_aris_export held as 'ARIS'; that one assertion now reads the marked value. The fixtures were regenerated, and two runs of the generator give identical bytes; aris_export.py --check is clean. Both suites pass, 361/361 each.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The connector now imports the register's own reconcile.py (vendored, still at v0.2.8; 101 files) and adds only its extensions on top: GUID-carried ids, deleted-id stale, unknown_ids. tests/test_connector.py is unchanged. check_instance validates connectors.toml: each system must be in the register's sources.toml, and id_attribute must be a non-empty string; there is a test for a good file and each of eight bad ones. The synthetic ARIS BPMN keeps exporterVersion 10.0.0.320027101, and its exporter now reads 'synthetic, mimicking ARIS', so every part of a landed source_version says synthetic. The fixtures were regenerated, and the generator stays deterministic. Both suites pass, 361/361. Follow-up, unchanged: the {id, previous} stale shape stays provisional until ieam-register decides.
<!-- SECTION:FINAL_SUMMARY:END -->
