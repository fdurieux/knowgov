---
id: TASK-0297
title: >-
  The key rule refuses every control and format character, listed so ECMA-262
  and Python read it alike (decision-0034 A1)
status: Done
assignee: []
created_date: '2026-11-09T19:01:00Z'
updated_date: '2026-11-09T19:59:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - task-0296
  - task-0256
priority: high
ordinal: 290000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 Amendment A1, accepted 2026-11-09 ("K1 (a) as advised"). Found by the spot check's re-check of task-0296 at main 946c72e, and confirmed by the coordinator.

- K1: these pass `harness/key_rule.py` on every surface (`gate_verdict`, `evidence_bundle`, `check_subject`) and read as absent at the gate: U+200E (LRM), U+202E (RLO, a bidi override), U+00AD (soft hyphen), U+2061, U+180E and NUL.
- K2: Python's str `\s` matches U+001C to U+001F and U+0085, but ECMA-262's does not. So a JavaScript client validating the inputSchema accepts `thing\x1c|property`, which the server refuses with -32602.

The rule: each side of the `|` is non-empty and holds no `|`, no whitespace and no character of general category Cc or Cf, every class listed as `\uXXXX` ranges with no `\s`, `\d` or `\w`. Combining marks (Mn, such as U+034F) stay allowed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `SIDE` refuses `|`, every whitespace character and every Cc and Cf code point, listed explicitly; `PATTERN` holds no `\s`, `\d` or `\w`.
- [x] #2 A test generates every Cc and Cf code point and every whitespace character from `unicodedata` and holds the pattern to refuse each, and holds a combining mark accepted.
- [x] #3 `gate_verdict` and `evidence_bundle` answer -32602 for an RLO key over stdio and HTTP, held by `check_mcp_server`; `check_subject` reports it as `key-syntax`.
- [x] #4 `DESCRIPTION` and the docstring state the rule; every public key still matches, and the record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the widened rule under Contract changes.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
decision-0034 A1's reach above U+FFFF, accepted 2026-11-09 ('astral (a) as advised'): the pattern is a positive list of BMP ranges, so every astral character is refused, the 127 astral Cc and Cf code points among them. 0.9.0's Known limits name it: keys use characters up to U+FFFF.

Built on claude/task-0297-key-controls (PR #444), from main 946c72e. harness/key_rule.py: ALLOWED is the BMP less Cc, Cf, Zs, Zl, Zp, Cs and |, as 20 explicit \uXXXX ranges generated from Unicode 15.1 (CPython 3.13); SIDE = [ALLOWED]+; PATTERN anchored, no \s, \d or \w, so ECMA-262 and Python read it alike; REFUSED_CATEGORIES; DESCRIPTION and the docstring state the rule and that keys use characters up to U+FFFF only (the maintainer, 'astral (a) as advised', decision-0034: a positive BMP list refuses every astral character alike in Python, in ECMA-262 reading UTF-16 units and under the u flag, which a refused-list class could not do for the 127 astral Cc/Cf code points); the source is ASCII. Now refused: U+200E, U+202E, U+00AD, U+2061, U+180E, NUL, U+001C to U+001F, U+0085; combining marks (U+034F, NFD names) kept. tools/check_subject.py's key-syntax message names the rule; tools/check_mcp_server.py's transport checks hold gate_verdict with an RLO key at -32602 on stdio and HTTP. instance/README.md and subjects/README.md state the rule. Tests (tests/test_key_rule.py, 8): every Cc, Cf, Zs, Zl, Zp code point and every str.isspace() character from unicodedata, beyond the BMP too, refused on either side by is_key and the schema; nothing in ALLOWED in a refused category; a combining mark and NFD names accepted; the pattern free of \s, \d and \w, its only escapes \u and \|, astral keys refused read as UTF-16 units; check_subject's key-syntax for an RLO key; BAD adds every case. Local, CPython 3.13 with rdflib, at a718f67: run_tests 1007/1061 (54 skipped) default and 1006/1061 (55 skipped) J-F, 0 failed; check_mcp_server --scenarios S1,S2,S6 every check holds; the CQ comparator 0 differing leaves: the record held; complexity holds (180); at 6620e6a (wording and docs) both suites again 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The key rule refuses every control and format character, and reads alike in ECMA-262 and Python: each side of the | holds only characters up to U+FFFF outside Unicode categories Cc, Cf, Zs, Zl, Zp and Cs, written as explicit \uXXXX ranges with no \s, so a JavaScript client and the server agree. The bidi marks and overrides, the soft hyphen, U+2061, U+180E, NUL and U+001C to U+001F, U+0085 are now -32602 on the wire and a key-syntax error in check_subject; combining marks are kept; every character above U+FFFF is refused (decision-0034, 'astral (a) as advised'). A test refuses every Cc and Cf code point the interpreter's Unicode tables name, so a new Unicode version cannot open a gap unseen. Every public key matches; the record does not move.
<!-- SECTION:FINAL_SUMMARY:END -->
