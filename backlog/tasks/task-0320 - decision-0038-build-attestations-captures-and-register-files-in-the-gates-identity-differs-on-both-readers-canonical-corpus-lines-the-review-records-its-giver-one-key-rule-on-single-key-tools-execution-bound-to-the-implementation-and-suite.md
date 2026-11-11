---
id: TASK-0320
title: >-
  decision-0038 build: attestations, captures and register files in the gate's
  identity; differs on both readers; canonical corpus lines; the review records
  its giver; one key rule on single-key tools; execution bound to the
  implementation and suite
status: To Do
assignee: []
created_date: '2026-11-11T08:27:00Z'
labels:
  - contracts
  - 0.9.0
dependencies: []
priority: high
ordinal: 313000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0038 (accepted 2026-11-11, "(a) as advised for all six", with the coordinator's three refinements). One narrow contract build before the 0.9.0 cut. Every change is additive or unreleased; the record must not move.

1. N2: gate report v3 gains optional `attestations` (the canonical JSON of [verification], [provenance] and [capture] as the load read them, sha256), `captures` (the answers and reviews the load applied, sha256) and register file digests beside its tag and commit. Each comes from what the load used, not files on disk; equal on both stores; held by check_round_trip and check_mcp_server.
2. N3: a `differs` list (the identity fields that differ, none for unknown) in the CLI report's baseline object and in MCP gate_verdict's baseline, computed in one place; the stderr lines stay.
3. N4: corpus = sha256 over one canonical JSON array [artefact, version, sha256] per loaded Version, sorted; null and "" distinct; tab and newline cannot collide.
4. G1+G2: `capture.py review` records the ruled answer's giver, read from the capture's content (its signed [answered] handle), never from the file name; the load binds a review by it. A review without the field keeps today's fail-closed rule. The refusal message names decision-0038, not "decision pending".
5. N7: three_valued_answer, derived_outputs and key_nodes take `key` under the same KEY_ITEM pattern and raw-or-NFC refusal as `keys`; -32602 with the value as sent.
6. N-b: `[verification] execution` lists the digests of the reference implementation and of the suite that judged it, each digested as a directory artefact is (the load's own part selection, task-0319); a changed implementation or suite voids the execution verification, named by the not-attested finding and by check_subject. The public subjects and the claim probe list theirs.
Also: reviewer A's N1 from the task-0307 re-check (a partly unknown identity object is named as differing): compare only sub-fields known on both sides.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 N2: editing [verification], a capture or review file, or a vendored register file moves its named field; a skipped capture file does not; equal on both stores; tests
- [ ] #2 N3: --baseline and MCP gate_verdict report the same differs list; a test holds them equal
- [ ] #3 N4: the corpus line is canonical JSON; tab, newline and null/empty cases differ; a test
- [ ] #4 G1+G2: with handles X and X-n, X-n's answer can be approved and its dispute settled; the giver comes from the capture's content; a legacy review keeps the fail-closed rule; tests
- [ ] #5 N7: the three single-key tools refuse what keys refuses, -32602, the value as sent, on both transports; a test
- [ ] #6 N-b: editing the reference implementation or the suite voids its execution verification and is named; the public subjects list their digests; tests
- [ ] #7 A-N1: a sub-field unknown on either side is never named as differing; a test
- [ ] #8 The record holds (both comparators 0 differing leaves); schemas validate earlier v3 reports; CHANGELOG lines under Contract changes
<!-- AC:END -->
