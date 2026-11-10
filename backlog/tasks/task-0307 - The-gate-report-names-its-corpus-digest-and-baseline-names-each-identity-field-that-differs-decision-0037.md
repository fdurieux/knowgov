---
id: TASK-0307
title: >-
  The gate report names its corpus digest, and --baseline names each identity
  field that differs (decision-0037)
status: Done
assignee: []
created_date: '2026-11-09T21:39:00Z'
updated_date: '2026-11-09T22:45:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0037
  - backlog/decisions/decision-0029
  - backlog/docs/doc-0037
priority: high
ordinal: 300000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0037, accepted 2026-11-09 ("§3.3 (a)", doc-0037 §3.3). Found by the functional review, group A (F2, F3), at main f194aac.

- F2: gate-report v3 names `task_profile`, `register` and `knowgov`, but not the corpus. After an in-place edit of decision_table.md (P2's threshold changed from 1244 to 1300), all four are identical to the pristine S1 report's; only the verdict, why, findings and levels differ.
- F3: take the S1 report and edit its `task_profile` to 0×64, `register.tag` to v0.1.0, `knowgov.version` to 0.5.0 and `as_of` to 2020-01-01. `gate_cli.py --scenario S1 --as-of record --baseline that.json` then gives "no regression", exit 0, and says nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The gate report's identity carries `corpus`: sha256 over the loaded document Versions' digests in a stated, deterministic order. The gate-report schema and decision-0029's documentation describe it, and it is equal on both stores and through the round trip.
- [x] #2 `--baseline FILE` and `--baseline record` name on stderr each identity field that differs from the baseline's (`task_profile`, `register`, `knowgov`, `corpus`, `as_of`). The exit is unchanged; a baseline without a field reads that field as unknown, never as different.
- [x] #3 F3's repro prints each changed field; F2's edit changes `corpus`; the pristine run's `corpus` is stable across runs and stores.
- [x] #4 `check_round_trip` and `check_mcp_server` hold the field; the comparator ignores it; the record does not move.
- [x] #5 A CHANGELOG line names it under Contract changes.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built on branch claude/task-0307-corpus-identity (decision-0037, doc-0037 §3.3 (a)).

- The gate report gains `corpus`: the sha256, hex, of one UTF-8 line per loaded document Version, `<artefact>\t<version>\t<sha256>\n`, sorted by artefact then version, every Version counted (`store.corpus_digest`, port read `version_digests` on both adapters, in `store.READS` and the MCP reader's READS). It is additive under schema version 3, not required, so earlier v3 reports validate. The schema, `gate_cli`'s docstring, CLAUDE.md and instance/README.md describe it.
- `--baseline FILE`/`record` names on stderr each of `task_profile`, `register`, `knowgov`, `corpus`, `as_of` that differs (`identity_drift`). The exit is unchanged. A field missing or null (an object of nulls) reads as unknown. A deterministic.json holds only the subject's `[record] as_of`.
- `tests/test_corpus_identity.py`: F3's repro names the four edited fields, exit 0; F2's in-place edit of decision_table.md (1244 to 1300) moves only `corpus`; a pristine corpus is stable across runs; a baseline without `corpus` names nothing; the record's baseline names only a different `as_of`.
- `check_round_trip` requires the field and holds it across hops; S1's corpus `46cb05dd…` is equal on rdflib and through neo4j→rdflib→neo4j. `check_mcp_server` holds gate_verdict's corpus to the load's and to gate_cli's.
- Verified: both comparators (CargoQuote 7 scenarios, J-F 6) 0 differing leaves; the round trips, the MCP checks, check_gate_after_change and check_register_change all exit 0; the suite 1064/1065 (1 skipped), stdlib-only 1009/1065 (56 skipped), 0 failed; the complexity ratchet holds. The record does not move.
- CHANGELOG Unreleased › Contract changes names it.
- decision-0029's record itself was not edited (the CLI changes only a decision's status); decision-0037 records the extension.
<!-- SECTION:FINAL_SUMMARY:END -->
