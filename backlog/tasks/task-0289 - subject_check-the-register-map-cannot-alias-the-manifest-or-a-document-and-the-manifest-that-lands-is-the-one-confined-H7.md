---
id: TASK-0289
title: >-
  subject_check: the register map cannot alias the manifest or a document, and
  the manifest that lands is the one confined (H7)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T15:37:00Z'
updated_date: '2026-11-09T16:12:00Z'
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
- [x] #1 The register map's path goes through `_norm` and `seen` before the documents. A collision with `subject.toml`, `scenarios.toml`, `plants.toml` or a document is refused, named.
- [x] #2 The text that finally lands at `subject.toml` is the text `confine_manifest` checked.
- [x] #3 "a" then "a/b", in either order, gives the named refusal.
- [x] #4 Each reproduction is a test in `tests/test_subject_check.py`, and the HTTP path is held where `check_mcp_server.py` covers subject_check.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the fix.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. plan(): the map's path through _norm and seen (_map_path, _add), the loader's files reserved (RESERVED). 2. confine_manifest on the text landing at subject.toml. 3. A file/folder overlap refused by name in either order (_no_folder_clash). 4. Tests in test_subject_check_tool.py; the alias in check_mcp_server's H7 loop. 5. CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #4: no tests/test_subject_check.py exists; the subject_check tool's tests live in tests/test_subject_check_tool.py, where both reproductions were added (test_the_register_map_cannot_alias_the_manifest_or_another_file_of_the_call, test_a_file_another_path_needs_as_a_folder_is_refused_by_name_in_either_order).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
subject_check's plan() wrote register_map_toml at [register] map's path with no duplicate check, so map = "subject.toml" replaced the manifest after confine_manifest had checked the decoy and the yield child read server files the landed manifest named: an existence oracle reachable over Streamable HTTP (a missing path 'does not exist', /etc/hostname a zero-yield warning). Now the map's path joins the call's files through _norm and seen (_map_path, _add), refused named on a collision with the manifest, scenarios, plants or a document; subject.toml, scenarios.toml and plants.toml are reserved passed or not (RESERVED); confine_manifest checks the text that lands at subject.toml; a file another path needs as a folder is refused by name in either order before anything is written (_no_folder_clash), no longer FileExistsError. Tests in tests/test_subject_check_tool.py (the tool's test file; there is no test_subject_check.py), both failing on main where the alias read /etc/hostname; check_mcp_server.py sends the alias over stdio and Streamable HTTP in its H7 loop and holds on CargoQuote S1. plan() 23 to 16, the complexity baseline tightened. The record held: no loader, rule or gate change. CHANGELOG under Unreleased > Changes. run_tests: bare venv without PyYAML 956/1016 (60 skipped), pins 1014/1016 (2 skipped), 0 failed.
<!-- SECTION:FINAL_SUMMARY:END -->
