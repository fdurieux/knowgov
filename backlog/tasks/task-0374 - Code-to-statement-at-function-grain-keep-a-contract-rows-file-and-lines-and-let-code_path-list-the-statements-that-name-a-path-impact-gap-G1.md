---
id: TASK-0374
title: >-
  Code to statement at function grain: keep a contract row's file and lines, and
  let code_path list the statements that name a path (impact gap G1)
status: To Do
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-18T07:55:00Z'
labels:
  - impact
  - reverse-engineering
  - contract
dependencies: []
priority: medium
ordinal: 363000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G1.

A reverse-engineered kit names each function's file and lines in its contracts, but the contracts mapper keeps only elaborated_by, so that join never reaches the store. Code that cannot carry a header citation (code the instance may not write to) then reaches every key of its application through `code_map.toml`. Today `code_map.toml` maps paths by glob and `harness/citation.py` reads a header comment line: neither parses the code.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 the contracts mapper keeps a row's file and line range as a fragment of the statements it cites
- [ ] #2 code_path (and upward.py code) lists the statements whose fragments name the path, with the ranges, beside the cited keys
- [ ] #3 who_knows --path may scope by those statements (with the G5 task)
- [ ] #4 a test on a public fixture; the scored records unchanged or re-recorded with every moved leaf accounted for; CHANGELOG line under Contract changes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Order of build (the maintainer, 2026-11-18: "yes, add that note to task-0374; add the parsing layer as a note to task-0374: python parsing, R parsing, and Java parsing").

First layer, no parsing: the kit's function names with their file and line ranges, as the contracts give them. The fragment also keeps the cited file's sha256 as the kit read it, so when the file's bytes differ the walk still answers and flags the ranges as possibly moved (a finding), never silently wrong.

Second layer, optional, a parser per language that resolves a named function to its current line range, so a statement follows its function when the code above it moves, and drift can say which function changed rather than which file:
- Python: the standard library's ast (FunctionDef, AsyncFunctionDef and ClassDef with lineno and end_lineno). No new dependency; first.
- R: no parser in Python's standard library. Either R itself (utils::getParseData through Rscript, where the instance has R) or a tree-sitter grammar for R. Either one is a new dependency, so it needs a decision record before the build.
- Java: no parser in Python's standard library either. Either a pure-Python parser such as javalang, or a tree-sitter grammar for Java, or the JDK's own tooling where a JDK is installed. Again a new dependency, so a decision record first.

Each parser is used only when present. Where none is available the first layer's ranges and digest check stand, and the report says which layer answered. One tree-sitter route could serve R and Java together. The decision should weigh it against a per-language runtime: tree-sitter means one dependency with grammars pinned per language, while Rscript or a JDK means no Python dependency but needs that runtime in the image.
<!-- SECTION:NOTES:END -->
