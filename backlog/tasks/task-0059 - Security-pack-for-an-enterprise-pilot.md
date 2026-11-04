---
id: TASK-0059
title: Security pack for an enterprise pilot
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-04T03:16:00Z'
labels:
  - lighthouse
  - security
milestone: m-8
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: medium
type: docs
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A regulated organisation's procurement asks for a security description before a pilot touches its systems (doc-0012 §6, OpenAI's review). The facts exist but are spread: the read-only mount, the localhost rule, the model endpoint off by default, the store holding status and provenance never content, the private instance never pushed out. A reviewer must be able to read them in one place and check each against the code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One adopter-register document lists the data flows of a private instance (what is read, stored, sent and to where), each with the file or setting that enforces it
- [x] #2 It states what leaves the client's network under each model-endpoint setting, including none
- [x] #3 It lists the dependencies and image pins with how they are kept current, and how to report a vulnerability
- [x] #4 Every claim in it is checked by an existing or new test, or marked as a practice the operator must follow
- [x] #5 A permission matrix: who may read, propose, approve, close, edit the model, or execute a business action (nobody), per actor (model, agent over MCP, pipeline, person by role, register approver), each enforceable row citing its test (doc-0013 P7)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Map every security fact to the file that enforces it and the test that holds it (mcp_server, arms, transcript, load/store port, capture/review, compose, Dockerfile, CI pins).
2. docs/security.md (adopter register): parts, data flows (read/stored/sent) with enforcing file and evidence, what leaves the network per model-endpoint setting, pins and how they move, permission matrix with evidence per row, gaps, operator practices.
3. SECURITY.md: private vulnerability reporting.
4. tests/test_security.py (stdlib): every cited test exists, every row names its evidence or Practice, the matrix's actors/actions and nobody executes; new holds for claims nothing held (digest-not-text, no outbound client but the model's and the store's, runs/ ignored, baseline arm sends whole documents); the gaps are still the code's, so a fix fails until the document follows.
5. Point lighthouse-evaluation and README to it; run the suite on both subjects.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Found and stated as gaps, not fixed (stack paths; proposed under NEXT): the page, Neo4j Browser and bolt are published on every interface, the page has no login and can start a run (POST /api/run) that calls the model; Neo4j's default password kgpoc2026; the gives role is never checked (capture.check_answers checks issued/withdrawn only); no Dependabot/Renovate; python:3.12-slim, neo4j:5.26-community, knowgov:latest and actions/setup-python@v6, setup-node@v6 pinned by tag only. Corrected the brief's premise: the store holds excerpts (fragment text) and statement values, not whole documents; the doc says so. The arms send whole documents (baseline) and bundles with named documents verbatim (governed); the transcript route sends the transcript and keeps only its digest. Local: run_tests.py 268/268 plain and with KG_SUBJECT=subjects/jef_data_load.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
docs/security.md is the security description a procurement reviewer reads: data flows with enforcing files and evidence, egress per model-endpoint setting (none without a key or with a private endpoint), pins and how they move, and the permission matrix (model, agent over MCP, pipeline, person by role, register approver, plus anyone reaching the page; nobody executes a business action). SECURITY.md gives private vulnerability reporting. tests/test_security.py (10 tests, stdlib) holds every citation to a real test, adds the holds that were missing, and fails when a named gap is fixed until the document follows. Five gaps stated plainly rather than claimed: ports on every interface with no page login and a default Neo4j password; gives unchecked; no automated dependency updates; tag-only pins on three images and two actions; the store holds excerpts. Verified: 268/268 on both subjects.
<!-- SECTION:FINAL_SUMMARY:END -->
