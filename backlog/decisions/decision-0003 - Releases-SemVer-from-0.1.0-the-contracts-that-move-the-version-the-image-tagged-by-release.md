---
id: decision-0003
title: >-
  Releases: SemVer from 0.1.0, the contracts that move the version, the image
  tagged by release
date: '2026-11-03T22:58:00Z'
status: accepted
---
## Context

knowgov had no release until 2026-11-03: no tag, no version, no changelog, and its image went to
ghcr only as `:<short-sha>` and `:latest`, so nothing could name "the knowgov that did X". The
maintainer approved cutting `v0.1.0` from the main of 2026-11-03 on these terms ("yes, prepare the
v0.1.0 release PR"); this record holds them.

## Decision

1. **SemVer, from `0.1.0`.** `VERSION` at the root holds the version; `CHANGELOG.md` holds one
   section per release, newest first, and the version in `VERSION` is its top section. A test holds
   the two together.
2. **What moves the version while it is 0.x.** A change to a contract raises the minor version:
   the gate command's exit codes or flags, the JSON shapes pinned by `harness/schemas/`, the
   instance layout (`instance/kinds.toml`, the folders `tools/check_instance.py` checks), the store
   port, the subject manifest format. Anything else raises the patch version.
3. **The image is tagged by release.** Pushing a tag `v*` publishes
   `ghcr.io/fdurieux/knowgov:<tag>` beside `:<short-sha>`; `:latest` stays the last main.
4. **How a release is cut.** A release PR moves `VERSION` and `CHANGELOG.md` and merges on a fully
   green matrix; the maintainer then publishes the GitHub Release on that merge commit, typing the
   tag as new, since a hosted session cannot push a tag. Publishing creates the tag, and the tag
   runs the publish job.

## Consequences

- `v0.1.0` is cut from main as of its release PR; the gate report's schema version 2 (task-0048,
  in progress) is therefore a `0.2.0` change.
- The vendored versions a release carries (pumllint, the register's tag, the pins in
  `demo/Dockerfile`) are listed in its changelog section, so an instance knows what it runs.
