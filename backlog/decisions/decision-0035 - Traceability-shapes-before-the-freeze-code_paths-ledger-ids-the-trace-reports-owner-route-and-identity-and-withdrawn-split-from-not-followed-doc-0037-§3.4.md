---
id: decision-0035
title: >-
  Traceability shapes before the freeze: code_path's ledger ids, the trace
  report's owner, route and identity, and withdrawn split from not followed
  (doc-0037 §3.4)
date: '2026-11-09T21:29:00Z'
status: accepted
---
## Context

The functional review of the 0.9.0 release candidate (doc-0037; group B, `session_01HTAA1Re9TEvFEokRYMR175`, at `main` `f194aac`) found three report shapes that leave the up-and-down chain or its vocabulary incomplete:
- **B1:** `code_path`'s ledger leg returns `entry.assertions` and `keys` as counts (88), though the ledger holds the assertion ids and the keys. So "this generated file → its keys → `key_nodes`" breaks over MCP. `derived_outputs` cannot stand in, because a load wipes the store's registration. The leg has no suspect state.
- **B2:** trace-report findings carry no `owner` or `route`, and its `gate` block lacks gate-report v3's identity (`task_profile`, `register`, `knowgov`). A suspect-code annotation cannot name who answers, and an auditor cannot see what the trace decided on.
- **B3:** "withdrawn" means deprecated or retired in `register_change` and the gate. It means any edge not followed, a proposed one included, in proposal-impact's `slices.map[].withdrawn` and `keys.behind_withdrawn`, in `register_impact`'s "flagged withdrawn", and in the page's "no, withdrawn".

Each schema involved is `additionalProperties: false`, so each change is a contract change: before the 0.9.0 cut, or a 0.10.0 (decision-0016 point 2).

## Options

- **(a)** Settle all three before the freeze:
  - B1: return the ids and keys;
  - B2: add the owner, the route and the identity, as the gate report has them;
  - B3: rename the not-followed fields to `not_followed`, keeping `withdrawn` for deprecated or retired.
- **(b)** Document them, and change them in 0.10.0.

## Opportunity canvas

- Problem: the upward read from built code stops at a count; a suspect-code annotation names no one; one word carries two meanings.
- Users: assistants (U4), squads (U3), CI, auditors (U5).
- Cost: three schema edits and their readers.
- Value: the up-and-down chain is complete over MCP, and the frozen vocabulary means one thing.

## Fit/gap

- (a) completes FR-06 and FR-08's upward read, and doc-0020's chain.
- (b) freezes the gaps for at least a minor.

## SWOT, (a)

- Strengths: no ambiguity frozen in.
- Weaknesses: three builds before the cut.
- Opportunities: the gate report already models owner, route and identity.
- Threats: the rename touches the page's and proposal-impact's readers.

## Advice

(a). Each is small, and a frozen ambiguity costs a minor version to undo.

## Decision

Accepted by the maintainer on 2026-11-09: "Option (A)", quoting doc-0037 §3.4's advice.

| Finding | Taken | Build |
|---|---|---|
| B1, code_path's ledger leg | its assertion ids and keys returned, and the leg's suspect state | task-0303 |
| B2, the trace report | each finding carries `owner` and `route`; the gate block carries gate-report v3's identity | task-0304 |
| B3, "withdrawn" | `withdrawn` only for deprecated or retired; every not-followed edge is `not_followed` | task-0305 |

## Consequences

- The three builds hold the 0.9.0 cut beside task-0301 and task-0302, and each is re-checked by the reviewer who found it.
- The schemas involved change before the freeze: `code-path`, `trace-report`, `proposal-impact` and `register-impact`'s reader output, and the page's impact text.
- doc-0037 §3.1 (execution verification) and §3.3 (audit identity) are still the maintainer's.
