---
id: TASK-0006
title: Instance layout and the private-instance mount
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - instance
milestone: m-2
dependencies:
  - TASK-0002
priority: medium
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A client's instance is private and never reaches this repository. It is a git repository with a declared layout: the register's trees (taxonomies, relationships, decisions, exceptions, glossary, exports), artefacts/<kind>/ for authored artefacts keyed by the rows of the artefact table on fdurieux.github.io, exports/<system>/<date>/ with manifests, and record/ for its results and digests. The platform vendors a public subject at a tag and mounts a private one through the compose override, the route docs/ieam-register-demo-integration.md already proposed for a live register checkout. One stack per instance; the page stays read-only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The instance layout is documented, with the artefact table's rows and which have a mapper
- [ ] #2 A directory in that layout mounted through the compose override runs replay and deterministic without any file written back
- [ ] #3 An artefact kind with no mapper is reported as absent, never silently skipped
- [ ] #4 ieam-register's public test case, plus the CargoQuote artefacts, is a valid instance
<!-- AC:END -->
