---
id: TASK-0149
title: >-
  check_subject tells a person what misleads them today: zero yield, short, one
  did-you-mean per key (doc-0021 B1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:46:00Z'
updated_date: '2026-11-05T22:56:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 156000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0021's probe found three silent or misleading outcomes in tools/check_subject.py: a document a mapper reads at zero yield raises no finding (G1); one yielded key is offered as the did-you-mean of two required keys, once for a different requirement (G2); an artefact without short fails with a KeyError blamed on the document (G5). Each misleads a person working by hand today and forces a workaround into task-0148's prompt. Maintainer's go, 2026-11-05.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A document a set mapper reads at zero yield is a WARNING naming the mapper and its input convention
- [x] #2 An artefact with a mapper and no short is refused with the right fix named, or defaulted, never a KeyError blamed on the document
- [x] #3 A yielded key is offered once, to its best match; a match on a different entity is a NOTE, not a did-you-mean; tools/fixtures/subject_probe and both public subjects hold, the schema version moves if the report shape does
- [x] #4 The matching workarounds leave task-0148's prompt text in the same PR if 0148 has landed; CHANGELOG Unreleased carries the layout refusal
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR fdurieux/knowgov#248: G5 refused with the stem as fix; G1 zero-yield WARNING from the new instance/mappers.toml naming the kind's other mappers; G2 best-match assignment, another entity a NOTE. Schema version 1, rule zero-yield added (shape unchanged). AC #4: task-0148 has not landed; its workarounds drop in #245.

Merged as fdurieux/knowgov#248 on a fully green matrix. Evidence: three tests in tests/test_check_subject.py on doc-0021's renewal probe (RNW ids: zero-yield naming '| REQ-nn | text |' and requirements_json; no short: refused with the stem, no mapper-failed; REQ-03|text offered to REQ-03|txt only, REQ-04|text a NOTE naming another entity's key); subject_probe, cargo_quote, jef_data_load, minimal hold; schema version 1, rule zero-yield added (shape unchanged). AC #4: task-0148 had not landed; its workarounds leave in #245, and CHANGELOG Unreleased carries the refusal.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
`tools/check_subject.py` stops misleading a person: a mapped artefact without `short` is refused with its stem as the fix, never a KeyError blamed on the document (G5); a document its mapper yields nothing from is a `zero-yield` WARNING naming what the mapper reads (the new `instance/mappers.toml`) and the kind's other mappers (G1); each yielded key is offered once, to its best match, and a match on another entity is a NOTE (G2). Merged as #248.
<!-- SECTION:FINAL_SUMMARY:END -->
