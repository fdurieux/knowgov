---
id: TASK-0301
title: >-
  A key is compared, stored and reported in Unicode NFC wherever it enters
  (decision-0034 A2)
status: Done
assignee: []
created_date: '2026-11-09T21:13:00Z'
updated_date: '2026-11-09T22:04:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - task-0297
  - task-0256
priority: high
ordinal: 294000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 Amendment A2, accepted 2026-11-09 ("N3 (a) as advised"). Found by the spot check's re-check of task-0297 at main f194aac (N3), and confirmed by the coordinator: `société|adresse` in NFC and in NFD both pass `key_rule.is_key` and are different keys, so one reads absent against the other. Nothing in knowgov normalises. The decomposed form comes routinely from macOS paths and clipboards, PDF copies and some exports; a Belgian instance will have accented French names throughout.

The rule: `key_rule.normalise` (NFC, not NFKC) applied wherever a key enters, before validation:
- the MCP reader's arguments;
- `check_subject` and the MCP `subject_check`;
- the `Subject` loader;
- the mappers' yielded keys;
- `register_map.toml` rows;
- code-header citations and `trace`;
- captures;
- `proposal_impact`;
- every CLI that takes a key.

The store holds NFC, and every answer echoes NFC.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `key_rule.normalise` is NFC, and every entry point where a key enters applies it before validation; the task's notes list each entry point.
- [x] #2 A test sends an NFD key through every entry point and finds it matched against the NFC key a document yields, and the reverse, with `société|adresse` and one more name, on a subject copy whose document spells the name in NFD.
- [x] #3 The store holds NFC and every report and answer echoes NFC; `DESCRIPTION`, the docstring and the adopter docs state that canonically equivalent keys are one key.
- [x] #4 `instance/README.md` names `git config core.precomposeunicode true` for macOS checkouts. Every public key is unchanged, and the record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Entry points, each normalised once at its source by key_rule.normalise (NFC, not NFKC), the rule checked after it:
- MCP reader: mcp_server.nfc_keys on the key and keys arguments before argument_refusal (gate_verdict, three_valued_answer, evidence_bundle, key_nodes, derived_outputs).
- Task classes: task_policy.build, so TASKS, the gate, proposal_impact's task keys and capture's required keys.
- Subject loader: register_map() rows, verification_map() (execution lists, review keys), three_valued; proposal_impact and register_impact read the map through it.
- Mappers: extract.Bag.ent and Bag.assertion compose the entity and predicate; extract.mapped_text composes a document before its mapper reads it (a mapper's \w stops at a combining mark), in extract_all and in check_subject's yield.
- Load: plants (load_inferred), captures' answers and unknowns, inferred proposals (load_inferred_proposals).
- Captures: capture.check_answers items (ingest), due_captures; review.py rulings.
- Code: citation.parse (header citations), trace register --keys (trace._nfc), upward.key_nodes.
- tools/check_subject.py, and so the MCP subject_check: key syntax, task keys against the yield.
Tests: tests/test_key_nfc.py, a subject copy whose C4 document names société, adresse and entrepôt, NFD under NFC keys and the reverse, through check_subject, the gate on rdflib and the MCP reader over stdio; société|adresse through the rule, a citation and a capture. The containers mapper yields société|uses:adresse, not société|adresse. Mapper-dependent tests skip without PyYAML, the rdflib one without rdflib.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Keys are compared, stored and reported in Unicode NFC wherever they enter (decision-0034 A2). key_rule.normalise and normalise_all, is_key validating after normalising; DESCRIPTION, the docstring, instance/README.md (with git config core.precomposeunicode true for macOS) and a CHANGELOG contract line say canonically equivalent keys are one key. Every public key is ASCII and unchanged; both comparators show 0 differing leaves, the record held. PR #446.
<!-- SECTION:FINAL_SUMMARY:END -->
