---
id: TASK-0230
title: >-
  The adopter-docs pass: every adopter-facing claim held against the code, a
  docs gate test, and the contracts at 1.0 in instance/README.md (doc-0028 G9-9,
  P2, P4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T19:36:00Z'
updated_date: '2026-11-08T20:51:00Z'
labels:
  - docs
  - release
  - contract
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0028 -
    What-a-knowgov-0.9-and-1.0-need-the-record-is-silent-the-version-arithmetic-the-contract-surface-the-gap-lists-proposed.md
priority: high
ordinal: 229000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0028 G9-9 is the last work item before the 0.9.0 cut besides G9-2. #291 fixed two stale claims, but the pass holding every adopter-facing claim against the code (P2) had not run: only docs/reverse-engineering.md was held, by tests/test_reverse_engineering_guide.py. A 0.9.0 that freezes contracts (decision-0016) needs its adopter docs to state the real commands, flags, KG_* settings, paths, endpoints, exit codes, pins and counts. decision-0016 point 3 makes the KG_* settings that instance/README.md or docs/security.md documents, and the page HTTP API as demo/README.md documents it, contracts at 1.0, so a stale doc there is a stale contract. P4: instance/README.md states the contracts at 1.0 in the adopter register. Dispatched by the coordinating session on the maintainer (2026-11-08 19:30Z: "dispatch task-0174 and the docs pass"). Scope: README.md, demo/README.md, instance/README.md, subjects/README.md, docs/guide.md, docs/security.md, docs/reverse-engineering.md, docs/reverse-engineering-preregistration.md, docs/lighthouse-evaluation.md; not CLAUDE.md or the backlog. Limits: no code behaviour change, no pin moved. A KG_* setting the code reads and no doc names is listed for the maintainer, not documented, because documenting it would make it a 1.0 contract. A docs-right, code-wrong finding, or a fix that would change a documented contract, is reported, not made.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every command, --flag, KG_* variable, repository path, HTTP endpoint, exit code, pinned version and stated count in the nine docs is held against main code, and each stale claim found is fixed
- [x] #2 A stdlib test holds every --flag the docs name to an option of a parser under harness/, tools/ or demo/tools/, every KG_* to a read in code and every repository path to one that exists, with foreign flags in a named allow-list; it fails on main before the fixes
- [x] #3 instance/README.md has a short section stating the contracts at 1.0 in the adopter register, quoting decision-0016 point 3 without widening it
- [x] #4 KG_* settings read in code and named by no doc are listed for the maintainer, not documented
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tests/test_adopter_docs.py, stdlib, the code read as text. It holds each of the nine docs to main:
   - every --flag to a parser option under harness/, tools/, demo/tools/, demo/app/, instance/ or the vendored register's tools, or to FOREIGN_FLAGS with its owner;
   - each fenced python command's options to that program's own add_argument;
   - every KG_* name to a read in code;
   - every repository path and relative link, from the root or the doc's folder, to one that exists, and every tests/x.py::name to a test of that file;
   - every /api route to one demo/app/server.py serves.
   Foreign entries are listed with their owner, and one no doc names any more fails. Run on main first: 4 stale claims and 17 foreign flags.
2. Fix what it catches: demo/README's tools/impact.py (x2, the register's tool), its two-walks claim (the page offers two of the register's three; thread is command-line only), the record path missing vendor/, security.md's /api/gaps.
3. Semantic claims (counts, exit codes, defaults, fields, versions, test references, behaviour) are reviewed by three read-only reviewers on a frozen main worktree; each finding is verified against the code before a fix.
4. P4: instance/README.md's last section quotes decision-0016 point 3 verbatim, with a plain-English table of where each is described. Format versions are named as not yet built.
5. DECIDE, not documented: the KG_* read in code and named by no doc, and those named only in demo/README.md (not 1.0 contracts as point 3 reads).
6. CHANGELOG under Unreleased, Changes; suites stdlib, bare and pins.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Run on main 76e1e04 first, tests/test_adopter_docs.py failed on four stale claims:
- demo/README tools/impact.py (x2);
- the record path missing vendor/;
- security.md /api/gaps.
Seventeen flags turned out foreign and are listed with their owners (git, docker compose, ssh-add, xcode-select, pumllint trace), plus four foreign paths (pumllint's two docs, the register's tools/reconcile.py, MCP's tools/call). The vendored register's tools count as parsers.
Three read-only reviewers then covered the semantic claims on a frozen main worktree:
- demo/README: 17, plus 3 slips within the page;
- instance/README: 8, plus one could-not-settle checked here (fifteen manifest tables, not sixteen);
- guide, security, lighthouse, subjects: 20.
Each finding was verified against the code before its fix:
- impact.py run from APP-0002, PROC-0004, JRN-0001, PROC-0006, CAP-0002 and ENT-0003;
- the comparator on the record (117 leaves);
- mcp_server's TOOLS imported (17; list_subjects alone without subject);
- lifecycle.toml's review months;
- gate_cli's exit codes;
- http_boundary's 421;
- armsReady and execution.refusal;
- SAVED_QUERIES (12).
My own docs/reverse-engineering.md step 4 was stale too: task-0217's three cross-document checks are built.
No KG_* is newly named in instance/README.md or docs/security.md (checked against main), so no contract is widened. A KG_NO_LOAD mention was reworded away for that reason.
Not changed, for the maintainer:
(a) KG_* read in code and named by no adopter doc (28):
  - tools and tests internal: KG_MUTANT, KG_ROOT, KG_NOW, KG_TRACEBACK, KG_OUTCOMES, KG_DEMO_URL;
  - CI-template inputs: KG_TASK, KG_STAGE, KG_NO_LOAD, KG_GATE, KG_CODE_REPO, KG_SUBJECT_IN;
  - the hook: KG_HOME;
  - the page and stack: KG_DEMO_PORT, KG_DEMO_RUNS, KG_PAGE_LISTEN, KG_WORKERS, KG_WORKER_CPUS, KG_WORKER_MEM, KG_WORKER_JOBS, KG_WORKER_JOB_SECONDS, KG_WORKER_WORK;
  - the store: KG_NEO4J_URI, KG_NEO4J_USER;
  - the arms: KG_ARMS_EFFORT, KG_THINKING_UNCOUNTED, KG_AGENT_IDLE_SECONDS;
  - MCP: KG_SUBJECT_CALL_TIMEOUT.
(b) Named only in demo/README.md, so not 1.0 contracts as decision-0016 point 3 reads: KG_AGENT_MAX_CALLS, KG_AGENT_MAX_SECONDS, KG_AGENT_MAX_TOKENS, KG_ANTHROPIC_KEY, KG_ARMS_MAX_TOKENS, KG_ARMS_MODEL, KG_MODELS, KG_MODEL_API_KEY, KG_MODEL_API_KEY_VAR, KG_PORT_BOLT, KG_PORT_BROWSER.
(c) Docs right, code wrong:
  - the Browser link's bolt port is hard-coded 7687 (demo/app/server.py:356, index.html:366), so a second stack's links reach the first stack's Neo4j;
  - index.html:633 says deterministic creates no Derived node;
  - index.html:129's Arms note omits the worker;
  - mcp_server's instructions say every tool takes subject;
  - preload_check.py's docstring says one file at a time;
  - lighthouse_evidence.py's docstring says a summary per criterion;
  - test_pins' test name says four ecosystems where it asserts five.
(d) security.md rows whose cited tests prove less than the row claims: the neo4j-data volume (line 56), and the pipeline's gate never ruling (line 336).
(e) Could not settle:
  - bpmnlint's 97 errors, without bpmnlint;
  - Browser 5.26.0, timings and token figures;
  - the guide's Neo4j-only counts (15/15/10/8);
  - Claude Code 2.1.295.
Suites on this tree:
- pins: 861/862, 1 skip, 0 failed;
- bare 3.13: 808/862, 54 skips, 0 failed.

After merging main 615fa36 (#382, task-0174 format versions):
- the P4 table's format-version row now cites decision-0023 and task-0174 as built, quotes #382's three read rules and points to its "Format versions" section;
- which ieam-register format versions a register may be in is split out as not yet stated;
- #382 added [format] to check_subject's TABLES, so the manifest has sixteen top-level tables again, and the count is restored to sixteen;
- tests/test_adopter_docs.py passes on #382's text.
Suites on the merged tree:
- bare 3.13: 815/870, 55 skips;
- pins: 869/870, 1 skip.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The adopter-docs pass (doc-0028 G9-9, P2) and P4.
- tests/test_adopter_docs.py, stdlib, holds the nine adopter docs to the code. It checks every --flag, each fenced command's options, every KG_* name, every repository path, relative link and tests::name, and every /api route. Foreign flags and paths are listed with their owners. It failed on main first, on four stale claims.
- Over 45 further stale claims, each verified against the code before its fix:
  - demo/README: the bind needs KG_DEMO_HOST; compose pull fetches the pinned release; Arms needs the worker; five chips; twelve saved queries; six rules at a load; four services;
  - instance/README: seventeen MCP tools; the gate's private load (decision-0017); lint findings at the linter's severity; require_approved; who writes captures/;
  - docs/guide.md section 8, rewritten from the walk's own output (ten links from APP-0002; every node starts a walk);
  - security.md: the runs server; lighthouse: the closed gaps.
- instance/README.md ends with what stays stable from 1.0, quoting decision-0016 point 3 verbatim, in a plain-English table. Format versions are named as not yet built.
- No code, contract or pin changes, and no KG_* is newly documented where it would become a contract.
- For the maintainer: the undocumented KG_* settings, the code-side texts that are wrong where the docs are right (the hard-coded bolt port above all), and two security rows with weak evidence; the notes list each.
- Suites pass.
<!-- SECTION:FINAL_SUMMARY:END -->
