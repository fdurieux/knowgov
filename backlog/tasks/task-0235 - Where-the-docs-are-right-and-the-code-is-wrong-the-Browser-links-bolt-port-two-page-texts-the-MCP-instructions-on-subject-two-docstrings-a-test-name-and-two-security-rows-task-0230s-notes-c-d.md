---
id: TASK-0235
title: >-
  Where the docs are right and the code is wrong: the Browser link's bolt port,
  two page texts, the MCP instructions on subject, two docstrings, a test name
  and two security rows (task-0230's notes c, d)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T21:19:00Z'
updated_date: '2026-11-08T21:24:00Z'
labels:
  - page
  - mcp
  - docs
dependencies: []
priority: medium
type: bug
ordinal: 230000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0230's adopter docs pass (#384) listed, for the maintainer, the places where the docs are right and the code is wrong (its notes (c)) and two docs/security.md rows whose cited tests prove less than the row claims (notes (d)). Dispatched by the coordinating session, 2026-11-08. Fixes, not contract changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The store panel's Browser link and the impact guides' Browser links connect to the bolt port the stack publishes (KG_PORT_BOLT, passed to the app by docker-compose.yml), 7687 when unset; /api/store carries the link additively as browser_connect; a test
- [x] #2 index.html no longer says deterministic mode creates no Derived node, and its Arms note names the contained worker (--profile arms)
- [x] #3 The MCP reader's instructions say every tool but list_subjects takes subject, held against the tool table; check_mcp_server and check_transports green
- [x] #4 tools/preload_check.py's and tools/lighthouse_evidence.py's docstrings say what the tools do; test_pins' Dependabot test is named for the five ecosystems it holds, and docs/security.md cites the new name
- [x] #5 docs/security.md's neo4j-data row and its gate-never-rules row each cite a test that proves the claim (tests/test_docs_code_fixes.py)
- [x] #6 Each new test fails on main first; run_tests (stdlib, without yaml, pins), check_mcp_server and the page tests green; CHANGELOG under Unreleased > Changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. server.bolt_port(env)/BOLT_PORT from KG_PORT_BOLT once at start; browser_connect_url and browser_play_url use it; store_status carries browser_connect; compose passes KG_PORT_BOLT to the app; index.html uses s.browser_connect.
2. index.html: the Derived text and the Arms note.
3. mcp_server INSTRUCTIONS and its comment: every tool but list_subjects.
4. Docstrings, test_pins rename, security.md citation.
5. tests/test_docs_code_fixes.py: one test per finding, the two security rows' proofs; security.md rows cite them.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
All seven tests in tests/test_docs_code_fixes.py failed on main f7c37a5 first; for the gate row, the invariant already held (gate.py and gate_cli.py call no ruling write; ruling writes are load.py's, change.py's and rules.py's; --no-load opens a read handle) and the failure was the row citing tests that proved less; so both security rows are proven by a test, neither relabelled Practice. The neo4j-data row's test reads the compose file's volume mount and declaration and the rdflib adapter's in-memory default. Local: run_tests stdlib 827/875, bare venv without yaml 820/875, pins 874/875, each 0 failed; KG_STORE=rdflib check_mcp_server S1,S2,S6 (check_transports, stdio and HTTP) every check holds. The page tests (test_page_subject, test_register_view, test_arms_execution, test_build_identity) pass in each run. The stack job proves the Browser link on the real stack only as far as its own default port.

Coordinator, 2026-11-08: /api/store's browser_connect is an additive change to the page's HTTP API, a 1.0 contract under decision-0016 point 3 (as task-0227's /api/subjects field was), so it has its own CHANGELOG line under Unreleased > Contract changes; the rest stays under Changes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixed the code-side findings of task-0230's docs pass. The Browser links (the store panel's and the impact guides') connect to the bolt port the stack publishes, KG_PORT_BOLT, which docker-compose.yml now passes to the app, read once at start, 7687 by default; /api/store carries the link as browser_connect. The page's stage-2 text says when a Derived node is registered, and the Arms note names the contained worker. The MCP reader's instructions say every tool but list_subjects takes subject. preload_check.py's and lighthouse_evidence.py's docstrings match the tools; test_pins' Dependabot test is named for five ecosystems. docs/security.md's store-location row and gate-never-rules row each cite a test in tests/test_docs_code_fixes.py that proves the claim. CHANGELOG under Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
