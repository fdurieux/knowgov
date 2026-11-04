---
id: TASK-0131
title: proposal_impact's deterministic link candidates D1-D5 (doc-0017 candidate 3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:25:00Z'
updated_date: '2026-11-04T20:48:00Z'
labels:
  - register
  - proposal
milestone: m-6
dependencies:
  - TASK-0130
priority: medium
type: feature
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0017 §6, candidate 3, built with task-0130. In order: D1, a register id the input names (`authored`). D2, an external id (`aris_guid`, `archi_id`, `edm_id`) matched through a node's `[source]`, read from the newest landed export where the connector (task-0063) has landed one (`authored`). D3, an exact normalised name match with a node of the same kind, whose live links are offered to the new node (`inferred`); per decision-0007 a step so matched is reported "same step as JRN-…". D4, for a step with no candidate, the realisers of the product's required capabilities as a pool, listed and never chosen. D5, a forbidden synonym from the glossary in a name is a placement error. A candidate never closes a gap; `inferred` never rises above proposed. Each candidate carries basis, rule (D1-D5) and reason. Precision (accepted over proposed) is measured at the pilot before any model joins (candidate 4, parked).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 On doc-0017's worked example: D3 proposes JRN-0013 is_supported_by PROC-0002 (inferred); D4 lists PROC-0002, PROC-0003 and PROC-0004 as the pool for JRN-0014 and JRN-0015 and chooses none, so both stay C1 gaps; D5 fires on a name carrying a forbidden synonym
- [x] #2 D1 and D2 candidates are authored; D3 inferred; no candidate changes coverage until the proposal states the link itself
- [x] #3 D2 is tested on the synthetic ARIS export landed in a temporary example instance (tools/connector.py), never on a real export
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Built with task-0130 in harness/proposal_impact.py candidates(): D1 stated links and reused ids (authored); D2 a source id_field matched through a register node's [source], else the newest landed export's MANIFEST [guids] (authored); D3 exact normalised name and same kind against approved nodes, their approved live links offered (inferred; 'same step as JRN-...'); D4 pool of PROC realisers of the step's product's required capabilities, none chosen; D5 check_glossary findings on overlay names as placement errors with rule D5. Status always proposed.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tests: D3 proposes JRN-0013 is_supported_by PROC-0002 inferred with 'same step as JRN-0002'; D4 pools PROC-0002/0003/0004 for JRN-0014 and JRN-0015, none chosen, both stay C1; D5 on 'item' (forbidden for node). With the stated support dropped, D3 still offers it unstated and C1 gains JRN-0013: no candidate changes coverage. D2 on the synthetic ARIS fixture landed in a temporary example instance (test_connector._landed): a node carrying PROC-0002's GUID is matched through exports/aris/<newest>/MANIFEST.toml [guids]; the instance's register digest unchanged; on the public register (no export) no D2.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Deterministic candidates D1-D5 in proposal_impact: D1/D2 authored, D3/D4 inferred, every candidate status proposed and never closing a gap; D5 a glossary placement error. Schema pins the status const. PR #211, with task-0130. Precision (accepted over proposed) is to be measured at the pilot before doc-0017 candidate 4 (a model's candidates) joins.
<!-- SECTION:FINAL_SUMMARY:END -->
