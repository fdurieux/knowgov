---
id: TASK-0181
title: >-
  instance/README.md states the contracts at 1.0, in the adopter register
  (decision-0016 point 3, doc-0028 P4)
status: To Do
assignee: []
created_date: '2026-11-06T16:51:00Z'
updated_date: '2026-11-08T23:53:00Z'
labels:
  - docs
  - contracts
dependencies: []
priority: medium
type: task
ordinal: 182000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0016 (accepted 2026-11-06, option b) names the contracts at 1.0: decision-0003 §2's list (the gate command's exit codes and flags, the JSON shapes under harness/schemas/, the instance layout, the store port, the subject manifest format) plus the MCP reader's and knowgov-runs' tools, prompts and their inputs and outputs (pinned by task-0172's schemas), the KG_* settings instance/README.md or docs/security.md documents, the page's HTTP API as demo/README.md documents it, the inputs and outputs of instance/ci/ (the action, the GitLab include, the shell wrappers, the hooks' settings snippets), the image's name and tag scheme, and the format versions of an instance's inputs and of the ieam-register formats an instance's register may be in. doc-0028 P4: once the decision is accepted, instance/README.md states them for an adopter, with the deprecation rule (point 5: a minor deprecates, at least one further minor and ninety days, removal only in a major) and the support window (point 6: the latest minor, best effort, until task-0060's entity), and what 0.9.x promises (point 2: fixes only).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/README.md gains a section, in the adopter register (plain English, each concept named before use), listing every contract decision-0016 point 3 names, each with where it is defined (schema file, README section, settings table) and how an adopter is told of a change
- [ ] #2 The section states the deprecation rule, the support window and what 0.9.x promises, quoting decision-0016's points by number
- [ ] #3 A test holds the section's contract list to decision-0016 point 3's list (no contract missing, none invented), in the spirit of tests/test_docs_flags.py
- [ ] #4 The format versions of an instance's inputs are named as built (decision-0023, task-0174), with what a missing version means as decision-0023 Amendment A1 settles it once the maintainer has answered
- [ ] #5 Once decision-0028 is accepted: the contracts table states the ieam-register tag the release vendors and tests, and a test holds it to demo/register/SOURCE.md's tag
- [ ] #6 Once decision-0030 is accepted: demo/README.md names the four routes that are the page's HTTP API at 1.0 and says every other route serves the page and may change; a test holds the list to the routes demo/app/server.py serves; CHANGELOG.md files GET /api/store's browser_connect under Changes, not Contract changes
<!-- AC:END -->
