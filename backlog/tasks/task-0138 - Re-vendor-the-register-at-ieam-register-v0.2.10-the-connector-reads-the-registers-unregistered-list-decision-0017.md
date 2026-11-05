---
id: TASK-0138
title: >-
  Re-vendor the register at ieam-register v0.2.10: the connector reads the
  register's unregistered list (decision 0017)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:41:00Z'
updated_date: '2026-11-05T20:12:00Z'
labels:
  - register
  - connector
milestone: m-8
dependencies: []
priority: medium
type: task
ordinal: 138000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On the maintainer's go of 2026-11-05. ieam-register v0.2.10 (4149e06, decision 0017) adds `unregistered` to `RECONCILE.json`: the export's ids (`MANIFEST.toml` `[ids]` keys) that no node's `[source]` carries, keyed by the system's `id_field`, and a per-system `exports` count in `check_register.py --report`. knowgov vendors the register at a tag (`tools/vendor_register.py`) and its connector imports the vendored `reconcile.py` (task-0121), adding its own extensions, among them `unknown_ids`: carried register ids the register does not hold. Re-vendor at v0.2.10 and let the connector's RECONCILE.json carry the register's `unregistered` as computed by the vendored code. Then compare `unknown_ids` with `unregistered` on the synthetic ARIS fixtures: if they are the same set, drop the extension (the register's field replaces it); if they answer different questions (an unknown register id typed in the tool versus an export object no node carries), keep both and document the difference. Either outcome is recorded in the task notes with the fixture numbers. Tags v0.2.9 → v0.2.10 in tests and workflows; CargoQuote's and J-F's records unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 vendor_register.py at v0.2.10 from a clean checkout; SOURCE.md and every digest test pass; the vendored reconcile.py writes unregistered
- [x] #2 connector.py's RECONCILE.json carries unregistered for the synthetic ARIS exports (first and later), as the register computes it; tests hold the entries
- [x] #3 unknown_ids is either dropped (same set as unregistered, shown on the fixtures) or kept with its distinct meaning documented in instance/README.md; the comparison is in the task notes
- [x] #4 The record and the comparator are unchanged on both subjects; CHANGELOG line under Unreleased (a contract change if unknown_ids is dropped)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. vendor_register.py at v0.2.10 from a clean checkout; tags v0.2.9 -> v0.2.10 in tests, demo.yml, register_fixture.
2. connector RECONCILE.json: unregistered flows from the vendored reconcile.py; a test holds it on first and later.
3. Compare unknown_ids with unregistered on both fixtures; keep or drop by the evidence; document in instance/README.md.
4. Suite, deterministic rdflib run and comparator on both subjects, check_instance on the example instance; CHANGELOG under Unreleased.

5. (Maintainer's (a), decision-0010, 2026-11-05) The connector's MANIFEST in the register's format: [ids] every AML object by GUID, [register_ids] GUID -> register id, [bpmn_ids]; carried-by-GUID dropped; unknown_ids and stale-by-register-id read the register-id tables; proposal_impact's D2 reads [register_ids].
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Comparison (synthetic ARIS fixtures, example instance, connector.land):
- first (2026-11-04): 14 register ids carried; unknown_ids 0; unregistered 14 (every carried id, keyed aris_guid).
- later (2026-11-18): 13 carried (PROC-0005 vanished, stale); unknown_ids 0; unregistered 13.
- Removing PROC-0005 from a register copy: unknown_ids [PROC-0005], unregistered still 14.
- PROC-0004's [source] set to system=aris, aris_guid=<its object GUID ac939acd-...>: still unregistered (14). Set to aris_guid="PROC-0004": dropped (13).
Verdict: different sets, different questions. unknown_ids = carried register ids the register lacks (typo or missing node). unregistered = MANIFEST [ids] keys that no node's [source] carries under the system's id_field. The connector keys [ids] by register id, while the register reads them as id_field values (aris_guid), so unregistered lists every carried id unless a node records its register id as its aris_guid. Both kept; instance/README.md gives each meaning. Not a contract change.
Checks: tests 439/439; rdflib deterministic CargoQuote 0 differ over 7 scenarios, J-F 0 differ over 6; check_instance on the example instance: layout holds; check_subject cargo_quote: 93 keys, manifest holds.

Option (a) measured, then chosen as (a3) (decision-0010; table there). first/later: 41/38 AML objects, every one with a GUID; 14/13 carry AT_ID; the BPMN carries 5/4 register ids, all also in the AML. Nodes as in the example (none carry aris_guid): ids diff by GUID (later: renamed PROC-0004's GUID; deleted PROC-0005's and two events'); register stale 0, connector stale PROC-0005; unregistered 41/38. With the 14 nodes given [source] aris_guid: unregistered 27/25, and the register's own stale_nodes is PROC-0005. Implemented: connector, proposal_impact D2 ([register_ids], [guids] in an older folder), tests (tests 442/442), instance/README.md, CLAUDE.md, CHANGELOG contract change. Record unchanged: CargoQuote 0 differences over 7 scenarios, J-F 0 over 6 (rdflib). check_instance: layout holds. aris_export --check: rc 0. check_proposal_branch: holds.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Re-vendored the register at ieam-register v0.2.10 (4149e06, decision 0017), and moved tags v0.2.9 -> v0.2.10 in the tests, demo.yml and register_fixture. Comparing unknown_ids with the register's unregistered on the ARIS fixtures (0 vs 14 and 0 vs 13) showed that the connector keyed MANIFEST [ids] by register id, while the register reads them by the system's id_field (aris_guid). The maintainer chose (a) (decision-0010). The MANIFEST now follows the register's format: [ids] holds every AML object by GUID (41/38), [register_ids] maps GUID to register id, and [bpmn_ids] holds the BPMN files' register ids. The register's own ids diff, stale_nodes and unregistered now read it correctly. The carried-by-GUID extension is dropped. unknown_ids and stale-by-register-id stay, read from the register-id tables; the latter is redundant once nodes carry [source] aris_guid, as a test shows. proposal_impact's D2 reads [register_ids] (and [guids] in older folders). This is a contract change (CHANGELOG). The record is unchanged on both subjects, and the tests pass 442/442. Follow-up: decision 0017's open question, how to excuse an object that is not a node (the 27/25 events and rules).
<!-- SECTION:FINAL_SUMMARY:END -->
