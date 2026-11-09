---
id: TASK-0245
title: >-
  No .env file enters the image: the build context excludes every .env, and the
  compose guidance matches (R4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T08:15:00Z'
labels:
  - security
  - demo
dependencies: []
priority: medium
ordinal: 239000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
R4 of the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). demo/Dockerfile copies the repository (COPY . /repo) and demo/Dockerfile.dockerignore has no .env rule, while demo/docker-compose.yml:11 invites a .env beside the compose file, inside the build context: a key written there is baked into a locally built image. The release image is built from a clean checkout. Exclude **/.env and **/.env.* (an .env.example, if one is added, stays allowed), hold the rule with a test that builds the context list from the ignore file, and make the compose comment say the file is read for interpolation and never copied into the image.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 demo/Dockerfile.dockerignore excludes .env and .env.* at the root and nested; a test holds it, as tests/test_demo.py holds the Dockerfile
- [x] #2 demo/docker-compose.yml's comment and docs/security.md agree on where a key may live and that a .env never reaches the image
- [x] #3 CHANGELOG Unreleased › Changes names it under security
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. demo/Dockerfile.dockerignore: exclude .env, .env.*, **/.env, **/.env.*; re-include .env.example and **/.env.example.
2. tests/test_demo.py: read the ignore file's rules (last match wins, ! re-includes, **/ at any depth including the root) and hold every .env path excluded and .env.example kept.
3. demo/docker-compose.yml's variables comment and a docs/security.md data-flow row: compose reads a .env beside the compose file to fill in variables, and it never reaches the image.
4. CHANGELOG Unreleased › Changes, under security.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
demo/Dockerfile.dockerignore: .env, .env.*, **/.env, **/.env.* out; !.env.example and !**/.env.example back in. The rules are written at the root and with **/ because the context is the repository (COPY . /repo).
tests/test_demo.py::test_no_env_file_reaches_the_image applies the ignore file's rules with a small matcher: last match wins, ! re-includes, **/ matches at any depth including the root, by fnmatch. It holds .env, .env.local, demo/.env, subjects/x/.env and instance/ci/.env.prod excluded, and .env.example, demo/.env.example and README.md kept. It also holds the compose comment and the security.md row to their texts. Without the new rules it fails.
demo/docker-compose.yml:11: compose reads the .env only to fill in the variables below, and it never reaches the image. docs/security.md has a new data-flow row after the key row, naming the shell as the key's owner, the two files, and the test.
Checks: run_tests 903/904 (1 skipped) on the pins, the same with KG_PAGE_LISTEN=0.0.0.0, and 848/904 (56 skipped) bare. Both deterministic comparators: 0 differing leaves (CargoQuote 7 scenarios, J-F 6). check_round_trip --chain rdflib,rdflib on CargoQuote: every answer survives.

Rerun on the merged tree at c267461, which brings in #398 and #399's two new tests: run_tests 905/906 (1 skipped) on the pins, both unset and with KG_PAGE_LISTEN=0.0.0.0, and 850/906 (56 skipped) bare. Deterministic comparators: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. check_round_trip --chain rdflib,rdflib on CargoQuote: every answer survives.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
No .env file reaches a locally built image any more. demo/Dockerfile.dockerignore leaves out every .env and .env.*, at the root and in any folder, and lets back in only a values-free .env.example. tests/test_demo.py::test_no_env_file_reaches_the_image holds the rule by applying the ignore file to sample paths. demo/docker-compose.yml's comment and a new docs/security.md data-flow row agree: compose reads a .env beside the compose file only to fill in the variables, and the file never reaches the image. The CHANGELOG line is under Unreleased › Changes, marked security. The release image was already built from a clean checkout, so no published image changes. The suite is green on the pins and bare, and both comparators show 0 differences.
<!-- SECTION:FINAL_SUMMARY:END -->
