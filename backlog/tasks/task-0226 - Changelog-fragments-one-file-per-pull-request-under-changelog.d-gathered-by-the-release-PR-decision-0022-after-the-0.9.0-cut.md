---
id: TASK-0226
title: >-
  Changelog fragments: one file per pull request under changelog.d/, gathered by
  the release PR (decision-0022), after the 0.9.0 cut
status: To Do
assignee: []
created_date: '2026-11-08T16:23:00Z'
labels:
  - release
  - process
milestone: m-8
dependencies: []
references:
  - backlog/decisions/decision-0022
priority: low
type: chore
ordinal: 226000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0022 (accepted 2026-11-08, the maintainer: "do it after 0.9.0"). Today every pull request an adopter would notice adds its line under CHANGELOG.md's ## Unreleased (maintainer, 2026-11-04). Parallel pull requests all add at the same spot, so each merge sends every other open pull request back for a catch-up merge and a fresh CI run (2026-11-08: #363, #364, #366, #369, #370 and #372 each needed one or two).

Start only after 0.9.0's release PR has merged; the freeze's last pull requests keep today's convention.

Build: each pull request writes its line to changelog.d/<task-id>.md with a front line naming its heading (Contract changes or Changes); the release PR gathers the fragments into the new version's section in a fixed order (heading, then task id) and deletes them; tests/test_release.py and .github/workflows/release.yml read the fragments; CLAUDE.md's Releases paragraph and the release checklist describe the new convention. Released sections are never edited.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Starts after 0.9.0's release PR has merged; until then the 2026-11-04 convention holds
- [ ] #2 A pull request's changelog line lives in its own file under changelog.d/, naming its heading; two pull requests never touch the same lines
- [ ] #3 A tool gathers the fragments into the release's section in a fixed order and removes them; it is proven on a fixture and leaves every released section byte-identical
- [ ] #4 tests/test_release.py and release.yml hold the version, the gathered section and an empty changelog.d/ at a tag; a test refuses a fragment with an unknown heading
- [ ] #5 CLAUDE.md's Releases paragraph states the new convention, citing decision-0022
<!-- AC:END -->
