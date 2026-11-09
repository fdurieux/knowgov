---
id: TASK-0237
title: >-
  The gate report names what it decided on: the task profile's digest, the
  register's tag and the knowgov build (decision-0029, task-0103 AC #3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T23:46:00Z'
updated_date: '2026-11-09T00:19:00Z'
labels:
  - gate
  - contracts
  - lighthouse
dependencies:
  - TASK-0103
priority: high
ordinal: 232000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0029 (proposed 2026-11-08, parked for the maintainer) would bring task-0103 AC #3 into 0.9.0, doc-0014 C9 option B: the gate report carries what was relied on. Additive fields on harness/schemas/gate-report.schema.json (additionalProperties false, so a schema version move under the project's convention): task_profile, the sha256 of the canonical JSON of the subject's [tasks.<class>] table read; register, the register's tag and commit (KG_REGISTER's SOURCE.md when vendored, else the checkout's git HEAD read without network, else null with the reason); knowgov, task-0231's build identity (version, commit, describe). The scored record does not move: if the comparator cannot pass without re-freezing it, stop and report a DECIDE. The build is prepared overnight and its PR waits for the maintainer's word on decision-0029; if it is declined, this task is archived. task-0103 AC #1 and #2 stay at m-8.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 gate_cli's report, and the MCP reader's gate_verdict where it returns the report, carry task_profile, register and knowgov as above; the schema pins them and its version moves under the project's convention
- [x] #2 tools/check_round_trip.py and tools/check_mcp_server.py hold the fields across the hops and the transports; the deterministic comparator passes with the record unchanged
- [x] #3 CHANGELOG.md names the fields under Unreleased › Contract changes; task-0103 AC #3 is checked when this merges
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. gate_cli SCHEMA_VERSION 3; report() adds task_profile (evaluate passes the digest of SUBJECT.tasks[class], keys substituted for a key set), register (register_impact.identity: SOURCE.md, else own checkout's git HEAD without network, else null+why) and knowgov (build_identity), cached per process.
2. Schema const 3, the three required; harness.yml's version assertion; pinned samples updated.
3. check_round_trip asserts the fields on the first store; differences() holds them across hops; check_mcp_server holds gate_verdict equal to gate_cli --no-load.
4. tests/test_gate_identity.py; CHANGELOG Contract changes; CLAUDE.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-09 evidence. decision-0029 is proposed (coordinator, 2026-11-09): the PR is held for the maintainer.
- AC1: harness/gate_cli.py SCHEMA_VERSION = 3. report() carries task_profile (profile_digest: the sha256 of json.dumps(sort_keys, separators=(',',':')) of SUBJECT.tasks[class]; with an agent-chosen key set the table carries those keys), register (register_impact.identity: SOURCE.md's tag and commit, else the checkout's own git HEAD and the exact tag, GIT_TERMINAL_PROMPT=0, no fetch, refused for an enclosing repository, else null with why) and knowgov (build_identity.identity()). Each is read once per process (register per root). gate_verdict carries them through gate_cli.evaluate. The schema is const 3, with the three required and additionalProperties false on register and knowgov. A version-2 report still reads as --baseline (baseline_of; test).
- AC2: tools/check_round_trip.py fails a first store whose reports do not name the three as this process reads them; differences() holds them across hops. Round trip CQ: every answer survives (task profile 42781013abbc, register v0.2.11). J-F C,D3: every answer survives. check_mcp_server CQ S1,S2,S6 and J-F C,D3: every check holds (gate_verdict equals gate_cli --no-load). Comparator CQ: 0 differing over 7 scenarios. J-F: 0 differing over 6. The record is untouched; the comparator reads no gate report. gate_cli run twice: same bytes.
- Suites: pins + KG_TEST_REQUIRE=rdflib,node,openai 895/896, 1 skipped; no PyYAML 840/896, 56 skipped; J-F 847/896, 49 skipped; 0 failed each.
- AC3: CHANGELOG Unreleased > Contract changes names the three fields and version 3; 0.8.0 byte-identical. task-0103 AC #3 checked in the same PR.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The gate report names what it decided on: schema version 3 (decision-0029, proposed, held for the maintainer). gate_cli's report, and so the MCP reader's gate_verdict, carry three required fields:
- task_profile: the sha256 of the canonical JSON of the subject's [tasks.<class>] table read;
- register: tag, commit and why, from SOURCE.md or the instance checkout's own git HEAD read without the network, else null with the reason;
- knowgov: task-0227's build identity.
The round trip and check_mcp_server hold the fields across hops and transports. Both subjects' comparators pass with the record untouched (the comparator reads no gate report), and two runs give the same bytes. A version-2 report still reads as a baseline. Merge only once the maintainer accepts decision-0029; if declined, close the PR and archive this task.
<!-- SECTION:FINAL_SUMMARY:END -->
