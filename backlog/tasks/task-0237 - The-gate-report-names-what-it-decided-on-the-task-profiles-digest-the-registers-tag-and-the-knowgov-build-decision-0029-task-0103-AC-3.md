---
id: TASK-0237
title: >-
  The gate report names what it decided on: the task profile's digest, the
  register's tag and the knowgov build (decision-0029, task-0103 AC #3)
status: To Do
assignee: []
created_date: '2026-11-08T23:46:00Z'
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
decision-0029 (2026-11-08, taken under the maintainer's overnight delegation) brings task-0103 AC #3 into 0.9.0, doc-0014 C9 option B: the gate report carries what was relied on. Additive fields on harness/schemas/gate-report.schema.json (additionalProperties false, so a schema version move under the project's convention): task_profile, the sha256 of the canonical JSON of the subject's [tasks.<class>] table read; register, the register's tag and commit (KG_REGISTER's SOURCE.md when vendored, else the checkout's git HEAD read without network, else null with the reason); knowgov, task-0231's build identity (version, commit, describe). The scored record does not move: if the comparator cannot pass without re-freezing it, stop and report a DECIDE. task-0103 AC #1 and #2 stay at m-8.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 gate_cli's report, and the MCP reader's gate_verdict where it returns the report, carry task_profile, register and knowgov as above; the schema pins them and its version moves under the project's convention
- [ ] #2 tools/check_round_trip.py and tools/check_mcp_server.py hold the fields across the hops and the transports; the deterministic comparator passes with the record unchanged
- [ ] #3 CHANGELOG.md names the fields under Unreleased › Contract changes; task-0103 AC #3 is checked when this merges
<!-- AC:END -->
