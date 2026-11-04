---
id: TASK-0085
title: The Turtle round trip carries the pre-load verdicts on each Version
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T01:31:00Z'
updated_date: '2026-11-04T02:52:00Z'
labels:
  - store
milestone: m-8
dependencies:
  - TASK-0064
  - TASK-0070
priority: medium
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the task-0064 session: export_turtle/import_turtle (task-0070) may not carry the preload_* properties task-0064 records on a Version, so a round-tripped store from an instance with a pre-load report could lose them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A store loaded with a pre-load report keeps every Version's preload verdict across both round-trip chains
- [x] #2 tools/check_round_trip.py compares the gate's preload bundle and info findings across the hops
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Check on the example instance with its pre-load report whether export_turtle/import_turtle carry the preload_* Version properties, rdflib and Neo4j 5.26.
2. Extend tools/check_round_trip.py: compare preload_verdicts, gate.resolve's preload bundle per task and the preload info findings across the hops; --expect-preload fails a store that recorded none.
3. Unit test on differences; CI: harness.yml rdflib,rdflib and demo.yml neo4j,rdflib,neo4j and rdflib,neo4j,rdflib on the verdict instance, S6 (stage 2 included) for the budget.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Finding: the verdicts were already carried. Both adapters' export_turtle write every node property generically (the Neo4j adapter through the rdflib layer), so preload_state/tool/tool_version/digest/report/why survive; nothing changed in harness/. What was missing was the proof.
Local, example instance + tools/preload_check.py report, every cargo_quote scenario and S6 stage 2: rdflib→rdflib, neo4j→rdflib→neo4j and rdflib→neo4j→rdflib (Neo4j 5.26.0 community, Java 21) all equal: 9-11 verdicts, 4-7 preload info findings per scenario. Negative: an import that drops the preload_* properties fails on gate counts/findings and on preload verdicts, bundle and findings. Without a report --expect-preload fails.
tests/run_tests.py 248/248 plain, with KG_SUBJECT=subjects/jef_data_load, and in a venv with the pins. J-F round trip subset C,D3 unchanged.

CI on 2792427 (#137): tests, rdflib, stack green. harness.yml: S6 and S6 stage 2 equal with 10/11 verdicts, the step's round trip 13 s. stack: both Neo4j chains on /tmp/verdict. The rdflib job took 18 min, over task-0084's 12; the new step is 13 s of it, the rest is the MCP, lighthouse and J-F round trip steps on a loaded runner, as on #134 and #138.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The Turtle round trip already carried every Version's preload_* verdict: both adapters export node properties generically (Neo4j through the rdflib layer), so no harness/ change. Added the proof: tools/check_round_trip.py compares preload_verdicts, the gate's preload bundle per task and the gate reports' preload info findings across the hops; --expect-preload fails a first store with none. CI runs it on the example instance with its report: rdflib,rdflib in harness.yml, neo4j,rdflib,neo4j and rdflib,neo4j,rdflib in the stack job, on S6 with stage 2 for the budget. tests/test_round_trip.py holds the comparison and the CI lines. Verified locally on all cargo_quote scenarios and on Neo4j 5.26 community; a lossy import fails; run_tests 248/248 plain and J-F. Risk: none new; the rdflib job's budget overrun predates this.
<!-- SECTION:FINAL_SUMMARY:END -->
