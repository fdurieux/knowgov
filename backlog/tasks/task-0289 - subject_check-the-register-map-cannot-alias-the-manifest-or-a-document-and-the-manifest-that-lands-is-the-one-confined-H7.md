---
id: TASK-0289
title: >-
  subject_check: the register map cannot alias the manifest or a document, and
  the manifest that lands is the one confined (H7)
status: To Do
assignee: []
created_date: '2026-11-09T15:37:00Z'
labels:
  - validation
  - security
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 282000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the independent spot check (decision-0032 point 5, task-0256) at main 9861953, SC-1. Fix-only, but it breaks task-0196 H7's documented confinement, so it lands before the 0.9.0 cut.

`harness/subject_check.py` `plan()` writes `register_map_toml` at `files[_rel([register] map)]` with no `seen` or duplicate check. `map = "subject.toml"` (or `"./subject.toml"`) replaces the manifest after `confine_manifest` has checked only the decoy, so the written manifest's `[[artefact]] path` is never confined.

Reproduction: `subject_check {"subject_toml": "[register]\nmap = \"subject.toml\"\n", "register_map_toml": <a manifest whose [[artefact]] path = "/abs/server/file">}`:
- a missing path gives "<path> does not exist";
- `/etc/hostname` gives a zero-yield warning, so the yield child read it;
- a readable file in a mapper's convention gives nothing.

So the tool is an existence oracle and a reader of server files: yielded key ids feed the near-match notes, and `[verification]` authored versions make `subject_versions` a digest oracle (read from the code). It is reachable over Streamable HTTP. `map = "scenarios.toml"` silently replaces `scenarios_toml` the same way.

Minor: `documents` with "a" then "a/b" gives "could not answer: FileExistsError"; the reverse order gives the named refusal.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The register map's path goes through `_norm` and `seen` before the documents. A collision with `subject.toml`, `scenarios.toml`, `plants.toml` or a document is refused, named.
- [ ] #2 The text that finally lands at `subject.toml` is the text `confine_manifest` checked.
- [ ] #3 "a" then "a/b", in either order, gives the named refusal.
- [ ] #4 Each reproduction is a test in `tests/test_subject_check.py`, and the HTTP path is held where `check_mcp_server.py` covers subject_check.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the fix.
<!-- AC:END -->
