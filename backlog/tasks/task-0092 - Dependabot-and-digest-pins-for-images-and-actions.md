---
id: TASK-0092
title: Dependabot and digest pins for images and actions
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T03:18:00Z'
updated_date: '2026-11-04T03:35:00Z'
labels:
  - security
  - ci
milestone: m-8
dependencies:
  - TASK-0059
priority: medium
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0059: no automated dependency updates; python:3.12-slim, neo4j:5.26-community and knowgov:latest are pinned by tag, actions/setup-python@v6 and setup-node@v6 by tag, not by digest or SHA.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 .github/dependabot.yml covers pip, npm, docker and github-actions
- [x] #2 Base images and the compose image are pinned by digest, the remaining actions by SHA; a test holds the pins
- [x] #3 docs/security.md's pins section and gap list move with the fix
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pin every FROM and pulled image: as name:tag@sha256 (digests from the registry API, cross-checked with docker buildx imagetools): python:3.12-slim, neo4j:5.26-community, the app image as release v0.1.0 (coordinator accepted), the GitLab template's python:3.12.
2. Pin setup-python/setup-node by commit SHA with the version in a comment, in the workflows and instance/ci/preload-check.yml.
3. .github/dependabot.yml weekly: pip (demo/requirements.txt), npm (instance/ci/package.json), docker, docker-compose, github-actions; the pip/npm files are watch-lists held equal to the installing pins.
4. tests/test_pins.py (stdlib) holds every image to a digest, every uses: to a SHA, one pin per name, the watch-lists to the pins.
5. docs/security.md pins section and gaps; tests/test_security.py gap checks.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Digests resolved through the proxy by the registry API (auth.docker.io / ghcr.io token, HEAD on the index) and cross-checked with docker buildx imagetools inspect: python:3.12-slim b18b261e…, python:3.12 17b97244…, neo4j:5.26-community 249a1ec6…, ghcr.io/fdurieux/knowgov:v0.1.0 bcd27f59…. Action SHAs from git ls-remote (lightweight tags): setup-python v6 = v6.3.0 ece7cb06…, setup-node v6 = v6.5.0 24997072…. The app image names the release v0.1.0, not :latest (coordinator accepted): a digest-pinned :latest would freeze at one main and Dependabot would churn it every merge. Dependabot's pip and npm entries read watch-lists that install nothing (demo/requirements.txt, instance/ci/package.json), held equal to the installing pins; the record's pins in tests/test_demo.py are unchanged. Proof: removing one SHA or one digest fails tests/test_pins.py and test_security's gap check; run_tests 282/282 plain and with KG_SUBJECT=subjects/jef_data_load; docker compose config resolves the pinned images.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed task-0059's gaps 3 and 4. .github/dependabot.yml proposes weekly updates for pip, npm, docker, docker-compose and github-actions; pip and npm read watch-lists (demo/requirements.txt, instance/ci/package.json) held equal to the pins that install, so a proposal stays red until the pin moves everywhere. Every pulled image is name:tag@sha256 (the Dockerfile's base, Neo4j, the app image as release v0.1.0, LiteLLM, the GitLab template's python:3.12); every remote action is a full commit SHA with its version in a comment, one SHA per action across the workflows and instance/ci/preload-check.yml. tests/test_pins.py (stdlib) holds all of it; docs/security.md's pins section names it and the gap list drops the two closed gaps; test_security's check holds them closed. The demo README says a build runs the checkout and a pull the named release. Risk: the compose app image no longer follows main; the 0.2.0 release PR moves it.
<!-- SECTION:FINAL_SUMMARY:END -->
