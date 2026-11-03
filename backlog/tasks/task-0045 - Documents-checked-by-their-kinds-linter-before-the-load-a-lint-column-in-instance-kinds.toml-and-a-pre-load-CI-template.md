---
id: TASK-0045
title: >-
  Documents checked by their kind's linter before the load: a lint column in
  instance/kinds.toml and a pre-load CI template
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T22:41:00Z'
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
- [ ] #1 instance/kinds.toml gains a lint field per kind (tool, gate-capable or not), filled from doc-0008 §5's table and held by tests/test_instance.py
- [ ] #2 tools/preload_check.py <instance> [--changed FILE...] runs each changed file's kind linter: exit 0 clean, 1 findings at or above threshold, 2 cannot run; a kind with no runnable linter is listed as unchecked
- [ ] #3 A CI template an instance copies (instance/ci/), proven in harness.yml on the example instance: a planted broken PlantUML file exits 1, the clean instance exits 0
- [ ] #4 instance/README.md and docs/guide.md say what the check does and what it does not (form, not knowledge)
<!-- AC:END -->
