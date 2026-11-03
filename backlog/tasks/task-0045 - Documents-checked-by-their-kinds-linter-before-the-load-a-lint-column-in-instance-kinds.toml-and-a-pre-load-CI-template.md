---
id: TASK-0045
title: >-
  Documents checked by their kind's linter before the load: a lint column in
  instance/kinds.toml and a pre-load CI template
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T22:50:00Z'
labels:
  - instance
  - gate
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0008
priority: high
type: feature
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0008 §5 (PROPOSED there): nothing checks a document's form before it reaches the graph. Route: a pull request into an instance's artefacts/<kind>/ whose CI runs the kind's linter as the programme's gate contract names it (fdurieux.github.io, 'Artefact by artefact'); the load reads only the merged tree. This is a different gate from harness/gate_cli.py (knowledge) and replaces nothing. Only linters that can run in this repository's CI are exercised (pumllint for plantuml-models); every other kind is reported 'unchecked: <tool the site names>', never silently passed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 instance/kinds.toml gains a lint field per kind (tool, gate-capable or not), filled from doc-0008 §5's table and held by tests/test_instance.py
- [x] #2 tools/preload_check.py <instance> [--changed FILE...] runs each changed file's kind linter: exit 0 clean, 1 findings at or above threshold, 2 cannot run; a kind with no runnable linter is listed as unchecked
- [x] #3 A CI template an instance copies (instance/ci/), proven in harness.yml on the example instance: a planted broken PlantUML file exits 1, the clean instance exits 0
- [x] #4 instance/README.md and docs/guide.md say what the check does and what it does not (form, not knowledge)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. lint = {tool, gate, capable} per kind in instance/kinds.toml from doc-0008 §5's table; check_instance.kinds() carries it; tests/test_instance.py holds tool and gate word for word to the brief.
2. tools/preload_check.py <instance> [--changed FILE...] [--since REF] [--fail-on] [-f json] [-o]: RUNNERS maps a kind to a linter that runs here (pumllint for plantuml-models, run with the instance as cwd, -f json); other kinds unchecked naming the table's tool; gate contract 0/1/2; JSON under harness/schemas/preload-report.schema.json, validated by harness/schema_check.py.
3. instance/ci/preload-check.yml (the workflow an instance copies) calls instance/ci/preload-check.sh (preload_check, then check_instance); harness.yml runs that script on the example instance with real pumllint: clean 0, a planted broken .puml committed after a base 1, KG_FAIL_ON=blocker 0.
4. tests/test_preload.py with a pumllint stand-in (the tests job installs none); instance/README.md, docs/guide.md §5 and CLAUDE.md say form, not knowledge, and that it does not replace harness/gate_cli.py.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Exit 2 also for a --changed file outside the instance, at the top of artefacts/, or in a folder kinds.toml does not know (doc-0008: 'a kind unknown'); a --changed file elsewhere in the instance (a manifest, a register row) is skipped, not failed. --since REF runs git diff --diff-filter=d REF...HEAD -- artefacts/ so the template survives file names with spaces and deletions. Default --fail-on major, pumllint's own; the linter's own exit 1 is never overridden to pass. capable = gate column starts 'yes' or 'via': 10 of 20 kinds. Not built (said in the guide): a baseline per kind, running the other kinds' tools, recording the verdict on the Version node. Verified: python tests/run_tests.py 132/132, also with KG_SUBJECT=subjects/jef_data_load; the harness.yml step run locally with pumllint 0.33.0: clean 0, broken 1 (SEQ001 critical), JSON valid, blocker threshold 0.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documents are now checked for form by their kind's linter before the load. instance/kinds.toml carries doc-0008 §5's linter per kind (tool, gate, capable), held word for word by tests/test_instance.py. tools/preload_check.py lints all, --changed or --since files under artefacts/<kind>/ with the linters that run here (pumllint for plantuml-models), lists every other kind's files as unchecked naming the table's tool, and exits 0/1/2 under the gate contract; its JSON is pinned by harness/schemas/preload-report.schema.json. instance/ci/ holds the workflow an instance copies and the script it calls; harness.yml runs that script with real pumllint on the example instance (clean 0, a planted broken PlantUML file 1). instance/README.md, docs/guide.md §5 and CLAUDE.md say it checks form, not knowledge, and does not replace harness/gate_cli.py. Tests: 132/132 in both subjects; tests/test_preload.py uses a pumllint stand-in. Follow-ups, not built: a per-kind baseline, other kinds' linters, the verdict on the Version node.
<!-- SECTION:FINAL_SUMMARY:END -->
