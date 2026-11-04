---
id: TASK-0063
title: >-
  Connector for the lighthouse incumbent: its export read into an instance as a
  dated mirror, verified on a real installation
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-04T18:02:00Z'
labels:
  - lighthouse
milestone: m-8
dependencies:
  - TASK-0062
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: high
type: feature
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0012 §3, E3 = 1: every row of the register's mapping/matrix.toml reads unverified, and no export route has met a target installation. The connector is the first route from an incumbent's record (an API, its MCP server, or a file export) into the instance layout the platform already reads, so the gate and the walk answer on the client's own design. The register's contracts bind it: exports are append-only under exports/<system>/<date>/ with MANIFEST.toml and RECONCILE.json, a vanished external id is a stale finding never a deletion, and a node file never copies a tool's attributes. The register's matrix row and its evidence are ieam-register's record, moved by a pull request there.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A dated export from the incumbent lands in the example instance with a manifest and a reconciliation report, and a second export lands beside it without overwriting the first
- [ ] #2 The same export run against the pilot's installation produces a reconciliation report with no error, kept in the private record
- [x] #3 A vanished external id between two exports is reported stale and deletes nothing
- [x] #4 The connector names its system only through instance configuration; nothing under harness/ or demo/app names the vendor
- [ ] #5 An ieam-register pull request moves the incumbent's mapping row off unverified, with the evidence of the run
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/connector.py (stdlib): reads <instance>/connectors.toml [system.<name>] (id_attribute, default AT_ID); readers for AML (the configured attribute, GUIDs) and BPMN in both dialects (namespace URIs, process @id and <documentation> only, never DI or element ids).
2. Lands an export as <instance>/register/exports/<system>/<date>/: the files, MANIFEST.toml in ieam-register's format (exported_on, source, source_version, tool, tool_version, previous, [files], [ids], [guids]), RECONCILE.json in reconcile.py's shape (files/ids added, updated/renamed, deleted; stale_nodes) plus register ids carried before and gone now as stale, and unknown ids; refuses an existing or earlier date; writes atomically; deletes nothing.
3. Generator and fixtures take the real ARIS namespace URIs, exporterVersion and port values.
4. tests/test_connector.py: first then later into a temp example instance (record and the instance's digests untouched); PROC-0005 stale, PROC-0004 renamed, the first folder byte-identical; a guard that nothing under harness/ or demo/app names the vendor.
5. instance/README.md section, CHANGELOG line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
tools/connector.py (stdlib) lands an export in <instance>/register/exports/<system>/<date>/: the files byte for byte, MANIFEST.toml in ieam-register's keys ([files] sha256, [ids] register id -> name, plus [guids] GUID -> register id for the register's own aris_guid rule), RECONCILE.json in reconcile.py's shape (files added/updated/deleted, ids added/renamed/deleted, stale_nodes) plus two additive keys: unknown_ids, and name_conflicts when AML and BPMN disagree (the AML's name kept).
reconcile.py is not in the vendored register (vendor_register.py copies register.py, check_register.py, impact.py), so connector.reconcile restates its comparison with the same keys and semantics, read from ieam-register v0.2.8, and imports load_register/load_toml from the vendored demo/register/tools/register.py. The register's rule alone finds nothing here (CargoQuote's nodes are source.system kit), so a node whose register id the previous export carried and this one does not is stale too: {id, previous}.
Identity: AML ObjDef's configured attribute (connectors.toml id_attribute, default AT_ID); BPMN process @id and element <documentation>, when a register id. Namespaces by URI (BPMN model; ARIS dialect told by http://www.softwareag.com/aris/attributes or /ebpmn). kg:registerId, element ids, DI never read. Date: --exported-on, else the AML Header-Info CreateDate/CreateTime; no wall clock.
Refusals (exit 1): an existing date folder, a date before the newest, a system missing from connectors.toml or sources.toml, a file neither AML nor BPMN 2.0, one id with two names in one file. Exit 2: no connectors.toml, unreadable input. Written to a .<date>.partial-<pid> folder and renamed.
Placement: the mirror lands only in a temporary example instance in tests/test_connector.py (first then later, register files digested before and after, check_instance and the register's own checker pass). example_instance.py, the record and their digests are untouched.
Generator and fixtures: the ARIS dialect's namespace URIs are now the real ARIS 10.0 ones, exporterVersion 10.0.0.320027101, aris:port S and CENTER (which edge gets which is the generator's guess); only the two quote_process.aris.bpmn fixtures moved.
AC #4 guard: tests/test_connector.py scans harness/ and demo/app; three lines are allowed by name, the register view's matrix columns (aris_status beside archi_status) and the glossary's sources-of-record line, which quote the register's own fields.
AC #2 and AC #5 wait for the pilot: the run on the pilot's ARIS installation, kept in the private record, and the ieam-register PR moving the mapping row off unverified with its evidence.
python tests/run_tests.py 359/359; KG_SUBJECT=subjects/jef_data_load 359/359.
<!-- SECTION:NOTES:END -->
