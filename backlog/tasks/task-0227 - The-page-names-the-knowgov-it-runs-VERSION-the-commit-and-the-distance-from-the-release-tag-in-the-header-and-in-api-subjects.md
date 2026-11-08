---
id: TASK-0227
title: >-
  The page names the knowgov it runs: VERSION, the commit and the distance from
  the release tag, in the header and in /api/subjects
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T16:51:00Z'
updated_date: '2026-11-08T17:22:00Z'
labels:
  - page
  - adopter
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 227000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08, asking why the page shows no knowgov version, then "yes" to building it.

Today the page shows the register's version (the register panel's heading: tag, or describe, or commit) but nothing of knowgov's own. demo/app/server.py sends only the HTTP Server header kg-demo/1. On the EC2 route the stack builds knowgov:local from the checkout (demo/docker-compose.override.yml), so the page runs whatever commit was last pulled, while VERSION reads 0.8.0 until the next release PR: on 2026-11-08 the maintainer's instance was at v0.8.0-277-g7e113f0. A version alone would therefore mislead; the page must name the commit too.

What to show: knowgov's VERSION, the build's commit (short), and its distance from the release tag when known, for example 'knowgov 0.8.0 + 277 (7e113f0)' from a checkout build, or 'knowgov 0.8.0 (v0.8.0)' from the release image. A part that cannot be known reads unknown, never a guess (a release image built without tags, a copy without .git).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The page header shows knowgov's VERSION and the build's commit, with the distance from the release tag when known; a part not known reads unknown, never inferred
- [x] #2 GET /api/subjects gains an additive knowgov object (version, commit, describe), each null when unknown; nothing else in the response changes
- [x] #3 The identity is read once at server start from the image's own files (VERSION; .git where the build copied it, or a value the Dockerfile records at build); no network, no wall clock, standard library
- [x] #4 It reads right in three cases, each with a test or a recorded check: a local build from a checkout (the override's knowgov:local), the published release image (or what the next release image will carry, if 0.8.0's cannot), and the page run from a checkout without Docker
- [x] #5 demo/README.md says where the page shows it and how to compare it with git -C ~/knowgov describe --tags --always; CHANGELOG under Unreleased > Changes; the record, the pins and the images' pins are unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/build_identity.py: identity(root) -> {version, commit, describe}; VERSION, then .knowgov-build.json, then git (refusing an enclosing repository), then .git's HEAD/refs/packed-refs; checked() keeps a describe only when it names a tag and agrees with the commit.
2. server.KNOWGOV read once at start; /api/subjects gains knowgov additively (also the no-subject reply).
3. index.html knowgovLabel()/knowgovChip() in the header chips.
4. Build: Dockerfile ARGs KG_BUILD_COMMIT/KG_BUILD_DESCRIBE written in a last layer; Dockerfile.dockerignore lets in .git/HEAD, refs, packed-refs only; release.yml build-args; override passes the args.
5. Tests (three cases, label in node), the stack job's assertion, README, security.md, CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Local runs: run_tests stdlib 784/825, 0 failed; bare venv without yaml 778/825, 0 failed; with the pins (KG_TEST_REQUIRE=rdflib,node,openai) 824/825, 0 failed. Comparator on rdflib: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. check_saved_queries not run locally (no store; the saved queries are untouched; the stack job runs it). AC #4: the release-image case and the checkout-without-Docker case are proven by tests/test_build_identity.py; the local-image case (knowgov:local through the override) is proven by demo.yml's stack job on PR #375, which asserts /api/subjects' knowgov.commit equals the checkout's HEAD, version equals VERSION and describe is null; that run is also the first proof of Dockerfile.dockerignore's exceptions under BuildKit (no Docker daemon in this session). The PR merges only on that job's green. The image carries the checkout's ref names, no history and no objects (coordinator's word; docs/security.md says so). Merged origin/main at f2634d7 into the branch: CHANGELOG keeps task-0205's line and this one.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page names the knowgov it runs. harness/build_identity.py reads {version, commit, describe} once at the server's start from the running copy's own files: VERSION; a record the image build writes from the optional build args KG_BUILD_COMMIT and KG_BUILD_DESCRIBE (release.yml passes the tag's commit and the tag; the override passes them through); git itself in a checkout, refusing an enclosing repository; else .git's HEAD, refs and packed-refs, which Dockerfile.dockerignore now lets into the image (ref names and hashes, no history, no objects). A describe stands only when it names a tag and agrees with the commit, so a bare hash or a stale export reads unknown. GET /api/subjects gains knowgov additively; the header chip reads e.g. 'knowgov 0.8.0 + 277 (7e113f0)', 'knowgov 0.8.0 (v0.8.0)' or '(7e113f0, distance from the release unknown)'. Proven by tests/test_build_identity.py (the release image and a checkout without Docker) and demo.yml's stack job (the local image). demo/README.md shows how to compare the chip with git describe; docs/security.md names what the image carries; CHANGELOG under Unreleased > Changes. The record, the pins and the images' pins are unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
