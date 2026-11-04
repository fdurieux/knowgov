---
id: TASK-0105
title: Dogfood the fail-closed hook on knowgov's own protected paths
status: To Do
assignee: []
created_date: '2026-11-04T10:46:00Z'
labels:
  - ci
  - security
milestone: m-8
dependencies:
  - TASK-0099
priority: medium
type: task
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maintainer's decision 2026-11-04, recorded in doc-0014 §11 (#170). This repository gains a .claude/ with two hooks on its own protected paths: (1) a vendored file or its SOURCE.md edited by hand; (2) a backlog markdown file written other than through the backlog CLI. The hooks reuse task-0099's script and exit mapping and call nothing else. The knowledge gate is not wired to this repository's commits: no subject describes the repository. No recipe, README or release note claims an outcome from the 20-of-20 figure (doc-0014).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test feeds each hook a hand edit to a vendored file and to a backlog file and sees both blocked; a CLI-written backlog change and an unprotected edit both pass
- [ ] #2 The hooks use task-0099's script and its exit mapping, with no copy of it
- [ ] #3 CLAUDE.md names the hooks in one line and states what they guard
<!-- AC:END -->
