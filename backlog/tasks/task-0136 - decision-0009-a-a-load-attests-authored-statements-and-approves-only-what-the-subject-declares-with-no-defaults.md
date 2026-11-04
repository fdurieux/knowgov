---
id: TASK-0136
title: >-
  decision-0009 (a): a load attests authored statements and approves only what
  the subject declares, with no defaults
status: To Do
assignee: []
created_date: '2026-11-04T23:12:00Z'
labels:
  - subject
  - load
milestone: m-8
dependencies:
  - TASK-0135
references:
  - backlog/decisions/decision-0009
  - backlog/docs/doc-0018
priority: high
type: feature
ordinal: 136000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0009, accepted by the maintainer on 2026-11-04 ("approve (a)", relayed by the coordinating session), option (a). doc-0018 F1: harness/load.py load_verifications called verify_authored and approve_verified with the loader's defaults (agent:maintainer, scope "authored", record "approval") whether or not subject.toml declares [verification] authored and approval, so an authored document read by nobody (a requirements file an assistant drafted, an export of unknown author) reached the gate approved. With (a), the declaration is the attestation: absent, authored statements stay proposed and execution-verified ones reach verified, not approved. Both public subjects declare both tables, so their records, the comparator and the scored record must not move. A contract change (the gate's verdict for an undeclared subject), a minor version while 0.x (decision-0003). (c), binding an attestation to each artefact's digest, is a follow-up decision proposed at m-8, not this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With no [verification] authored declared, a load runs no authored-by-construction review; with no approval declared, it approves nothing; each runs exactly as before when declared
- [ ] #2 On doc-0018's probe (tools/fixtures/subject_probe, given a scenario), REQ-01|text loads proposed, not approved, and the gate reports it below verified
- [ ] #3 cargo_quote and jef_data_load load unchanged: the deterministic runs equal the record and the comparator passes, on rdflib and in the stack job
- [ ] #4 tools/check_subject.py reports, as a note naming decision-0009, a subject whose mappers emit authored statements and that declares no [verification] authored
- [ ] #5 instance/README.md's 'Who vouches for a document' and subjects/README.md describe the rule in place of the old default; CHANGELOG line under Unreleased > contract changes
<!-- AC:END -->
