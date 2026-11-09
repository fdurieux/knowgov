---
id: TASK-0296
title: >-
  One entity|attribute key rule in check_subject's KEY_RE and the inputSchema of
  gate_verdict and evidence_bundle, Unicode format characters refused
  (decision-0034 choice 3)
status: Done
assignee: []
created_date: '2026-11-09T16:51:00Z'
updated_date: '2026-11-09T17:22:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 289000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 (accepted 2026-11-09, "N7, D1, D3 as advised") choice 3(a). Found by the spot check (GV-1, CS-4) at 9861953.

- `gate_verdict {"keys":["nonsense"]}` is answered as BLOCKED, "nonsense (absent)", though the description says `entity|attribute` and `check_subject`'s `KEY_RE` refuses it. `keys:[""]` is already refused.
- `evidence_bundle` takes `keys` the same way.
- `KEY_RE`'s `\s` misses a zero-width space: `thing\u200b|property` passes the checker and reads absent at the gate.

One rule: each side of the `|` is non-empty and holds no `|`, no whitespace and no format character (`\u200b` to `\u200d`, `\u2060`, `\ufeff`). task-0265's CS-4 item moves here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `tools/check_subject.py`'s `KEY_RE` and the `keys` items of `gate_verdict` and `evidence_bundle` carry the same pattern, held equal by a test.
- [x] #2 `gate_verdict` and `evidence_bundle` answer -32602 for a key outside it, over stdio and HTTP, in both eras; `check_mcp_server.py` holds one such call.
- [x] #3 A key holding a zero-width space or another listed format character is an error in `check_subject` and -32602 on the wire.
- [x] #4 Every key in the public subjects and the record matches, and the record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the pattern under Contract changes.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on claude/task-0296-key-rule (PR #440). harness/key_rule.py holds the rule: SIDE = [^|\s\u200b-\u200d\u2060\ufeff]+ written as escapes (the source carries no invisible character, held by a test), PATTERN the anchored JSON Schema pattern read alike by Python and ECMA-262, KEY_RE its body compiled for fullmatch, is_key, DESCRIPTION. tools/check_subject.py's KEY_RE is key_rule.KEY_RE (its key-syntax message names the invisible format characters); mcp_server.KEY_ITEM carries PATTERN as the items of gate_verdict's and evidence_bundle's keys, so task-0281's argument_refusal answers -32602 naming keys[0] before dispatch, on stdio and HTTP, in both eras. tools/check_mcp_server.py's check_transports holds gate_verdict {keys: [nonsense]} and evidence_bundle with a zero-width space as -32602 on stdio and HTTP. tests/test_key_rule.py (6): one pattern by identity and text; the rule and the schema agree on 7 good and 15 bad keys; check_subject's key-syntax error; -32602 on stdio and HTTP in both eras for both tools; every key in the public subjects' task classes, register maps and the record's gate_keys matches (over 400); the changelog line. Local, CPython 3.13 with rdflib, on main merged at 34076aa: run_tests 981/1034 (53 skipped) default and 980/1034 (54 skipped) J-F, 0 failed; check_mcp_server --scenarios S1,S2,S6 every check holds; the CQ comparator 0 differing leaves: the record held; complexity --check holds (180).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
One rule for a knowledge key, entity|attribute: each side of the | non-empty, with no |, no whitespace and no format character (U+200B to U+200D, U+2060, U+FEFF), held in harness/key_rule.py. check_subject's KEY_RE is it, and the keys items of gate_verdict and evidence_bundle carry it as their pattern, so keys ["nonsense"] or a key with a zero-width space is -32602 before dispatch on both transports and both eras, and a key-syntax error in check_subject. check_mcp_server holds two such calls. Every key in the public subjects and the record matches; the record does not move. decision-0034 choice 3(a); CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
