---
id: TASK-0319
title: >-
  check_subject's attestation check reads a directory artefact's Version as the
  load does, and runs whenever a bound declaration exists (task-0318 re-check
  D1, D2, E1, E2)
status: To Do
assignee: []
created_date: '2026-11-10T05:31:00Z'
labels:
  - integrity
  - attestation
  - 0.9.0
dependencies: []
priority: high
ordinal: 312000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, before the 0.9.0 cut: completes task-0318's N-c (the coordinator, 2026-11-10). Found by reviewer A's re-check of task-0318 (session_01HTAA1UC5tSJ4yRcP1AcDFW, main 67c3d8c): N-a FIXED, N-c fixed for files, NOT FIXED for directory artefacts. The contract does not move.

D1: one newline appended to a file in J-F's `contracts/` gives 12 errors naming `contracts/`, `contracts/dmn/` and `features/`, two of them untouched. `artefact_digests` hashes every file under the directory (`p.rglob("*")`), ignoring the artefact's `include` and nested artefacts, so on the pristine kit 156 files outside the Versions are already unlisted, silent only until some listed digest goes stale. The contracts/ error lists several digests without naming the changed file. Removing a file gives the same 12.
D2: a file added to a directory artefact within its include (`contracts/NEW.md`) passes check_subject (exit 0) because no listed digest went stale and `_changed_artefacts` never runs; the load gives contracts/ a new Version and 146 of its 195 statements drop from approved to proposed.
E1: re-attesting by adding the new digest while keeping the old gives 16 errors of the old unclear form; the fix text "re-attest it (list the new digest)" should say replace the old digest, and a stale digest error should name the artefact it belonged to (planted Versions derived from the edited file need re-listing too).
E2: `authored` or `approval` with `versions = []` attests nothing (36 keys verified, none approved) and check_subject says nothing; note it as N-a does for execution and review.

Fix: compute a directory artefact's Version with the load's own part selection (include, nested artefacts excluded) and name the changed, added or removed file; run the per-artefact comparison whenever a bound declaration exists, not only when a digest is stale; reword the fix text; note an empty authored or approval list.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 D1: one edit in contracts/ names contracts/ alone, with the changed file; contracts/dmn/ and features/ are not named; removing a file names it; a test on the J-F kit or a fixture
- [ ] #2 D2: a file added within the include is an error naming the artefact and the added file, as the load unbinds it; a file outside the include changes nothing; a test
- [ ] #3 E1: the fix text says replace the old digest; a stale digest names the artefact it belonged to; a test
- [ ] #4 E2: authored or approval with versions = [] gets a note naming decision-0019; a test
- [ ] #5 Both public subjects and the claim probe pass check_subject as before; the record holds
<!-- AC:END -->
