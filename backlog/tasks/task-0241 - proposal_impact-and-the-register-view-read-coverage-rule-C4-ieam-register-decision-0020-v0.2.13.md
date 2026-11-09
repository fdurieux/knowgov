---
id: TASK-0241
title: >-
  proposal_impact and the register view read coverage rule C4 (ieam-register
  decision 0020, v0.2.13)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T00:14:00Z'
updated_date: '2026-11-09T07:22:00Z'
labels:
  - register
  - proposal
  - contracts
dependencies: []
priority: high
ordinal: 235000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ieam-register v0.2.13 (re-vendored by task-0240, #393, on the maintainer's word: "yes, re-vendor the register at v0.2.13 before 0.9.0") adds coverage rule C4: an approved process that realises an approved capability is supported by an approved application or module. knowgov's harness/proposal_impact.py (_cov, coverage) and demo/app/register_view.py (coverage, coverage_lines) read coverage C1 to C3 by name, and harness/schemas/proposal-impact.schema.json requires exactly C1, C2 and C3. So a proposal that breaks C4 reads clean in proposal_impact, and the register view has no C4 coverage line (its findings list and error badge do show a C4 error). Reading every rule the vendored checker defines, not a fixed list, changes the proposal-impact output, a contract (decision-0016 point 3). Placement is the maintainer's: in 0.9.0 (the coordinator's recommendation, 2026-11-09: it completes the re-vendor the maintainer asked for before the cut, and after the cut it is a 0.10.0), or after the cut with the gap named in 0.9.0's Known limits. Not built until the maintainer answers; depends on task-0240 (#393).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 proposal_impact reads every coverage rule the vendored check_register.py defines (C1 to C4 at v0.2.13), and its schema names C4; a proposal overlay that breaks C4 reports it, hypothetical, as it does C1 to C3
- [x] #2 The register view's coverage summary and lines name C4 beside C1 to C3
- [x] #3 A fixture breaking C4 is held by tests and by tools/check_proposal_branch.py or a sibling; the deterministic comparator and the round trip pass with the record unchanged
- [x] #4 CHANGELOG.md names it under Unreleased › Contract changes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The maintainer, 2026-11-09: "all as advised", so in 0.9.0 (relayed by the coordinator). Built: proposal_impact.coverage_rules(CR) is tuple(CR.COVERAGE_RULES), the register's own checker loaded from the register root; _cov, coverage and render_text loop over it. demo/app/register_view._rules() reads the vendored checker's COVERAGE_RULES for coverage and coverage_lines; the page renders coverage_lines as given. Schema proposal-impact, version 1, additive, by the slices and branch precedent: before and after name C4, the new gap's rule enum takes C4; C1 to C3 stay required, so a report on an instance register from before decision 0020 (no C4) validates. harness/schema_check has no patternProperties, so a later rule (C5) needs one schema line. Fixture tools/fixtures/proposal_c4_gap.json: PROC-0011 realizes CAP-0003, with a diagram of record (C3 holds) and no supports link; C4 5/5 -> 5/6, new gap PROC-0011, hypothetical. check_proposal_branch runs both fixtures in branch mode and writes a node's [source] into the branch files, so the branch reads what the held overlay reads. The worked example breaks no C4. Docs: the MCP tool descriptions and instance/README.md name every rule the checker defines. Each new test fails on 6d27961.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
proposal_impact and the register view read every coverage rule the vendored check_register.py defines, from its COVERAGE_RULES (C1 to C4 at ieam-register v0.2.13); a proposal breaking C4 reports it, hypothetical, under coverage.new_gaps; the proposal-impact schema (version 1, additive) names C4 with C1 to C3 still the required keys. Fixture tools/fixtures/proposal_c4_gap.json, held by tests/test_proposal_impact.py and tools/check_proposal_branch.py in branch mode; the register view's summary and lines name C4. The record is unchanged: the comparator on S1-S7 and J-F, check_round_trip --chain (rdflib, and Neo4j to rdflib and back), check_register_change, check_proposal_branch and check_mcp_server on both subjects hold. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
