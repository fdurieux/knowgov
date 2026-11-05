---
id: TASK-0136
title: >-
  decision-0009 (a): a load attests authored statements and approves only what
  the subject declares, with no defaults
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T23:12:00Z'
updated_date: '2026-11-05T00:32:00Z'
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
- [x] #1 With no [verification] authored declared, a load runs no authored-by-construction review; with no approval declared, it approves nothing; each runs exactly as before when declared
- [x] #2 On doc-0018's probe (tools/fixtures/subject_probe, given a scenario), REQ-01|text loads proposed, not approved, and the gate reports it below verified
- [x] #3 cargo_quote and jef_data_load load unchanged: the deterministic runs equal the record and the comparator passes, on rdflib and in the stack job
- [x] #4 tools/check_subject.py reports, as a note naming decision-0009, a subject whose mappers emit authored statements and that declares no [verification] authored
- [x] #5 instance/README.md's 'Who vouches for a document' and subjects/README.md describe the rule in place of the old default; CHANGELOG line under Unreleased > contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/load.py load_verifications: verify_authored only when [verification] authored is declared, approve_verified only when approval is; no defaults. 2. tools/check_subject.py: a note (rule attestation, schema enum) when the yield shows authored statements and no [verification] authored is declared. 3. harness.yml: doc-0018's probe given minimal's S0 loads REQ-01|text proposed, REQ-02|txt absent. 4. instance/README.md 'Who vouches for a document' and subjects/README.md to the rule; CHANGELOG under Unreleased > contract changes. 5. The records: CargoQuote, J-F and minimal deterministic runs against the comparator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Only load_verifications called verify_authored and approve_verified; change.py's stage-2 reverify declares its own keys and record in scenarios.toml and still calls load_verifications, so S6 runs as before (the comparator holds S6). The probe step is proven both ways locally: on this load it reads {REQ-01|text: proposed, REQ-02|txt: absent}; on the old load the same step fails with REQ-01|text approved. load.py imports PyYAML, so the stdlib tests job cannot import it; the behavioural proof is the harness.yml step on the rdflib job, the check's note is in tests/test_check_subject.py. Local, rdflib with the record's pins, on 220d79d plus this stack: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6, minimal BLOCKED with both keys absent.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0009 (a) built. harness/load.py load_verifications runs the authored-by-construction review only when subject.toml declares [verification] authored, and approves verified statements only when it declares approval; no default (agent:maintainer, record 'approval') stands in for a person. A subject without the declarations loads its authored statements proposed and approves nothing, and the gate reads them below verified (doc-0018's probe given S0: REQ-01|text proposed, harness.yml). tools/check_subject.py notes a subject whose documents hold authored statements and that declares no [verification] authored (rule attestation, additive in the schema). Both public subjects declare both tables: CargoQuote (7 scenarios) and J-F (6) equal their records on rdflib, minimal BLOCKED, the stack job's comparator on this PR. instance/README.md and subjects/README.md state the rule; CHANGELOG under Unreleased > contract changes. Follow-up named by the decision, not created: (c), an attestation bound to each artefact's digest, at m-8.
<!-- SECTION:FINAL_SUMMARY:END -->
